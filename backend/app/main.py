from __future__ import annotations

import asyncio
import contextlib
import logging
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .config import settings
from .database import Database
from .languages import LANGUAGES
from .models import JoinParameters, RoomCreate, RoomResponse
from .translator import (
    DeepSeek4FreeTranslator,
    DemoTranslator,
    DisabledTranslator,
    Translation,
    Translator,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Client:
    websocket: WebSocket
    member_id: str
    name: str
    language: str

    def public(self) -> dict[str, str]:
        return {"id": self.member_id, "name": self.name, "language": self.language}


class RoomHub:
    """Tracks active WebSockets only; durable data stays in SQLite."""

    def __init__(self) -> None:
        self.rooms: dict[str, dict[str, Client]] = defaultdict(dict)

    async def add(self, room_id: str, client: Client) -> None:
        old = self.rooms[room_id].get(client.member_id)
        self.rooms[room_id][client.member_id] = client
        if old and old.websocket is not client.websocket:
            with contextlib.suppress(Exception):
                await old.websocket.close(code=4001, reason="Connection replaced")

    def remove(self, room_id: str, member_id: str, websocket: WebSocket) -> bool:
        current = self.rooms.get(room_id, {}).get(member_id)
        if current and current.websocket is websocket:
            del self.rooms[room_id][member_id]
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            return True
        return False

    def languages(self, room_id: str) -> set[str]:
        return {client.language for client in self.rooms.get(room_id, {}).values()}

    def people(self, room_id: str) -> list[dict[str, str]]:
        return [client.public() for client in self.rooms.get(room_id, {}).values()]

    async def _send(self, client: Client, event: dict[str, Any]) -> bool:
        try:
            await client.websocket.send_json(event)
            return True
        except Exception:
            return False

    async def broadcast(self, room_id: str, event: dict[str, Any]) -> None:
        clients = list(self.rooms.get(room_id, {}).values())
        delivered = await asyncio.gather(*(self._send(client, event) for client in clients), return_exceptions=True)
        for client, result in zip(clients, delivered):
            if result is not True:
                self.remove(room_id, client.member_id, client.websocket)

    async def broadcast_language(self, room_id: str, language: str, event: dict[str, Any]) -> None:
        clients = [
            client for client in self.rooms.get(room_id, {}).values() if client.language == language
        ]
        delivered = await asyncio.gather(*(self._send(client, event) for client in clients), return_exceptions=True)
        for client, result in zip(clients, delivered):
            if result is not True:
                self.remove(room_id, client.member_id, client.websocket)

    async def broadcast_presence(self, room_id: str) -> None:
        await self.broadcast(room_id, {"type": "presence", "members": self.people(room_id)})


class ChatService:
    def __init__(self, database: Database, translator: Translator, hub: RoomHub) -> None:
        self.database = database
        self.translator = translator
        self.hub = hub
        self.translation_locks: dict[tuple[str, str], asyncio.Lock] = {}

    def serialise(self, message: dict[str, str], language: str) -> dict[str, Any]:
        cached = self.database.translation(message["id"], language)
        status = cached["status"] if cached else "pending"
        content = cached["content"] if cached else message["original_content"]
        return {
            "id": message["id"],
            "author_id": message["author_id"],
            "author_name": message["author_name"],
            "original_content": message["original_content"],
            "content": content,
            "translation_status": status,
            "created_at": message["created_at"],
        }

    async def send_history(self, room_id: str, client: Client) -> None:
        messages = self.database.messages(room_id, settings.history_limit)
        await client.websocket.send_json(
            {
                "type": "history",
                "messages": [self.serialise(message, client.language) for message in messages],
            }
        )
        # Cached translations return with history. Missing variants are queued
        # afterwards so joining never blocks on a remote model response.
        for message in messages:
            if not self.database.translation(message["id"], client.language):
                asyncio.create_task(self.translate_and_publish(room_id, message, client.language))

    async def publish_message(self, room_id: str, client: Client, content: str) -> None:
        message = self.database.add_message(room_id, client.member_id, client.name, content)
        # The source reaches everyone immediately. The UI marks it as translating
        # and replaces it as soon as their language-specific variant is complete.
        await self.hub.broadcast(
            room_id,
            {
                "type": "message",
                "message": {
                    "id": message["id"],
                    "author_id": message["author_id"],
                    "author_name": message["author_name"],
                    "original_content": message["original_content"],
                    "content": message["original_content"],
                    "translation_status": "pending",
                    "created_at": message["created_at"],
                },
            },
        )
        # `message` has source content in that broadcast for every receiver; the
        # follow-up translation events are filtered per target language.
        for language in self.hub.languages(room_id):
            asyncio.create_task(self.translate_and_publish(room_id, message, language))

    async def translate_and_publish(
        self, room_id: str, message: dict[str, str], language: str
    ) -> None:
        key = (message["id"], language)
        lock = self.translation_locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self.database.translation(message["id"], language)
            if cached:
                translation = Translation(cached["content"], cached["status"])
            else:
                translation = await self.translator.translate(message["original_content"], language)
                self.database.put_translation(
                    message["id"], language, translation.content, translation.status
                )

        await self.hub.broadcast_language(
            room_id,
            language,
            {
                "type": "translation",
                "message_id": message["id"],
                "content": translation.content,
                "translation_status": translation.status,
            },
        )
        # No task can start between unlock and this synchronous map operation.
        if not lock.locked():
            self.translation_locks.pop(key, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database = Database(settings.database_path)
    if settings.deepseek_auth_token:
        translator: Translator = DeepSeek4FreeTranslator(
            settings.deepseek_auth_token, settings.max_parallel_translations
        )
        mode = "deepseek4free"
    elif settings.demo_translator:
        translator = DemoTranslator()
        mode = "demo"
    else:
        translator = DisabledTranslator()
        mode = "disabled"
    app.state.database = database
    app.state.hub = RoomHub()
    app.state.chat = ChatService(database, translator, app.state.hub)
    app.state.translator_mode = mode
    logger.info("Lingua Room started with translator mode: %s", mode)
    try:
        yield
    finally:
        database.close()


app = FastAPI(
    title="Lingua Room API",
    version="1.0.0",
    description="WebSocket chat with per-language DeepSeek4Free translations.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins) or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "translator": app.state.translator_mode}


@app.get("/api/languages")
async def list_languages() -> dict[str, tuple[dict[str, str], ...]]:
    return {"languages": LANGUAGES}


@app.post("/api/rooms", response_model=RoomResponse, status_code=201)
async def create_room(payload: RoomCreate) -> dict[str, str]:
    return app.state.database.create_room(payload.name)


@app.get("/api/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str) -> dict[str, str]:
    room = app.state.database.room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@app.websocket("/ws/rooms/{room_id}")
async def room_socket(
    websocket: WebSocket,
    room_id: str,
    member_id: str = Query(...),
    name: str = Query(...),
    language: str = Query(...),
) -> None:
    room_id = room_id.upper()
    if not app.state.database.room(room_id):
        await websocket.close(code=4404, reason="Room not found")
        return

    try:
        joined = JoinParameters(member_id=member_id, name=name, language=language)
    except ValidationError:
        await websocket.close(code=1008, reason="Invalid join parameters")
        return

    await websocket.accept()
    client = Client(websocket, joined.member_id, joined.name, joined.language)
    hub: RoomHub = app.state.hub
    chat: ChatService = app.state.chat
    await hub.add(room_id, client)

    try:
        await websocket.send_json(
            {
                "type": "room",
                "room": app.state.database.room(room_id),
                "you": client.public(),
            }
        )
        await chat.send_history(room_id, client)
        await hub.broadcast_presence(room_id)
        while True:
            event = await websocket.receive_json()
            if event.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if event.get("type") != "send":
                await websocket.send_json({"type": "error", "message": "Unknown event"})
                continue
            content = event.get("content")
            if not isinstance(content, str):
                await websocket.send_json({"type": "error", "message": "Message must be text"})
                continue
            content = content.strip()
            if not content:
                continue
            if len(content) > settings.max_message_length:
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": f"Messages may have at most {settings.max_message_length} characters",
                    }
                )
                continue
            await chat.publish_message(room_id, client, content)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("WebSocket error in room %s", room_id)
    finally:
        if hub.remove(room_id, client.member_id, websocket):
            await hub.broadcast_presence(room_id)
