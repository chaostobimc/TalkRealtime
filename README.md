# Lingua Room

Eine Echtzeit-Chat-Plattform im modernen WhatsApp-Stil: Jede Person wählt beim Betreten einen Namen und eine Sprache. Nachrichten werden als Original gespeichert und pro gewählter Sprache automatisch übersetzt. Das Original bleibt für alle jederzeit sichtbar.

## Architektur

- **Frontend:** React + TypeScript + Vite, responsive und ohne UI-Framework
- **Backend:** Python / FastAPI, WebSockets, SQLite
- **Übersetzung:** ausschließlich der angefragte Adapter für [`xtekky/deepseek4free`](https://github.com/xtekky/deepseek4free), keine offizielle DeepSeek-API
- **Performance:** Nachrichten werden sofort per WebSocket ausgespielt; Übersetzungen laufen asynchron, werden nach Sprache dedupliziert und in SQLite gecacht. Eine übersetzte Nachricht wird daher nur einmal je Zielsprache erzeugt, auch wenn viele Personen diese Sprache nutzen.
- **Chat-Komfort:** eindeutige Live-Namen pro Raum, Emoji-Picker, Nachrichtensuche, Raum-/Profilmenüs sowie Bild-, PDF- und Textanhänge bis 8 MB.

## Lokal starten

### 1. Backend

> Python 3.11 oder neuer empfohlen. Das angegebene DeepSeek4Free-Repository wird über das Bootstrap-Skript geklont, weil es selbst kein Python-Paket-Metadatenfile bereitstellt.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
./scripts/install_deepseek4free.sh
cp .env.example .env
# DEEPSEEK_AUTH_TOKEN in .env setzen (nicht committen)
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Öffne `http://localhost:5173`.

## DeepSeek4Free-Konfiguration

`backend/app/translator.py` kapselt den geklonten Quellcode, sodass keine offizielle API oder ein SDK dafür verwendet wird. Trage die Web-Session-Authentifizierung ausschließlich als `DEEPSEEK_AUTH_TOKEN` in `backend/.env` oder als Umgebungsvariable auf dem Server ein. Sie wird nie an den Browser gesendet oder geloggt.

Wenn der Dienst nicht konfiguriert oder temporär nicht erreichbar ist, wird das Original **sichtbar als noch nicht übersetzt** angezeigt – es wird nie als falsche Übersetzung ausgegeben. Für einen rein visuellen lokalen Prototyp kann `DEMO_TRANSLATOR=true` gesetzt werden.

Der Status ist ohne Geheimnisse unter `http://localhost:8000/api/health` sichtbar: `translator: "deepseek4free"` bestätigt, dass die Umgebungsvariable beim Serverstart geladen wurde. Nach einem fehlgeschlagenen Versuch zeigt `last_error` die bereinigte Provider-Ursache (z. B. abgelaufene Anmeldung oder Rate Limit), niemals den Token. Nach Änderungen an `.env` muss Uvicorn neu gestartet werden.

Der Übersetzungsprompt ist absichtlich eng: Er verlangt ausschließlich den übersetzten Text, erhält keine Chat-Historie und schützt URLs, E-Mail-Adressen, @Mentions, Hashtags sowie Inline-Code durch Platzhalter. Fragen sollen Fragen bleiben; die KI darf sie nicht beantworten oder kommentieren.

## Produktionshinweise

- Setze `CORS_ORIGINS` auf die tatsächliche Frontend-Domain.
- Verwende HTTPS/WSS und einen Reverse Proxy (z. B. Caddy oder nginx).
- Räume sind in dieser schlanken Referenz über ihren sechsstelligen Freigabecode zugänglich. Für private Teams sollten Authentifizierung, Zugriffskontrolle, Rate Limiting, Moderation und eine persistente Presence-Schicht ergänzt werden.
- DeepSeek4Free basiert auf einer nicht offiziellen Schnittstelle. Prüfe vor einem produktiven Einsatz die jeweils geltenden Nutzungsbedingungen, Datenschutz- und Compliance-Anforderungen.
