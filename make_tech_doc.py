from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 HRFlowable, Table, TableStyle, PageBreak, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

W, H = A4

# ── Colour palette ──────────────────────────────────────────────
INK      = colors.HexColor('#0f172a')
INK2     = colors.HexColor('#475569')
INK3     = colors.HexColor('#94a3b8')
PURPLE   = colors.HexColor('#7c3aed')
PURPLE_D = colors.HexColor('#5b21b6')
PURPLE_L = colors.HexColor('#ede9fe')
GREEN    = colors.HexColor('#059669')
AMBER    = colors.HexColor('#d97706')
RED      = colors.HexColor('#dc2626')
BLUE     = colors.HexColor('#2563eb')
CODEBG   = colors.HexColor('#1e293b')
CODEFG   = colors.HexColor('#e2e8f0')
ROWALT   = colors.HexColor('#f8fafc')
ROWHEAD  = colors.HexColor('#7c3aed')

# ── Paragraph styles ────────────────────────────────────────────
def sty(name, **kw):
    base = ParagraphStyle(name, fontName='Helvetica', fontSize=10,
                          leading=16, textColor=INK, spaceAfter=4)
    for k, v in kw.items():
        setattr(base, k, v)
    return base

TITLE  = sty('TITLE',  fontSize=30, fontName='Helvetica-Bold', textColor=PURPLE_D,
             alignment=TA_CENTER, spaceAfter=6, leading=36)
SUBTITLE=sty('SUBT',   fontSize=13, textColor=INK2, alignment=TA_CENTER, spaceAfter=4)
META   = sty('META',   fontSize=9,  textColor=INK3, alignment=TA_CENTER, spaceAfter=0)
SECNUM = sty('SECNUM', fontSize=9,  textColor=PURPLE, fontName='Helvetica-Bold',
             spaceAfter=0, spaceBefore=18)
H1     = sty('H1',     fontSize=17, fontName='Helvetica-Bold', textColor=PURPLE_D,
             spaceAfter=6, spaceBefore=4, leading=22)
H2     = sty('H2',     fontSize=13, fontName='Helvetica-Bold', textColor=PURPLE,
             spaceAfter=4, spaceBefore=12, leading=18)
H3     = sty('H3',     fontSize=11, fontName='Helvetica-Bold', textColor=INK,
             spaceAfter=3, spaceBefore=8, leading=15)
BODY   = sty('BODY',   fontSize=10, textColor=INK, leading=17, spaceAfter=5,
             alignment=TA_JUSTIFY)
BUL    = sty('BUL',    fontSize=10, textColor=INK, leading=16, spaceAfter=3,
             leftIndent=16)
BUL2   = sty('BUL2',   fontSize=9.5,textColor=INK2,leading=15, spaceAfter=2,
             leftIndent=30)
CODE   = sty('CODE',   fontSize=9,  fontName='Courier', textColor=CODEFG,
             backColor=CODEBG, leading=14, spaceAfter=0, leftIndent=8,
             rightIndent=8, spaceBefore=0)
LABEL  = sty('LABEL',  fontSize=9,  fontName='Helvetica-Bold', textColor=PURPLE,
             spaceAfter=2, spaceBefore=6)
NOTE   = sty('NOTE',   fontSize=9,  textColor=INK2, leading=14,
             spaceAfter=4, leftIndent=10)
FOOT   = sty('FOOT',   fontSize=8,  textColor=INK3, alignment=TA_CENTER, spaceAfter=0)
BADGE  = sty('BADGE',  fontSize=8.5,fontName='Helvetica-Bold', textColor=colors.white,
             alignment=TA_CENTER)

def hr(color=PURPLE, thick=1.5):
    return HRFlowable(width='100%', thickness=thick, color=color,
                      spaceAfter=10, spaceBefore=4)

def hr_light():
    return HRFlowable(width='100%', thickness=0.5, color=INK3,
                      spaceAfter=8, spaceBefore=4)

def code_block(lines):
    out = []
    out.append(Spacer(1, 4))
    for line in lines:
        out.append(Paragraph(line, CODE))
    out.append(Spacer(1, 6))
    return out

def tbl(rows, col_widths, head=True):
    t = Table(rows, colWidths=col_widths, repeatRows=1 if head else 0)
    style = [
        ('FONTNAME',  (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), INK),
        ('GRID',      (0,0), (-1,-1), 0.4, INK3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, ROWALT]),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING',(0,0), (-1,-1), 7),
    ]
    if head:
        style += [
            ('BACKGROUND', (0,0), (-1,0), ROWHEAD),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ]
    t.setStyle(TableStyle(style))
    return t

