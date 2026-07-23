import { FormEvent, KeyboardEvent, type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { Copy, dictionary } from './locales';

type Language = { code: string; name: string; native: string };
type Room = { id: string; name: string; created_at: string };
type Person = { id: string; name: string; language: string };
type Profile = { id: string; name: string; language: string };
type ChatMessage = {
  id: string;
  author_id: string;
  author_name: string;
  original_content: string;
  content: string;
  translation_status: 'pending' | 'complete' | 'unavailable';
  created_at: string;
};

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || 'http://localhost:8000';
const fallbackLanguages: Language[] = [
  { code: 'de', name: 'German', native: 'Deutsch' },
  { code: 'en', name: 'English', native: 'English' },
  { code: 'es', name: 'Spanish', native: 'Español' },
  { code: 'fr', name: 'French', native: 'Français' },
  { code: 'it', name: 'Italian', native: 'Italiano' },
  { code: 'pt', name: 'Portuguese', native: 'Português' },
  { code: 'tr', name: 'Turkish', native: 'Türkçe' },
  { code: 'ru', name: 'Russian', native: 'Русский' },
  { code: 'ar', name: 'Arabic', native: 'العربية' },
  { code: 'ja', name: 'Japanese', native: '日本語' },
  { code: 'ko', name: 'Korean', native: '한국어' },
  { code: 'zh', name: 'Chinese', native: '中文' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
];

function getStoredProfile(): Omit<Profile, 'id'> {
  try {
    const saved = JSON.parse(localStorage.getItem('lingua-profile') || '{}');
    return { name: typeof saved.name === 'string' ? saved.name : '', language: typeof saved.language === 'string' ? saved.language : 'de' };
  } catch {
    return { name: '', language: 'de' };
  }
}

function profileFor(name: string, language: string): Profile {
  const normalized = name.trim().replace(/\s+/g, ' ');
  localStorage.setItem('lingua-profile', JSON.stringify({ name: normalized, language }));
  return { id: crypto.randomUUID(), name: normalized, language };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || 'Request failed');
  return response.json() as Promise<T>;
}

export default function App() {
  const initialCode = new URLSearchParams(window.location.search).get('room')?.toUpperCase() || '';
  const stored = getStoredProfile();
  const [languages, setLanguages] = useState<Language[]>(fallbackLanguages);
  const [active, setActive] = useState<{ room: Room; me: Profile } | null>(null);

  useEffect(() => {
    request<{ languages: Language[] }>('/api/languages')
      .then(({ languages: loaded }) => setLanguages(loaded))
      .catch(() => undefined);
  }, []);

  const enterRoom = (room: Room, name: string, language: string) => {
    const me = profileFor(name, language);
    window.history.replaceState({}, '', `${window.location.pathname}?room=${room.id}`);
    setActive({ room, me });
  };

  if (!active) {
    return <Lobby languages={languages} initialName={stored.name} initialLanguage={stored.language} initialCode={initialCode} onEnter={enterRoom} />;
  }
  return <Chat room={active.room} me={active.me} languages={languages} onLeave={() => { window.history.replaceState({}, '', window.location.pathname); setActive(null); }} />;
}

function Lobby({ languages, initialName, initialLanguage, initialCode, onEnter }: {
  languages: Language[];
  initialName: string;
  initialLanguage: string;
  initialCode: string;
  onEnter: (room: Room, name: string, language: string) => void;
}) {
  const [name, setName] = useState(initialName);
  const [language, setLanguage] = useState(initialLanguage);
  const [roomName, setRoomName] = useState('');
  const [joinCode, setJoinCode] = useState(initialCode);
  const [mode, setMode] = useState<'create' | 'join'>(initialCode ? 'join' : 'create');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const t = dictionary(language);

  const create = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !roomName.trim()) { setError(t.required); return; }
    setBusy(true); setError('');
    try {
      const room = await request<Room>('/api/rooms', { method: 'POST', body: JSON.stringify({ name: roomName }) });
      onEnter(room, name, language);
    } catch {
      setError(t.createFailed);
    } finally { setBusy(false); }
  };

  const join = async (event: FormEvent) => {
    event.preventDefault();
    if (!name.trim() || !joinCode.trim()) { setError(t.required); return; }
    setBusy(true); setError('');
    try {
      const room = await request<Room>(`/api/rooms/${encodeURIComponent(joinCode.trim().toUpperCase())}`);
      onEnter(room, name, language);
    } catch {
      setError(t.roomNotFound);
    } finally { setBusy(false); }
  };

  return <main className="lobby-shell">
    <div className="lobby-orb orb-one" /><div className="lobby-orb orb-two" />
    <header className="lobby-header"><Brand /><span className="header-tagline">{t.tagline}</span><span className="header-status"><i /> {t.liveTranslation}</span></header>
    <section className="welcome-grid">
      <div className="welcome-copy">
        <div className="eyebrow"><Sparkle /> {t.aiPowered}</div>
        <h1>{t.hero}<br /><em>{t.heroAccent}</em></h1>
        <p>{t.intro}</p>
        <div className="translation-preview" aria-label="Translation preview">
          <div className="preview-avatar">AM</div>
          <div><span className="preview-name">Amélie <small>· Français</small></span><strong>« On se retrouve à 18 h ? »</strong><span className="preview-line"><Translate /> “Treffen wir uns um 18 Uhr?”</span></div>
        </div>
        <div className="privacy-note"><Shield /> {t.translationHint}</div>
      </div>

      <div className="entry-card">
        <div className="card-tabs" role="tablist">
          <button className={mode === 'create' ? 'active' : ''} onClick={() => { setMode('create'); setError(''); }} type="button">{t.createRoom}</button>
          <button className={mode === 'join' ? 'active' : ''} onClick={() => { setMode('join'); setError(''); }} type="button">{t.joinRoom}</button>
        </div>
        <form onSubmit={mode === 'create' ? create : join}>
          <label htmlFor="display-name">{t.yourName}</label>
          <div className="field-with-icon"><User /><input id="display-name" value={name} onChange={e => setName(e.target.value)} maxLength={32} placeholder={t.namePlaceholder} autoComplete="name" /></div>
          <label htmlFor="language">{t.language}</label>
          <div className="select-wrap"><Globe /><select id="language" value={language} onChange={e => setLanguage(e.target.value)}>{languages.map(item => <option key={item.code} value={item.code}>{item.native} · {item.name}</option>)}</select><Chevron /></div>
          {mode === 'create' ? <>
            <label htmlFor="room-name">{t.roomName}</label>
            <div className="field-with-icon"><Hash /><input id="room-name" value={roomName} onChange={e => setRoomName(e.target.value)} maxLength={48} placeholder={t.roomNamePlaceholder} /></div>
          </> : <>
            <label htmlFor="room-code">{t.roomCode}</label>
            <div className="field-with-icon code-field"><Hash /><input id="room-code" value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())} maxLength={6} placeholder="AB12CD" autoCapitalize="characters" /></div>
          </>}
          {error && <div className="form-error"><Info /> {error}</div>}
          <button className="primary-action" disabled={busy} type="submit">{busy ? <Spinner /> : mode === 'create' ? <Plus /> : <ArrowRight />}{mode === 'create' ? t.createRoom : t.join}</button>
        </form>
        <div className="card-foot"><Lock /> <span>{t.cardFoot}</span></div>
      </div>
    </section>
    <footer className="lobby-footer"><span>Lingua Room <b>·</b> {t.footerMade}</span><span>{t.footerRooms} <b>·</b> {t.footerOriginal}</span></footer>
  </main>;
}