# ── BUILD STORY ──────────────────────────────────────────────────
story = []

# ══ COVER ══════════════════════════════════════════════════════
story.append(Spacer(1, 2.5*cm))
story.append(Paragraph('DocuVault AI Assistant', TITLE))
story.append(Paragraph('Technical Documentation', sty('T2', fontSize=20,
    fontName='Helvetica-Bold', textColor=PURPLE, alignment=TA_CENTER, spaceAfter=8)))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph('Chatbot &amp; Voice Bot — Architecture, Implementation &amp; Configuration', SUBTITLE))
story.append(Spacer(1, 0.3*cm))
story.append(hr(PURPLE, 2.5))
story.append(Spacer(1, 0.3*cm))

meta_rows = [
    ['Version', '2.0'],
    ['Date', 'March 2024'],
    ['Stack', 'Django 4 · ChromaDB · Groq (LLaMA-3) · Web Speech API · SSE'],
    ['Scope', 'Voice Bot · Text Chatbot · RAG Pipeline · TTS/STT'],
]
story.append(tbl(
    [['Property', 'Details']] + meta_rows,
    [4*cm, 12.5*cm], head=True
))
story.append(Spacer(1, 1*cm))

toc_items = [
    ('1', 'System Architecture Overview'),
    ('2', 'RAG Pipeline (Retrieval-Augmented Generation)'),
    ('3', 'Text Chatbot — Implementation'),
    ('4', 'SSE Streaming — How Real-Time Responses Work'),
    ('5', 'Voice Bot — Speech-to-Text (STT)'),
    ('6', 'Voice Bot — Text-to-Speech (TTS)'),
    ('7', 'Voice Modal — UI States & Flow'),
    ('8', 'Configuration Reference'),
    ('9', 'Browser Compatibility'),
    ('10', 'Troubleshooting Guide'),
]
story.append(Paragraph('Table of Contents', H2))
for num, title in toc_items:
    story.append(Paragraph(f'  {num}.  {title}', BUL))
story.append(PageBreak())

# ══ SECTION 1 — ARCHITECTURE ════════════════════════════════════
story.append(Paragraph('SECTION 1', SECNUM))
story.append(Paragraph('System Architecture Overview', H1))
story.append(hr())
story.append(Paragraph(
    'DocuVault AI Assistant is a full-stack Django web application combining a document management system '
    'with an AI-powered chatbot. The system uses Retrieval-Augmented Generation (RAG) to ground AI '
    'responses in uploaded documents. Voice input and output are handled entirely client-side using '
    'the Web Speech API, with a server-side Whisper fallback for unsupported browsers.',
    BODY))

story.append(Paragraph('High-Level Architecture', H2))
arch = [
    ['Layer', 'Component', 'Technology'],
    ['Frontend', 'Chat UI + Voice Modal', 'HTML/CSS/Vanilla JS'],
    ['Frontend', 'Speech-to-Text (STT)', 'Web Speech API (SpeechRecognition)'],
    ['Frontend', 'Text-to-Speech (TTS)', 'Web Speech Synthesis API'],
    ['Frontend', 'Streaming client', 'fetch() + ReadableStream + SSE parser'],
    ['Backend', 'Web framework', 'Django 4.x'],
    ['Backend', 'LLM inference', 'Groq API via LangChain ChatGroq'],
    ['Backend', 'LLM model', 'LLaMA-3 70B (groq/llama3-70b-8192)'],
    ['Backend', 'Vector store', 'ChromaDB (local persistence)'],
    ['Backend', 'Embeddings', 'HuggingFace sentence-transformers'],
    ['Backend', 'PDF parsing', 'PyMuPDF (fitz) + pdfplumber'],
    ['Backend', 'STT fallback', 'faster-whisper (server-side)'],
    ['Backend', 'Streaming protocol', 'Server-Sent Events (SSE) over HTTP'],
]
story.append(tbl(arch, [3.5*cm, 5*cm, 8*cm]))
story.append(Spacer(1, 0.5*cm))

story.append(Paragraph('Request Flow', H2))
flow = [
    '1.  User types or speaks a question.',
    '2.  If voice: SpeechRecognition converts audio to text (client-side).',
    '3.  Text is POST-ed to /chatbot/query/stream/ with CSRF token.',
    '4.  Django retrieves relevant document chunks from ChromaDB (RAG).',
    '5.  Chunks + conversation history are passed to Groq LLM as context.',
    '6.  LLM streams tokens back via SSE (Server-Sent Events).',
    '7.  Frontend renders tokens progressively into the chat bubble.',
    '8.  TTS speaks each sentence as it arrives (voice mode only).',
    '9.  After response completes, voice mode auto-resumes listening.',
]
for f in flow:
    story.append(Paragraph(f, BUL))
story.append(PageBreak())

# ══ SECTION 2 — RAG ═════════════════════════════════════════════
story.append(Paragraph('SECTION 2', SECNUM))
story.append(Paragraph('RAG Pipeline — Retrieval-Augmented Generation', H1))
story.append(hr())
story.append(Paragraph(
    'RAG allows the chatbot to answer questions grounded in your uploaded documents rather than relying '
    'solely on the LLM\'s training data. Documents are chunked, embedded into vectors, and stored in '
    'ChromaDB. At query time, the most relevant chunks are retrieved and injected into the LLM prompt.',
    BODY))

story.append(Paragraph('Auto-Indexing Pipeline', H2))
story.append(Paragraph('Documents are automatically indexed when uploaded. No manual step required.', BODY))
idx = [
    '1.  User uploads a PDF through the DocuVault interface.',
    '2.  Django signals.py fires post_save on the Document model.',
    '3.  A daemon background thread calls _index_in_background(document_id).',
    '4.  PDF is parsed page-by-page using PyMuPDF / pdfplumber.',
    '5.  Text is split into overlapping chunks (512 tokens, 50-token overlap).',
    '6.  Each chunk is embedded using HuggingFace sentence-transformers.',
    '7.  Embeddings are stored in ChromaDB with metadata (doc title, page number).',
    '8.  DocumentEmbedding model updated: is_indexed=True, status=completed.',
]
for i in idx:
    story.append(Paragraph(i, BUL))

story.append(Paragraph('Hybrid Search', H2))
story.append(Paragraph(
    'At query time, the system performs hybrid retrieval combining semantic similarity '
    '(cosine distance on embeddings) with keyword matching (BM25-style). Results are '
    're-ranked and the top-N chunks are selected as context.', BODY))

story.append(Paragraph('Source Attribution', H2))
story.append(Paragraph(
    'Each retrieved chunk carries metadata: document title, page number, and content type '
    '(text, table, image). After the LLM responds, the frontend displays source chips '
    'below the answer showing which document pages were used. If no document context '
    'was used, a "General knowledge" badge is shown instead.', BODY))

story.append(Paragraph('Key Files', H2))
files = [
    ['File', 'Purpose'],
    ['documents/signals.py', 'Django post_save signal — triggers auto-indexing'],
    ['documents/rag/llm_manager.py', 'Groq LLM wrapper with stream() support'],
    ['documents/rag/conversation.py', 'query_stream() — RAG retrieval + LLM call'],
    ['documents/rag/config.py', 'SYSTEM_PROMPT — document-first instructions'],
    ['documents/rag_views.py', 'chatbot_query_stream_view — SSE endpoint'],
]
story.append(tbl(files, [5.5*cm, 11*cm]))
story.append(PageBreak())

# ══ SECTION 3 — TEXT CHATBOT ════════════════════════════════════
story.append(Paragraph('SECTION 3', SECNUM))
story.append(Paragraph('Text Chatbot — Implementation', H1))
story.append(hr())
story.append(Paragraph(
    'The text chatbot is a streaming chat interface built with vanilla JavaScript. '
    'Messages are rendered progressively as tokens arrive from the server. '
    'Markdown formatting (bold, italic, code, lists) is applied in real time.', BODY))

story.append(Paragraph('Frontend — sendQuery() Function', H2))
story.append(Paragraph('Core function that handles the full request-response cycle:', BODY))
story += code_block([
    'async function sendQuery(override) {',
    '  // 1. Cancel any in-progress stream (AbortController)',
    '  if (streamAbort) { streamAbort.abort(); streamAbort = null; }',
    '  streamAbort = new AbortController();',
    '  setBusy(true);',
    '  addMsg("human", esc(q), []);   // show user bubble',
    '  const bub = mkBub();           // create empty AI bubble',
    '',
    '  // 2. POST to SSE endpoint',
    '  const resp = await fetch("/chatbot/query/stream/", {',
    '    method: "POST", body: fd,',
    '    signal: streamAbort.signal   // allows cancellation',
    '  });',
    '',
    '  // 3. Read SSE stream token by token',
    '  const reader = resp.body.getReader();',
    '  while (true) {',
    '    const { done, value } = await reader.read();',
    '    if (done) break;',
    '    // parse SSE events: session, sources, token, done, error',
    '  }',
    '}',
])