function Chat({ room: initialRoom, me, languages, onLeave }: { room: Room; me: Profile; languages: Language[]; onLeave: () => void }) {
  const [room, setRoom] = useState(initialRoom);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [members, setMembers] = useState<Person[]>([]);
  const [text, setText] = useState('');
  const [connected, setConnected] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [copied, setCopied] = useState(false);
  const [socketError, setSocketError] = useState('');
  const socket = useRef<WebSocket | null>(null);
  const end = useRef<HTMLDivElement | null>(null);
  const t = dictionary(me.language);
  const languageLabel = useMemo(() => languages.find(item => item.code === me.language)?.native || me.language.toUpperCase(), [languages, me.language]);

  useEffect(() => {
    let stopped = false;
    let retry: number | undefined;
    const connect = () => {
      const wsBase = API_BASE.replace(/^http/, 'ws');
      const query = new URLSearchParams({ member_id: me.id, name: me.name, language: me.language });
      const ws = new WebSocket(`${wsBase}/ws/rooms/${room.id}?${query.toString()}`);
      socket.current = ws;
      ws.onopen = () => { if (!stopped) { setConnected(true); setSocketError(''); } };
      ws.onmessage = event => {
        const incoming = JSON.parse(event.data) as Record<string, any>;
        if (incoming.type === 'room') setRoom(incoming.room as Room);
        if (incoming.type === 'history') setMessages(incoming.messages as ChatMessage[]);
        if (incoming.type === 'presence') setMembers(incoming.members as Person[]);
        if (incoming.type === 'message') setMessages(current => current.some(message => message.id === incoming.message.id) ? current : [...current, incoming.message as ChatMessage]);
        if (incoming.type === 'translation') {
          setMessages(current => current.map(message => message.id === incoming.message_id ? { ...message, content: incoming.content, translation_status: incoming.translation_status } : message));
        }
        if (incoming.type === 'error') setSocketError(incoming.message as string);
      };
      ws.onclose = () => {
        if (!stopped) { setConnected(false); retry = window.setTimeout(connect, 1800); }
      };
      ws.onerror = () => ws.close();
    };
    connect();
    return () => { stopped = true; if (retry) window.clearTimeout(retry); socket.current?.close(); };
  }, [me.id, me.language, me.name, room.id]);

  useEffect(() => { end.current?.scrollIntoView({ behavior: messages.length > 1 ? 'smooth' : 'auto', block: 'end' }); }, [messages.length, messages.map(m => m.translation_status).join()]);

  const send = (event: FormEvent) => {
    event.preventDefault();
    const content = text.trim();
    if (!content || socket.current?.readyState !== WebSocket.OPEN) return;
    socket.current.send(JSON.stringify({ type: 'send', content }));
    setText('');
  };
  const composerKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); (event.currentTarget.form as HTMLFormElement)?.requestSubmit(); }
  };
  const share = async () => {
    const url = `${window.location.origin}${window.location.pathname}?room=${room.id}`;
    try {
      if (navigator.share) await navigator.share({ title: 'Lingua Room', text: t.shareText, url });
      else await navigator.clipboard.writeText(url);
      setCopied(true); window.setTimeout(() => setCopied(false), 1800);
    } catch { /* User closed native share. */ }
  };

  return <main className="chat-page">
    <aside className="chat-sidebar">
      <div className="sidebar-top"><Brand /><button className="icon-button leave-button" onClick={onLeave} title={t.back}><ArrowLeft /></button></div>
      <div className="room-card">
        <div className="room-monogram">{room.name.slice(0, 1).toUpperCase()}</div>
        <div><span className="room-kicker">ROOM · {room.id}</span><h2>{room.name}</h2><p><i className="presence-dot" /> {members.length || 1} {members.length === 1 ? t.people.slice(0, -1) : t.people}</p></div>
        <button className="icon-button room-more" aria-label="Room settings"><More /></button>
      </div>
      <button className="invite-button" onClick={share}><Link /> {copied ? t.copied : t.invite}<span className="invite-code">{room.id}</span></button>
      <nav className="sidebar-nav"><span className="nav-label">{t.messages}</span><button className="nav-current"><ChatBubble /><span>#{room.name}</span><b>{messages.length || ''}</b></button></nav>
      <div className="members-section"><div className="section-heading"><span>{t.members}</span><b>{members.length || 1}</b></div>
        <div className="member-list">{(members.length ? members : [me]).map(person => <MemberItem key={person.id} person={person} me={me} languages={languages} t={t} />)}</div>
      </div>
      <div className="sidebar-bottom"><div className="translation-status"><span className="translation-glyph"><Translate /></span><div><b>{t.liveTranslation}</b><small>{languageLabel}</small></div><i /></div><div className="me-row"><Avatar name={me.name} size="small" /><span>{me.name}<small>{languageLabel}</small></span><button className="icon-button"><ChevronUp /></button></div></div>
    </aside>

    <section className="chat-main">
      <header className="chat-topbar"><div className="mobile-brand"><Brand /></div><div className="topbar-room"><span className="topbar-label">{t.messages}</span><h1>{room.name}</h1></div><div className="topbar-right"><span className="translate-pill"><Translate /> {t.liveTranslation}</span><button className="icon-button" onClick={share} aria-label={t.copyLink}><Share /></button><button className="icon-button desktop-only"><Search /></button></div></header>
      {!connected && <div className="connection-banner"><Spinner /> {socketError || t.connectionLost}</div>}
      <div className="message-scroll">
        <div className="day-divider"><span>{t.today}</span></div>
        {!messages.length && <div className="empty-chat"><div className="empty-art"><ChatBubble /></div><h2>{t.emptyTitle}</h2><p>{t.emptyText}</p></div>}
        <div className="message-stack">{messages.map(message => <MessageBubble key={message.id} message={message} own={message.author_id === me.id} t={t} showOriginal={expanded.has(message.id)} onToggle={() => setExpanded(current => { const next = new Set(current); next.has(message.id) ? next.delete(message.id) : next.add(message.id); return next; })} />)}</div>
        <div ref={end} />
      </div>
      <form className="composer" onSubmit={send}><button type="button" className="composer-icon desktop-only" aria-label="Attach file"><Paperclip /></button><textarea value={text} onChange={event => setText(event.target.value)} onKeyDown={composerKeyDown} placeholder={connected ? t.messagePlaceholder : t.connectionLost} disabled={!connected} rows={1} maxLength={4000} /><button type="button" className="composer-icon" aria-label="Emoji"><Smile /></button><button type="submit" className="send-button" disabled={!text.trim() || !connected} aria-label={t.send}><Send /></button></form>
    </section>
  </main>;
}