story.append(Paragraph('SSE Event Types', H2))
events = [
    ['Event Type', 'Payload', 'Action'],
    ['session', '{ session_id: 123 }', 'Updates sid variable for conversation continuity'],
    ['sources', '{ data: [...] }', 'Renders source chips below AI bubble immediately'],
    ['token', '{ data: "word " }', 'Appends token to bubble, triggers TTS sentence flush'],
    ['done', '{ data: "full text" }', 'Finalises bubble, saves to DB, restarts voice if active'],
    ['error', '{ data: "msg" }', 'Shows error message in bubble'],
]
story.append(tbl(events, [2.5*cm, 5.5*cm, 8.5*cm]))
story.append(PageBreak())

# ══ SECTION 4 — SSE STREAMING ═══════════════════════════════════
story.append(Paragraph('SECTION 4', SECNUM))
story.append(Paragraph('SSE Streaming — How Real-Time Responses Work', H1))
story.append(hr())
story.append(Paragraph(
    'Server-Sent Events (SSE) allow the server to push data to the browser progressively '
    'over a single HTTP connection. This enables the chatbot to display text and speak '
    'audio before the full AI response is complete, giving a natural real-time feel.', BODY))

story.append(Paragraph('Why SSE Instead of WebSockets?', H2))
pts = [
    'SSE works over standard HTTP/HTTPS — no special server configuration needed.',
    'SSE is one-directional (server to client) which matches the chat pattern perfectly.',
    'Built-in reconnection and event ID support in the browser.',
    'EventSource API is native — however, since we use POST (not GET), we use fetch() + ReadableStream instead of EventSource directly.',
]
for p in pts:
    story.append(Paragraph(p, BUL))

story.append(Paragraph('Django Backend — chatbot_query_stream_view', H2))
story += code_block([
    '@login_required',
    '@require_http_methods(["POST"])',
    'def chatbot_query_stream_view(request):',
    '    def sse_generator():',
    '        # 1. Emit session ID',
    '        yield f\'data: {json.dumps({"type":"session","session_id":...})}\\n\\n\'',
    '',
    '        for event in chatbot.query_stream(question=question):',
    '            if event["type"] == "sources":',
    '                yield f\'data: {json.dumps({"type":"sources","data":...})}\\n\\n\'',
    '            elif event["type"] == "token":',
    '                yield f\'data: {json.dumps({"type":"token","data":chunk})}\\n\\n\'',
    '            elif event["type"] == "done":',
    '                yield f\'data: {json.dumps({"type":"done","data":...})}\\n\\n\'',
    '',
    '    response = StreamingHttpResponse(sse_generator(),',
    '                                      content_type="text/event-stream")',
    '    response["Cache-Control"] = "no-cache"',
    '    response["X-Accel-Buffering"] = "no"   # disables nginx buffering',
    '    return response',
])

story.append(Paragraph('AbortController — Cancelling Stale Streams', H2))
story.append(Paragraph(
    'When a new query is sent while a previous stream is still reading, the old fetch '
    'is cancelled via AbortController. This prevents stacked network connections and '
    'duplicate bubble rendering.', BODY))
story += code_block([
    'let streamAbort = null;',
    '',
    'async function sendQuery(override) {',
    '  if (streamAbort) { streamAbort.abort(); }   // cancel previous',
    '  streamAbort = new AbortController();',
    '  const resp = await fetch(url, { signal: streamAbort.signal, ... });',
    '  // ...',
    '  // In finally block:',
    '  streamAbort = null;',
    '}',
])
story.append(PageBreak())

# ══ SECTION 5 — STT ════════════════════════════════════════════
story.append(Paragraph('SECTION 5', SECNUM))
story.append(Paragraph('Voice Bot — Speech-to-Text (STT)', H1))
story.append(hr())
story.append(Paragraph(
    'Speech recognition is handled client-side using the Web Speech API (SpeechRecognition). '
    'This runs entirely in the browser — no audio is sent to the Django server for transcription '
    'unless the browser does not support the API, in which case a server-side Whisper fallback is used.',
    BODY))

story.append(Paragraph('SpeechRecognition Setup', H2))
story += code_block([
    'const SR = window.SpeechRecognition || window.webkitSpeechRecognition;',
    'recog = new SR();',
    'recog.continuous     = true;    // keeps listening until stopped',
    'recog.interimResults = true;    // shows partial results in real time',
    'recog.lang           = "en-IN"; // accent / language for recognition',
    'recog.maxAlternatives = 1;',
])

story.append(Paragraph('Key Events', H2))
evts = [
    ['Event', 'What It Does'],
    ['onstart', 'Sets UI to Listening state, updates status text'],
    ['onresult', 'Accumulates final + interim transcript; resets 2-second silence timer'],
    ['onerror', 'Handles not-allowed (mic blocked), no-speech (silence), language-not-supported (falls back to en-US)'],
    ['onend', 'Fires when recognition stops; triggers tryRst() to restart if still in voice session'],
]
story.append(tbl(evts, [4*cm, 12.5*cm]))

story.append(Paragraph('Silence Detection — Auto-Send', H2))
story.append(Paragraph(
    'A 2-second silence timer is reset on every onresult event. When the timer fires '
    '(user stops speaking for 2 seconds), the accumulated transcript is automatically '
    'sent as a query without any button press.', BODY))
story += code_block([
    'recog.onresult = (e) => {',
    '  // ... accumulate transcript ...',
    '  clearTimeout(silTimer);',
    '  silTimer = setTimeout(() => {',
    '    const final = accumulated.trim();',
    '    if (isListening && final) {',
    '      isListening = false;',
    '      _killRecog();       // null callbacks, then abort — no ghost events',
    '      sendQuery(final);   // fire the query',
    '    }',
    '  }, 2000);  // 2 second silence threshold',
    '};',
])

story.append(Paragraph('_killRecog() — Preventing Memory Leaks', H2))
story.append(Paragraph(
    'A critical helper that nullifies ALL event callbacks before calling abort(). '
    'Without this, Chrome fires ghost onend events after abort(), which triggers '
    'tryRst() creating a new SR instance — causing memory leaks that crash the tab '
    'after 2-3 voice queries.', BODY))
story += code_block([
    'function _killRecog() {',
    '  if (recog) {',
    '    recog.onresult = null;   // prevent ghost events',
    '    recog.onerror  = null;',
    '    recog.onend    = null;',
    '    recog.onstart  = null;',
    '    try { recog.abort(); } catch {}',
    '    recog = null;',
    '  }',
    '}',
])

story.append(Paragraph('Server-Side Whisper Fallback', H2))
story.append(Paragraph(
    'If the browser does not support SpeechRecognition, audio is recorded via MediaRecorder '
    'and uploaded to /chatbot/voice/transcribe/ where faster-whisper transcribes it server-side.', BODY))
story.append(Paragraph('Install: pip install faster-whisper', LABEL))
story.append(PageBreak())

# ══ SECTION 6 — TTS ════════════════════════════════════════════
story.append(Paragraph('SECTION 6', SECNUM))
story.append(Paragraph('Voice Bot — Text-to-Speech (TTS)', H1))
story.append(hr())
story.append(Paragraph(
    'AI responses are spoken aloud using the Web Speech Synthesis API. TTS is activated '
    'in two scenarios: (1) when the user toggles Voice On via the toolbar button, or '
    '(2) automatically when the user is in a voice session (used the mic button).', BODY))

story.append(Paragraph('Voice Selection Priority', H2))
story.append(Paragraph(
    'The system tries to find the best available voice on the user\'s device in this order:', BODY))
story += code_block([
    'const want = ["Microsoft Heera",    // Indian English female (Windows)',
    '              "Microsoft Ravi",     // Indian English male (Windows)',
    '              "Lekha",              // Indian English (macOS)',
    '              "Veena"];             // Indian English (macOS)',
    '',
    '// Fallback chain:',
    'bestV = vs.find(v => v.lang === "en-IN")      // any en-IN voice',
    '     || vs.find(v => v.lang.startsWith("en")) // any English voice',
    '     || vs[0];                                // first available voice',
])

story.append(Paragraph('Change Voice / Accent', H2))
story.append(Paragraph('To use a different accent, edit two locations in chatbot.html:', BODY))
story.append(Paragraph('1. Recognition language (what it listens in):', LABEL))
story += code_block(['let srLang = "en-IN";   // change to en-US, en-GB, en-AU etc.'])
story.append(Paragraph('2. Voice priority list (what it speaks in):', LABEL))
story += code_block(['const want = ["Microsoft Heera", "Microsoft Ravi", ...];'])
story.append(Paragraph('To find available voices on your system, run in browser console:', LABEL))
story += code_block(['speechSynthesis.getVoices().forEach(v => console.log(v.name, v.lang));'])