function MemberItem({ person, me, languages, t }: { person: Person; me: Profile; languages: Language[]; t: Copy }) {
  const language = languages.find(item => item.code === person.language)?.native || person.language;
  return <div className="member-item"><Avatar name={person.name} size="small" online /><div><b>{person.id === me.id ? t.you : person.name}</b><small>{language}</small></div><i className="member-online" /></div>;
}

function MessageBubble({ message, own, t, showOriginal, onToggle }: { message: ChatMessage; own: boolean; t: Copy; showOriginal: boolean; onToggle: () => void }) {
  const time = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(new Date(message.created_at));
  const displayOriginal = showOriginal && message.content !== message.original_content;
  return <article className={`message-row ${own ? 'own' : ''}`}><Avatar name={message.author_name} size="message" /><div className="message-wrap"><div className="message-meta"><b>{own ? t.you : message.author_name}</b><span>{time}</span></div><div className={`bubble ${own ? 'bubble-own' : ''}`}><p>{displayOriginal ? message.original_content : message.content}</p>{message.translation_status === 'pending' && <div className="translation-note pending"><Spinner /> {t.translating}</div>}{message.translation_status === 'unavailable' && <div className="translation-note unavailable"><Info /> {t.unavailable}</div>}{message.translation_status === 'complete' && <div className="translation-note translated"><Translate /> {displayOriginal ? t.original : t.translated}</div>}</div>{message.translation_status === 'complete' && message.content !== message.original_content && <button className="original-toggle" onClick={onToggle}>{showOriginal ? t.translated : t.original}<Chevron /></button>}</div></article>;
}