story.append(Paragraph('Speed and Pitch', H2))
story += code_block([
    'utt.rate  = 1.18;   // speed: 1.0=normal, 1.5=fast, 2.0=max',
    'utt.pitch = 1.05;   // pitch: 0.5=low, 1.0=normal, 2.0=high',
])
story.append(Paragraph('Both values are found in the pumpTTS() function in chatbot.html.', NOTE))

story.append(Paragraph('Sentence Streaming — TTS Starts Before Full Response', H2))
story.append(Paragraph(
    'Rather than waiting for the complete AI response, TTS starts as soon as the first '
    'complete sentence arrives during streaming. A regex extracts sentences ending in '
    '. ! ? or newline and speaks them immediately.', BODY))
story += code_block([
    'function ttsFlush(buf) {',
    '  const re = /[^.!?\\n]+[.!?\\n]+/g;',
    '  let last = 0, m;',
    '  while ((m = re.exec(buf)) !== null) {',
    '    speakChunk(m[0].trim());         // speak each complete sentence',
    '    last = m.index + m[0].length;',
    '  }',
    '  return buf.slice(last);            // return remaining partial sentence',
    '}',
])

story.append(Paragraph('TTS Queue Management', H2))
ttsq = [
    ['Issue', 'Solution'],
    ['Chrome stops speaking silently', '25-second safety timer in pumpTTS() recovers automatically'],
    ['Queue overflow / memory spiral', 'Queue capped at 8 items; trimmed to 4 when exceeded'],
    ['Corrupted queue from cancel()', 'speechSynthesis.cancel() removed from pumpTTS(); only called in stopSpeak()'],
    ['Voice not loaded yet', 'loadVoices() called on voiceschanged event + 1s timeout fallback'],
]
story.append(tbl(ttsq, [5*cm, 11.5*cm]))
story.append(PageBreak())

# ══ SECTION 7 — VOICE MODAL ═════════════════════════════════════
story.append(Paragraph('SECTION 7', SECNUM))
story.append(Paragraph('Voice Modal — UI States and Flow', H1))
story.append(hr())
story.append(Paragraph(
    'When the mic button is clicked, a full-screen voice modal opens with an animated orb '
    'that changes colour based on the current voice state. The modal wraps the same underlying '
    'voice engine — it is purely a UI layer on top of the STT/TTS functions.', BODY))

story.append(Paragraph('Modal States', H2))
states = [
    ['State', 'Orb Colour', 'Visual', 'Description'],
    ['idle', 'Purple', 'Slow pulse', 'Modal just opened, waiting to start'],
    ['listening', 'Red', 'Fast pulse', 'Microphone active, user is speaking'],
    ['processing', 'Amber', 'Spinning', 'Query sent, waiting for LLM response'],
    ['speaking', 'Green', 'Wave bars animate', 'AI is speaking the response via TTS'],
]
story.append(tbl(states, [2.5*cm, 3*cm, 3.5*cm, 7.5*cm]))

story.append(Paragraph('State Transition Flow', H2))
flow2 = [
    'openVoiceModal()  ->  idle state  ->  startVoice() after 400ms',
    'startVoice()      ->  getUserMedia() permission check  ->  startSR()',
    'startSR()         ->  listening state  ->  user speaks',
    'silence 2s        ->  _killRecog()  ->  processing state  ->  sendQuery()',
    'sendQuery()       ->  SSE stream  ->  tokens arrive  ->  pumpTTS()',
    'pumpTTS()         ->  speaking state  ->  SpeechSynthesis speaks',
    'TTS ends          ->  afterSpeak()  ->  scheduleNextListen()  ->  startSR()',
    '                  ->  back to listening state  ->  loop continues',
]
for f in flow2:
    story.append(Paragraph(f, BUL))

story.append(Paragraph('Conversation Loop', H2))
story.append(Paragraph(
    'After the AI finishes speaking, the system automatically returns to listening mode '
    'after 700ms. This creates a continuous voice conversation without the user needing '
    'to press any button. The loop continues until the user clicks Stop or closes the modal.',
    BODY))

story.append(Paragraph('Modal Controls', H2))
ctrls = [
    ['Control', 'Action'],
    ['Stop button (square icon)', 'If listening: stops and restarts. If speaking: stops TTS. If idle: closes modal.'],
    ['Send Now button', 'Manually sends current transcript without waiting for silence timeout.'],
    ['Close (x) button', 'Stops voice session, closes modal, returns focus to text input.'],
    ['ESC key', 'Closes modal (same as Close button).'],
    ['Click outside modal', 'Closes modal (click on dark overlay).'],
]
story.append(tbl(ctrls, [4.5*cm, 12*cm]))
story.append(PageBreak())

# ══ SECTION 8 — CONFIGURATION ════════════════════════════════════
story.append(Paragraph('SECTION 8', SECNUM))
story.append(Paragraph('Configuration Reference', H1))
story.append(hr())

story.append(Paragraph('Voice Settings — chatbot.html', H2))
cfg = [
    ['Setting', 'Location', 'Default', 'Description'],
    ['srLang', 'Line ~690', 'en-IN', 'Recognition language/accent for STT'],
    ['utt.rate', 'pumpTTS()', '1.18', 'TTS speech speed (0.1 to 2.0)'],
    ['utt.pitch', 'pumpTTS()', '1.05', 'TTS voice pitch (0.5 to 2.0)'],
    ['want[]', 'loadVoices()', 'Microsoft Heera...', 'Ordered list of preferred TTS voices'],
    ['2000 (ms)', 'silTimer', '2000', 'Silence duration before auto-send (milliseconds)'],
    ['700 (ms)', 'scheduleNextListen()', '700', 'Delay before resuming listen after TTS ends'],
    ['8 (items)', 'speakChunk()', '8', 'Maximum TTS queue size before trimming'],
]
story.append(tbl(cfg, [3*cm, 3*cm, 3.5*cm, 7*cm]))

story.append(Paragraph('RAG Settings — documents/rag/config.py', H2))
rag_cfg = [
    ['Setting', 'Description'],
    ['SYSTEM_PROMPT', 'Instructs LLM to prefer document context over general knowledge'],
    ['n_results', 'Number of chunks retrieved per query (default: 5)'],
    ['chunk_size', 'Token size per chunk when indexing PDFs (default: 512)'],
    ['chunk_overlap', 'Overlap between adjacent chunks (default: 50 tokens)'],
    ['use_hybrid', 'Enable hybrid semantic + keyword search (default: True)'],
    ['use_rewrite', 'Enable query rewriting for better retrieval (default: True)'],
]
story.append(tbl(rag_cfg, [4.5*cm, 12*cm]))

story.append(Paragraph('Django URLs — documents/urls.py', H2))
urls = [
    ['URL', 'View', 'Purpose'],
    ['/chatbot/', 'chatbot_view', 'Main chatbot page (GET)'],
    ['/chatbot/query/stream/', 'chatbot_query_stream_view', 'SSE streaming endpoint (POST)'],
    ['/chatbot/voice/transcribe/', 'voice_transcribe_view', 'Whisper STT fallback (POST)'],
    ['/chatbot/clear/', 'clear_chat', 'Clear conversation history (POST)'],
]
story.append(tbl(urls, [5*cm, 5.5*cm, 6*cm]))
story.append(PageBreak())

# ══ SECTION 9 — BROWSER COMPATIBILITY ═══════════════════════════
story.append(Paragraph('SECTION 9', SECNUM))
story.append(Paragraph('Browser Compatibility', H1))
story.append(hr())