function Avatar({ name, size, online = false }: { name: string; size: 'small' | 'message'; online?: boolean }) {
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || '?';
  const hue = [...name].reduce((total, char) => total + char.charCodeAt(0), 0) % 360;
  return <div className={`avatar avatar-${size}`} style={{ background: `hsl(${hue} 46% 82%)`, color: `hsl(${hue} 36% 26%)` }}>{initials}{online && <i />}</div>;
}

function Brand() { return <div className="brand"><span className="brand-mark"><span /><span /><span /></span><b>lingua</b><em>room</em></div>; }

function Icon({ children }: { children: ReactNode }) { return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>; }
function Sparkle() { return <Icon><path d="m12 2 1.4 5.2L18 9l-4.6 1.8L12 16l-1.4-5.2L6 9l4.6-1.8L12 2Z" /><path d="m19 15 .7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7L19 15Z" /></Icon>; }
function Shield() { return <Icon><path d="M12 3 4.8 6v5c0 4.6 3 8 7.2 10 4.2-2 7.2-5.4 7.2-10V6L12 3Z" /><path d="m9 12 2 2 4-4" /></Icon>; }
function User() { return <Icon><circle cx="12" cy="8" r="3.2" /><path d="M5.5 20c.7-3.3 3.1-5 6.5-5s5.8 1.7 6.5 5" /></Icon>; }
function Globe() { return <Icon><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></Icon>; }
function Hash() { return <Icon><path d="M4 9h16M4 15h16M10 3 8 21m8-18-2 18" /></Icon>; }
function Chevron() { return <Icon><path d="m7 10 5 5 5-5" /></Icon>; }
function ChevronUp() { return <Icon><path d="m7 14 5-5 5 5" /></Icon>; }
function Plus() { return <Icon><path d="M12 5v14M5 12h14" /></Icon>; }
function ArrowRight() { return <Icon><path d="M5 12h14m-6-6 6 6-6 6" /></Icon>; }
function ArrowLeft() { return <Icon><path d="M19 12H5m6 6-6-6 6-6" /></Icon>; }
function Lock() { return <Icon><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></Icon>; }
function Info() { return <Icon><circle cx="12" cy="12" r="9" /><path d="M12 11v5m0-8h.01" /></Icon>; }
function Spinner() { return <span className="spinner" aria-hidden="true" />; }
function Translate() { return <Icon><path d="M5 5h8m-4-2v2m0 0c0 4-2 6.5-5 8m2-5c1 1.7 2.4 3 4 4" /><path d="M14 18h6m-3-12 4 12m-6-4h5" /></Icon>; }
function Link() { return <Icon><path d="M10 13a5 5 0 0 0 7.1.1l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1" /><path d="M14 11a5 5 0 0 0-7.1-.1l-2 2A5 5 0 0 0 12 20l1.1-1.1" /></Icon>; }
function More() { return <Icon><circle cx="5" cy="12" r=".8" fill="currentColor" /><circle cx="12" cy="12" r=".8" fill="currentColor" /><circle cx="19" cy="12" r=".8" fill="currentColor" /></Icon>; }
function ChatBubble() { return <Icon><path d="M20 11.5a7.5 7.5 0 0 1-8 7.5 9.5 9.5 0 0 1-3.6-.7L4 20l1.3-3.7A7.4 7.4 0 0 1 4 12a7.5 7.5 0 0 1 8-7.5 7.5 7.5 0 0 1 8 7Z" /></Icon>; }
function Search() { return <Icon><circle cx="11" cy="11" r="6" /><path d="m16 16 4 4" /></Icon>; }
function Share() { return <Icon><circle cx="18" cy="5" r="2" /><circle cx="6" cy="12" r="2" /><circle cx="18" cy="19" r="2" /><path d="m8 11 8-5m-8 7 8 5" /></Icon>; }
function Paperclip() { return <Icon><path d="m20 11-8.4 8.4a5 5 0 0 1-7.1-7.1L13 3.8a3.5 3.5 0 1 1 5 5L9.4 17.4a2 2 0 1 1-2.8-2.8l8-8" /></Icon>; }
function Smile() { return <Icon><circle cx="12" cy="12" r="9" /><path d="M8 14s1.3 2 4 2 4-2 4-2M9 9h.01M15 9h.01" /></Icon>; }
function Send() { return <Icon><path d="m21 3-7.4 18-3.2-7.4L3 10.4 21 3Z" /><path d="m10.4 13.6 4.2-4.2" /></Icon>; }