compat = [
    ['Feature', 'Chrome', 'Edge', 'Firefox', 'Safari'],
    ['Text Chatbot (SSE)', 'Full', 'Full', 'Full', 'Full'],
    ['SpeechRecognition (STT)', 'Full', 'Full', 'Not supported', 'Partial'],
    ['SpeechSynthesis (TTS)', 'Full', 'Full', 'Full', 'Full'],
    ['Indian voices (en-IN)', 'Yes (Windows)', 'Yes (Windows)', 'System only', 'macOS only'],
    ['Voice Modal', 'Full', 'Full', 'No STT', 'Partial'],
    ['Whisper Fallback (STT)', 'N/A', 'N/A', 'Yes', 'Yes'],
]
story.append(tbl(compat, [5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph(
    'Recommended: Google Chrome or Microsoft Edge on Windows for full Indian English voice support '
    '(Microsoft Heera / Microsoft Ravi voices). Firefox users will use the server-side Whisper '
    'fallback for STT and system voices for TTS.', NOTE))

story.append(Paragraph('HTTPS Requirement', H2))
story.append(Paragraph(
    'SpeechRecognition requires either HTTPS or localhost. On HTTP with a non-localhost hostname '
    '(e.g., http://192.168.1.10:8000), the browser will block microphone access and the voice bot '
    'will show a "Microphone blocked" error. For local development, always use http://127.0.0.1:8000 '
    'or http://localhost:8000. For production, deploy with HTTPS.', BODY))
story.append(PageBreak())

# ══ SECTION 10 — TROUBLESHOOTING ════════════════════════════════
story.append(Paragraph('SECTION 10', SECNUM))
story.append(Paragraph('Troubleshooting Guide', H1))
story.append(hr())

issues = [
    ('Voice bot stops working after 2-3 queries',
     [
         'Cause: Ghost onend events from un-cleaned SpeechRecognition instances stack up in memory.',
         'Fixed by: _killRecog() which nulls all callbacks before abort().',
         'If it still happens: refresh the page to reset all SR instances.',
         'Check: Open DevTools > Memory tab > take heap snapshot to confirm no SR leak.',
     ]),
    ('Microphone blocked / not-allowed error',
     [
         'Cause: Browser denied microphone permission.',
         'Fix: Click the lock icon in Chrome address bar > Allow microphone.',
         'Also ensure the page is served over HTTPS or localhost.',
         'Fix: Go to Chrome Settings > Privacy > Site Settings > Microphone > Allow.',
     ]),
    ('Voice bot shows Listening but no transcript appears',
     [
         'Cause: en-IN locale not supported on this system.',
         'Fix: The system auto-falls back to en-US on language-not-supported error.',
         'Alternative: Change srLang to "en-US" manually in chatbot.html line ~690.',
         'Also check: Is there background noise? SpeechRecognition needs a clear audio signal.',
     ]),
    ('TTS not speaking / AI is silent',
     [
         'Cause 1: No voices loaded yet. Voices load asynchronously on page load.',
         'Fix: Click the Voice On button, wait 2 seconds, then try again.',
         'Cause 2: speechSynthesis is paused (Chrome bug after tab switch).',
         'Fix: Call speechSynthesis.resume() in browser console.',
         'Cause 3: ttsOn is false and voiceActive is false (not in voice session).',
         'Fix: Either toggle Voice On button or use the mic button to enter voice mode.',
     ]),
    ('Browser tab crashes during voice session',
     [
         'Cause: Multiple SpeechRecognition instances running simultaneously (memory leak).',
         'Fixed by: _killRecog() always destroying old instance before new SR() call.',
         'Fixed by: TTS queue capped at 8 items to prevent memory spiral.',
         'Fixed by: AbortController cancels stale SSE streams before new query.',
     ]),
    ('AI ignores document content and gives general answers',
     [
         'Cause: Document not indexed yet (embedding still in processing state).',
         'Check: Go to document list > check indexing status badge.',
         'Fix: Wait for indexing to complete (background thread, usually under 30 seconds).',
         'Cause 2: Query is too different from document content for RAG to retrieve relevant chunks.',
         'Fix: Ask a more specific question using keywords from the document.',
     ]),
    ('Responses are very slow',
     [
         'Cause: Groq API rate limit or network latency.',
         'Check: View Django server console for API error messages.',
         'Fix: Groq free tier has rate limits — upgrade plan or add retry logic.',
         'Also: Large documents with many chunks take longer to search. Reduce n_results in config.py.',
     ]),
    ('Source chips not appearing below answers',
     [
         'Cause: Query answered from general knowledge (no document chunks retrieved).',
         'Expected behaviour: General knowledge badge shown instead.',
         'If document was uploaded: Check is_indexed status in DocumentEmbedding model.',
         'Fix: Re-upload the document or trigger re-indexing via admin panel.',
     ]),
]

for title, bullets in issues:
    story.append(KeepTogether([
        Paragraph(title, H3),
        *[Paragraph(b, BUL) for b in bullets],
        Spacer(1, 0.2*cm),
    ]))

# ── FOOTER ──────────────────────────────────────────────────────
story.append(hr_light())
story.append(Paragraph(
    'DocuVault AI Assistant Technical Documentation  |  Version 2.0  |  March 2024  |  Confidential',
    FOOT))

# ── RENDER ──────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    'docuvault_chatbot_voice_tech_doc.pdf',
    pagesize=A4,
    leftMargin=1.8*cm, rightMargin=1.8*cm,
    topMargin=1.8*cm,  bottomMargin=1.8*cm,
    title='DocuVault AI Assistant Technical Documentation',
    author='DocuVault',
    subject='Chatbot and Voice Bot Technical Reference',
)
doc.build(story)
print('docuvault_chatbot_voice_tech_doc.pdf created successfully')
