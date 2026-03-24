const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TableOfContents
} = require("docx");

// ── helpers ──────────────────────────────────────────────────────────────────
const BLUE = "1F4E79";
const LIGHT_BLUE = "D6E4F0";
const MED_BLUE = "2E75B6";
const WHITE = "FFFFFF";
const FULL_W = 9360; // US Letter 1" margins

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellPad = { top: 80, bottom: 80, left: 120, right: 120 };

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: BLUE, type: ShadingType.CLEAR },
    margins: cellPad,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: WHITE, font: "Arial", size: 22 })] })],
  });
}
function cell(text, width, opts = {}) {
  const runs = [];
  if (opts.bold) {
    runs.push(new TextRun({ text, bold: true, font: "Arial", size: 21 }));
  } else {
    runs.push(new TextRun({ text, font: "Arial", size: 21 }));
  }
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shaded ? { fill: "F2F7FB", type: ShadingType.CLEAR } : undefined,
    margins: cellPad,
    children: [new Paragraph({ children: runs })],
  });
}

function makeTable(headers, rows, colWidths) {
  const tw = colWidths.reduce((a, b) => a + b, 0);
  const tRows = [
    new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
    ...rows.map((r, ri) =>
      new TableRow({
        children: r.map((c, ci) => cell(c, colWidths[ci], { bold: ci === 0, shaded: ri % 2 === 0 })),
      })
    ),
  ];
  return new Table({ width: { size: tw, type: WidthType.DXA }, columnWidths: colWidths, rows: tRows });
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 200 }, children: [new TextRun({ text, bold: true, font: "Arial", size: 32, color: BLUE })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 160 }, children: [new TextRun({ text, bold: true, font: "Arial", size: 28, color: MED_BLUE })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 120 }, children: [new TextRun({ text, bold: true, font: "Arial", size: 24, color: MED_BLUE })] });
}
function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after || 160 },
    children: [new TextRun({ text, font: "Arial", size: 22, bold: opts.bold, italics: opts.italic, color: opts.color })],
  });
}
function bullet(text, ref = "bullets", level = 0) {
  return new Paragraph({
    numbering: { reference: ref, level },
    children: [new TextRun({ text, font: "Arial", size: 22 })],
  });
}
function spacer() {
  return new Paragraph({ spacing: { after: 80 }, children: [] });
}

// ── CONTENT ──────────────────────────────────────────────────────────────────
const children = [];

// ── COVER PAGE ───
children.push(
  spacer(), spacer(), spacer(), spacer(), spacer(), spacer(),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "DocuVault", font: "Arial", size: 56, bold: true, color: BLUE })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [new TextRun({ text: "Knowledge Management AI Platform", font: "Arial", size: 28, color: MED_BLUE })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [new TextRun({ text: "Client Reference Guide", font: "Arial", size: 26, color: "555555" })] }),
  spacer(),
  makeTable(["", ""], [
    ["Version", "DocuVault v3.0"],
    ["Date", "March 24, 2026"],
    ["Prepared by", "Renata AI"],
    ["Classification", "Confidential \u2013 Client Use Only"],
  ], [2400, 6960]),
  new Paragraph({ children: [new PageBreak()] })
);

// ── TABLE OF CONTENTS ───
children.push(
  h1("Contents"),
  new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 1. SYSTEM OVERVIEW
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("1.  System Overview"),
  para("DocuVault is Renata AI\u2019s Knowledge Management Platform. It gives your organisation one place to store, organise, and query all your documents \u2014 using plain English, not search keywords."),
  para("At its core is an AI assistant that reads your documents and answers questions instantly. No more hunting through folders or opening file after file."),
  h3("What you can do with DocuVault"),
  bullet("Upload and organise your documents in one secure place."),
  bullet("Control who can see each document \u2014 from fully public to private or role-restricted."),
  bullet("Ask the AI assistant questions in plain English and get answers drawn from your own documents."),
  bullet("Interact with the AI using voice \u2014 ask questions by speaking and hear answers read aloud."),
  bullet("Collaborate with your team through comments, shared links, and notifications."),
  bullet("Track every action with a complete audit trail."),
  bullet("Manage users and roles with fine-grained permission levels."),
  spacer(),
  makeTable(["Item", "Details"], [
    ["Platform", "DocuVault v3.0 \u2014 web-based (browser) + optional desktop agent"],
    ["Supported Files", "PDF, Word, text files, images, and more"],
    ["Max File Size", "100 MB per upload"],
    ["AI Knowledge Modes", "Hybrid (default)  \u00b7  Strict (documents only)  \u00b7  Indicated  \u00b7  GK"],
    ["Access Control", "Public  \u00b7  Private  \u00b7  Role-Based  \u00b7  Custom (per user)"],
    ["Web Access", "Any modern web browser on desktop, tablet, or mobile"],
    ["Desktop Access", "Optional background desktop agent \u2014 auto-connects files, runs in system tray"],
    ["Voice Assistant", "Built-in voice bot \u2014 speak questions, hear AI answers, hands-free operation"],
    ["Internet Required", "No \u2014 fully offline after one-time model download. No API key, no cloud dependency."],
  ], [2400, 6960]),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 2. KEY FEATURES
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("2.  Key Features"),

  // 2.1 Document Management
  h2("2.1  Document Management"),
  para("Everything you need to manage documents throughout their full lifecycle."),
  makeTable(["Feature", "What it does"], [
    ["Upload", "Add documents from your computer. Supported types include PDF, Word, images, and more."],
    ["Bulk Upload", "Upload multiple documents or entire folders at once. Files are processed in the background and prepared for indexing."],
    ["Access Control", "Choose who can see each document: Public, Private, Role-Based, or shared with specific people."],
    ["Version History", "Every time a document is edited, the previous version is saved. You can view or restore any past version."],
    ["Document Locking", "Lock a document while editing so no one else can make changes at the same time."],
    ["Categories & Tags", "Organise documents into categories (with sub-categories) and tag them for flexible grouping."],
    ["Metadata", "Track view count, download count, file size, and upload date automatically."],
    ["Soft Delete", "Deleted documents can be recovered by an administrator before permanent removal."],
  ], [2400, 6960]),
  spacer(),

  // 2.2 AI Knowledge Assistant
  h2("2.2  AI Knowledge Assistant"),
  para("The AI assistant lets you ask questions about your documents in plain English. It reads through all indexed documents, finds the most relevant parts, and writes a clear answer."),
  makeTable(["Feature", "What it does"], [
    ["Ask in Plain English", "Type a question naturally \u2014 the AI understands context, not just keywords."],
    ["Answers from Your Docs", "The AI draws from documents stored in DocuVault, so answers are grounded in your data."],
    ["Follow-up Questions", "Ask follow-up questions in the same conversation. The AI remembers context."],
    ["AI Knowledge Modes", "GK: Built-in knowledge only. Hybrid: Documents first, general knowledge as fallback. Strict: Documents only. Indicated: Both sources, clearly labelled."],
    ["Permission-Aware", "The AI only uses documents the logged-in user is allowed to access."],
    ["Source Transparency", "Each answer shows which documents and pages were used, so you can verify the information."],
    ["Streaming Responses", "Answers stream in real-time via Server-Sent Events, so you see the response as the AI writes it."],
  ], [2400, 6960]),
  spacer(),

  // 2.3 Users, Roles & Access Control
  h2("2.3  Users, Roles & Access Control"),
  makeTable(["User Type", "What they can do"], [
    ["Guest", "View documents that are set to Public only. Cannot upload or edit."],
    ["Regular User", "Upload and manage their own documents. Access documents based on their role level. Comment and collaborate."],
    ["Admin", "Full access to all documents, all users, and all system settings."],
  ], [2400, 6960]),
  para("Administrators can create custom roles (e.g. \u201CTeam Lead\u201D, \u201CDepartment Head\u201D) and assign a numeric level to each. Documents set to Role-Based access are visible only to users whose role level meets or exceeds the required threshold."),
  spacer(),

  // 2.4 Collaboration & Sharing
  h2("2.4  Collaboration & Sharing"),
  makeTable(["Feature", "What it does"], [
    ["Comments", "Add comments to any document. Replies are threaded for easy reading."],
    ["Shared Links", "Generate a link to share a document. Optionally add a password, set an expiry date, or limit how many times it can be opened."],
    ["Direct Sharing", "Share a document directly with specific registered users."],
    ["Notifications", "The system automatically alerts you when a document is shared with you, updated, or commented on."],
    ["Favourites", "Bookmark documents you use often for quick access from your sidebar."],
  ], [2400, 6960]),
  spacer(),

  // 2.5 Search & Organisation
  h2("2.5  Search & Organisation"),
  makeTable(["Feature", "What it does"], [
    ["Search Bar", "Search by title, description, or content. Results rank the most relevant documents first."],
    ["Filters", "Narrow results by owner, date, access level, category, tags, or file type."],
    ["Sorting", "Sort by title, upload date, last updated, view count, or file size."],
    ["Categories", "Organise documents into a tree of categories. Each category can have a colour and icon."],
    ["Tags", "Add one or more tags to a document. Search and filter by tag across all categories."],
  ], [2400, 6960]),
  spacer(),

  // 2.6 Audit Trail & Notifications
  h2("2.6  Audit Trail & Notifications"),
  para("Every action in DocuVault is automatically recorded. The activity log shows who did what, and when \u2014 making it easy to track changes for compliance and accountability."),
  makeTable(["Recorded Action", "When it appears in the log"], [
    ["Upload / Create", "A new document is added to the system."],
    ["View / Download", "A user opens or downloads a document."],
    ["Edit / Update", "A document or its details are changed."],
    ["Delete", "A document is removed (soft-deleted)."],
    ["Share", "A document is shared via link or direct user share."],
    ["Comment", "A comment is added to a document."],
    ["Permission Changed", "A document\u2019s access level or user role is updated."],
  ], [2400, 6960]),
  spacer(),

  // ══════════════════════════════════════════════════════════════════════════
  // 2.7 Voice AI Integration (EXPANDED)
  // ══════════════════════════════════════════════════════════════════════════
  h2("2.7  Voice AI Assistant"),
  para("DocuVault includes a fully integrated Voice AI Assistant that allows users to interact with the AI knowledge system using speech. Instead of typing questions, users can speak naturally and receive spoken answers \u2014 creating a seamless, hands-free experience."),
  spacer(),

  h3("Core Voice Features"),
  makeTable(["Feature", "What it does"], [
    ["Speech-to-Text Input", "Speak your question naturally. The system converts speech to text in real-time using the browser\u2019s Web Speech API. You see a live transcript as you speak."],
    ["Text-to-Speech Output", "The AI reads its answer aloud using high-quality voice synthesis. Responses are broken into natural sentences for smooth playback."],
    ["Continuous Conversation", "After the AI finishes speaking, it automatically resumes listening for your next question \u2014 enabling multi-turn voice conversations without pressing any buttons."],
    ["Auto-Send on Silence", "When you pause speaking for 2 seconds, the system automatically sends your question to the AI. A \u201CSend Now\u201D button is also available for manual control."],
    ["Voice Toggle", "A dedicated Voice On/Off button in the toolbar lets you enable or disable text-to-speech at any time without interrupting your session."],
    ["Fallback Transcription", "If the browser does not support speech recognition, the system falls back to server-side transcription using Whisper AI (runs locally, no cloud)."],
  ], [2800, 6560]),
  spacer(),

  h3("Voice Interface Modes"),
  para("The Voice AI Assistant provides two interface modes that users can choose based on their preference:"),
  spacer(),

  para("Full-Screen Voice Modal", { bold: true }),
  bullet("An immersive, full-screen voice conversation interface."),
  bullet("Animated visual orb that changes colour to indicate state: purple (ready), red (listening), amber (processing), green (speaking)."),
  bullet("Wave animations provide visual feedback while the AI is speaking."),
  bullet("Live transcript display shows what you\u2019re saying in real-time."),
  bullet("Response preview area shows the AI\u2019s answer as it streams in."),
  bullet("Close with the \u00D7 button or press Escape at any time."),
  spacer(),

  para("Inline Voice Bar (Compact Mode)", { bold: true }),
  bullet("A compact voice bar appears above the chat input box."),
  bullet("Colour-coded status dot shows current state at a glance."),
  bullet("Real-time transcription displayed inline (truncated to keep the bar compact)."),
  bullet("Stop and Send Now buttons for manual control."),
  bullet("Minimal screen footprint \u2014 ideal for users who want voice input without leaving the chat view."),
  spacer(),

  h3("Voice Technology Stack"),
  makeTable(["Component", "Technology", "Details"], [
    ["Speech Recognition (Primary)", "Web Speech API", "Native browser API. Supports continuous listening, interim results. Language: en-AU with en-US fallback."],
    ["Speech Recognition (Fallback)", "faster-whisper / OpenAI Whisper", "Server-side transcription using the \u201Ctiny\u201D model. Runs locally on CPU with int8 quantization. No cloud dependency."],
    ["Voice Synthesis", "Web Speech Synthesis API", "Native browser TTS. Priority voices: Microsoft Heera/Ravi (Indian English). Configurable rate and pitch. Queue-based playback."],
  ], [2200, 2400, 4760]),
  spacer(),

  h3("How the Voice Assistant Works"),
  bullet("Step 1 \u2014 Activate: Click the microphone button in the chat interface. The browser requests microphone permission (first time only)."),
  bullet("Step 2 \u2014 Speak: Ask your question naturally. A live transcript appears as you speak."),
  bullet("Step 3 \u2014 Auto-Send: After 2 seconds of silence, the question is automatically sent to the AI (or click Send Now)."),
  bullet("Step 4 \u2014 AI Responds: The AI answer streams in via Server-Sent Events and is spoken aloud through text-to-speech."),
  bullet("Step 5 \u2014 Continue: Once the AI finishes speaking, the system resumes listening for your next question \u2014 creating a natural voice conversation loop."),
  spacer(),

  h3("Voice AI Use Cases"),
  makeTable(["Scenario", "How Voice AI Helps"], [
    ["Executives & Decision Makers", "Ask questions about reports, financials, and policies without typing. Get instant spoken summaries while reviewing other work."],
    ["Field Teams & Site Workers", "Hands-free access to technical manuals, safety documents, and procedures \u2014 especially useful when hands are occupied."],
    ["Accessibility", "Enables users with mobility limitations or visual impairments to interact with the full document knowledge base using speech."],
    ["Meeting Rooms & Presentations", "Query the AI assistant live during meetings. Ask questions aloud and have answers read to the room."],
    ["Rapid Research", "Cycle through multiple questions faster by speaking than typing, ideal for research sessions across many documents."],
  ], [2800, 6560]),
  spacer(),

  para("The Voice AI Assistant works alongside all existing features \u2014 documents, permissions, AI knowledge modes, and audit logging apply exactly the same way whether you type or speak.", { italic: true }),
  new Paragraph({ children: [new PageBreak()] }),

  // ══════════════════════════════════════════════════════════════════════════
  // 2.8 Desktop Agent
  // ══════════════════════════════════════════════════════════════════════════
  h2("2.8  Desktop Agent"),
  para("For teams who work heavily with local files, DocuVault offers an optional lightweight Desktop Agent that runs in the background on your computer. It bridges the gap between your local file system and the DocuVault platform \u2014 so documents are synced, indexed, and searchable without any manual effort."),
  makeTable(["Feature", "What it does"], [
    ["System Tray App", "The agent sits quietly in your Windows/macOS system tray. One click opens DocuVault \u2014 no browser URL to remember."],
    ["Automatic File Watching", "Select folders on your computer to watch. Any file saved there is automatically detected and uploaded to DocuVault."],
    ["Background Sync", "Files are uploaded and indexed in the background without interrupting your work. Rapid saves are debounced to avoid duplicates."],
    ["Auto-Start on Boot", "The agent starts with your computer and reconnects to the DocuVault server automatically \u2014 no manual login each day."],
    ["Right-Click Upload", "Right-click any file in Windows Explorer or macOS Finder and choose \u201CSend to DocuVault\u201D directly."],
    ["Offline Queue", "If the server is temporarily unreachable, the agent queues pending files and syncs them once the connection is restored."],
    ["Version Tracking", "When a previously synced file is modified, the agent creates a new version in DocuVault rather than a duplicate document."],
    ["Desktop Notifications", "Native desktop pop-up notifications for completed uploads, indexing status, and shared documents."],
    ["Setup Wizard", "A guided 3-step wizard handles connection, folder selection, and auto-start configuration \u2014 no technical knowledge needed."],
    ["Web Management Panel", "Admins can monitor agent status, view recent syncs, and manage configuration from the web dashboard at /workspace/agent/."],
  ], [2800, 6560]),
  para("The Desktop Agent is ideal for power users who regularly save documents locally (reports, drawings, scanned files, spreadsheets) and want them available in DocuVault automatically. The web platform remains fully functional for all users \u2014 the agent is an optional add-on. See Section 6.5 for full technical details, deployment options, and API documentation.", { italic: true }),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 3. SYSTEM USAGE & NAVIGATION
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("3.  System Usage & Navigation"),
  para("The table below shows how to navigate to each feature. All paths are relative to your system\u2019s base URL (e.g. https://yourdomain.com)."),
  makeTable(["URL Path", "How to access"], [
    ["/register/", "Open the system in your browser and click Register. Enter your name, email, and password."],
    ["/login/", "Enter your username and password and click Sign In."],
    ["/dashboard/", "Your home screen after login. Shows recent documents, notifications, and quick links."],
    ["/documents/", "The full document library. Use the search bar and filter panel to narrow results."],
    ["/documents/create/", "Click + New Document. Select a file, fill in the details, set access level, and click Save."],
    ["/documents/<id>/", "Click any document title to open it \u2014 preview, download, comment, version history, and share."],
    ["/documents/<id>/edit/", "Open a document then click Edit. Save changes \u2014 the system automatically creates a new version."],
    ["/documents/<id>/index/", "Open a document then click Index for AI. The system reads and indexes the content for the AI assistant."],
    ["/documents/bulk-index/", "Admins only. From the document list, go to Actions \u2192 Bulk Index to index all unprocessed documents."],
    ["/chatbot/", "Click AI Assistant in the sidebar. Type your question, press Enter, or click the microphone for voice."],
    ["/chatbot/voice/transcribe/", "Server-side voice transcription endpoint (used automatically as fallback when Web Speech API is unavailable)."],
    ["/search/", "Use the search bar in the top navigation. Add filters for date, owner, category, tags, and access level."],
    ["/categories/", "Navigate to Organise \u2192 Categories to create, nest, and colour-code categories."],
    ["/favorites/", "Click the star icon on any document. Access bookmarks via Favourites in the sidebar."],
    ["/notifications/", "Click the bell icon in the top bar to see all notifications."],
    ["/activity/", "Go to Account \u2192 Activity Log for a complete history of all actions."],
    ["/admin/users/", "Admins only. Go to Admin \u2192 Users to view all accounts and update role assignments."],
    ["/admin/roles/", "Admins only. Go to Admin \u2192 Roles to create, edit, or remove custom roles."],
    ["/profile/edit/", "Click your avatar (top right) \u2192 Edit Profile to update your details."],
    ["/workspace/agent/", "Desktop Agent management panel \u2014 view status, configure folders, download the agent, and monitor syncs."],
  ], [3000, 6360]),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 4. SYSTEM ARCHITECTURE
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("4.  System Architecture"),
  para("This section provides a high-level overview of the DocuVault system architecture, including how documents are stored, indexed, and processed by the AI engine. All components operate on your local infrastructure."),

  h2("4.1  System Structure"),
  para("DocuVault has three main layers that work together:"),
  makeTable(["Layer", "What it is", "What it does for you"], [
    ["Your Browser", "The web interface you open on any device.", "Where you upload, search, chat with AI, use voice, and manage settings."],
    ["DocuVault Platform", "The server application in the background.", "Handles login, stores documents securely, controls access, and connects you to AI."],
    ["AI & Storage", "The AI engine and databases.", "Reads and indexes documents, answers questions, and stores all data."],
  ], [2000, 3200, 4160]),
  spacer(),
  para("System Flow: Your Browser (Any device) \u2192 DocuVault Platform (Application) \u2192 Document Storage (Local files) \u2192 AI Search Engine (Local index) \u2192 Ollama (Local AI running Qwen 2.5) \u2014 No Internet Required.", { italic: true }),
  spacer(),

  h2("4.2  Document Indexing Process"),
  para("Before the AI can answer questions about a document, it must be \u201Cindexed\u201D \u2014 this means the AI reads it and saves a summary in a way it can search very quickly."),
  h3("Steps in plain English"),
  bullet("Step 1 \u2014 Upload: You select a file and upload it. DocuVault saves it securely."),
  bullet("Step 2 \u2014 Validate: The system checks the file size (must be under 100 MB) and file type."),
  bullet("Step 3 \u2014 AI Reads It: The platform reads the document \u2014 extracting all text, tables, and if needed, running text recognition on scanned pages."),
  bullet("Step 4 \u2014 Save to Index: The content is broken into sections and saved in the AI search index."),
  bullet("Step 5 \u2014 Ready: The document is now available to the AI assistant for any permitted user."),
  para("How to index a document: Open any document, then click Index for AI. The status will update to \u201CIndexed\u201D once complete. Admins can also index all documents at once using the Bulk Index option."),
  spacer(),

  h2("4.3  AI Query Processing"),
  para("When you type or speak a question in the AI assistant, DocuVault goes through these steps to find and write the answer:"),
  bullet("Step 1 \u2014 You ask a question: Type or speak in plain English, e.g. \u201CWhat are the leave policy rules?\u201D"),
  bullet("Step 2 \u2014 Platform searches your documents: DocuVault searches all indexed documents to find the most relevant sections."),
  bullet("Step 3 \u2014 AI reads the relevant parts: The AI reads the top matching sections. It only uses documents you have permission to access."),
  bullet("Step 4 \u2014 AI writes the answer: Using the content it found, the AI writes a clear, direct answer."),
  bullet("Step 5 \u2014 You receive the answer: The answer appears in the chat (and is spoken aloud if voice is active) with source documents and page numbers."),
  spacer(),

  h3("AI-Based vs Index-Based Processing"),
  makeTable(["Type", "What it does", "Best used for"], [
    ["AI-Based", "The AI generates responses using language understanding and reasoning.", "Summaries, explanations, conversational queries."],
    ["Index-Based", "The system retrieves relevant sections from a pre-built document index.", "Accurate, document-grounded answers."],
  ], [2000, 4160, 3200]),
  para("DocuVault uses Retrieval-Augmented Generation (RAG): First, the system retrieves relevant document sections (Index-Based), then the AI reads and generates the answer (AI-Based). This ensures responses are accurate, fast, based on your documents, and fully traceable."),
  spacer(),

  h3("AI Knowledge Modes"),
  makeTable(["Mode", "How it behaves", "Best for"], [
    ["GK (General Knowledge)", "Uses only built-in AI knowledge. Does not reference any documents.", "General queries, brainstorming."],
    ["Hybrid (default)", "Uses your documents first and fills gaps with general knowledge.", "Everyday use \u2014 balanced accuracy and flexibility."],
    ["Strict", "Only answers from your documents. Clearly states if no answer is found.", "Compliance, legal, sensitive environments."],
    ["Indicated", "Uses both sources and clearly labels which parts come from documents vs general knowledge.", "Research, auditing, traceability."],
  ], [2200, 4160, 3000]),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 5. TECHNICAL SPECIFICATIONS
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("5.  Technical Specifications"),
  para("This section outlines the core technical components, configurations, and infrastructure that power the DocuVault platform."),

  h2("5.1  Technology Stack"),
  makeTable(["Category", "Technology"], [
    ["Web Framework", "Django 5.x (Python 3.10+)"],
    ["Database", "SQLite (development) / PostgreSQL (production)"],
    ["AI Language Model", "Ollama (Local Inference) \u2014 Qwen 2.5 or compatible model. Downloaded once, runs fully offline."],
    ["AI Search Engine", "ChromaDB vector database \u2014 stored locally, no cloud dependency"],
    ["Embedding Model", "all-MiniLM-L6-v2 \u2014 runs on-device via sentence-transformers"],
    ["Document Reading", "pdfplumber, PyMuPDF, Camelot (tables), Tesseract (OCR for scanned pages)"],
    ["AI Framework", "LangChain + Ollama backend, HuggingFace (local), PyTorch"],
    ["Voice Recognition", "Web Speech API (browser-native) + faster-whisper / Whisper (server-side fallback)"],
    ["Voice Synthesis", "Web Speech Synthesis API (browser-native) with smart sentence chunking"],
    ["Desktop Agent", "Python + watchdog (file monitoring) + pystray (system tray) + PyInstaller (EXE packaging)"],
    ["Max File Upload", "100 MB per file"],
    ["Search Method", "Hybrid \u2014 70% semantic similarity + 30% keyword matching"],
    ["Internet Required", "No \u2014 entire stack runs offline on local hardware after setup"],
  ], [2400, 6960]),
  spacer(),

  h2("5.2  AI Configuration"),
  makeTable(["Setting", "Value"], [
    ["LLM runtime", "Ollama \u2014 local model server, starts automatically with DocuVault"],
    ["Default model", "Qwen 2.5-7B (downloaded once, ~4.7 GB, then fully offline)"],
    ["API key required", "None \u2014 no cloud API key needed"],
    ["Document chunk size", "512 characters (256 in lightweight mode)"],
    ["Overlap between chunks", "100 characters"],
    ["Results per query", "8 chunks (6 in lightweight mode)"],
    ["Conversation memory", "Up to 8 turns per session"],
    ["Max response length", "512 tokens (~380 words)"],
    ["Response consistency", "Low variability \u2014 temperature 0.2 for reliable, repeatable answers"],
    ["Voice transcription model", "Whisper \u201Ctiny\u201D (CPU, int8 quantization) \u2014 ~75 MB, runs locally"],
    ["Internet during inference", "Not required \u2014 model runs entirely on local CPU/GPU"],
  ], [3200, 6160]),
  spacer(),

  h2("5.3  User & Permission Model"),
  makeTable(["Access Level", "Who can see the document"], [
    ["Public", "Everyone, including guests who are not logged in."],
    ["Private", "The document owner and admins only."],
    ["Role-Based", "Users whose role level is equal to or higher than the required level set by the owner."],
    ["Custom", "Only specific users selected by the document owner, plus admins."],
  ], [2400, 6960]),
  spacer(),

  h2("5.4  Key Database Records"),
  makeTable(["Record Type", "What it stores"], [
    ["Document", "The file, title, access level, category, tags, and owner."],
    ["Document Version", "A snapshot of the document every time it is edited."],
    ["Chat Session", "A conversation thread between a user and the AI assistant."],
    ["Chat Message", "Each individual question and AI answer, with source references."],
    ["Activity Log", "An immutable record of every action in the system."],
    ["Notification", "Alerts sent to users for shares, comments, and updates."],
    ["Shared Link", "A temporary link with optional password, expiry, and access count."],
    ["Agent Token", "Authentication token for the Desktop Agent, with last-used tracking and active status."],
  ], [2800, 6560]),
  spacer(),

  h2("5.5  Data Backup & Recovery"),
  para("DocuVault stores all documents, AI indexes, and system databases on the local server. To protect against hardware failure or accidental data loss, it is recommended to configure regular backups."),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 6. EXTENSIONS & INTEGRATIONS
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("6.  Extensions & Integrations"),
  para("DocuVault is designed to scale with your organisation. The features described in this section are available as extensions or integrations that can be configured and enabled on top of the core platform."),

  // 6.1 AMC
  h2("6.1  Annual Maintenance Contract (AMC)"),
  para("An Annual Maintenance Contract (AMC) can be provided to keep DocuVault updated, secure, and running smoothly over time."),
  h3("What the AMC covers"),
  bullet("AI model upgrades \u2014 The system can be updated to newer AI models that provide better understanding, improved responses, and more accurate answers."),
  bullet("Performance improvements \u2014 Enhancements to document search, response speed, and overall system efficiency."),
  bullet("Security updates and monitoring \u2014 Regular updates to maintain system security and stability."),
  bullet("UI improvements and new features \u2014 Periodic updates to improve usability and add useful capabilities."),
  spacer(),
  h3("Important clarification"),
  para("DocuVault does not train the AI model on your documents. Instead, it uses an approach called Retrieval-Augmented Generation (RAG)."),
  para("In simple terms, three components work together:"),
  bullet("AI Model (running through Ollama) \u2014 The AI engine that understands questions and generates answers in natural language."),
  bullet("Embedding Model \u2014 Converts document text into a searchable format so the system can quickly find the most relevant parts."),
  bullet("RAG Process \u2014 When a user asks a question, the system retrieves the most relevant document sections, and the AI model reads those sections and generates a response."),
  spacer(),
  para("Because of this design:"),
  bullet("AI model upgrades do not require retraining on your documents."),
  bullet("Your existing indexed documents will continue to work normally after an upgrade."),
  bullet("In simple terms, the documents stay the same, but the AI engine that interprets them becomes more advanced."),
  spacer(),
  h3("When re-indexing may be needed"),
  para("Re-indexing is only required if the embedding model used for document search changes. If that happens, the system simply regenerates the document embeddings automatically. The original documents do not need to be uploaded again, and this process can be handled as part of the AMC."),
  spacer(),

  // 6.2 Email System Integration
  h2("6.2  Email System Integration"),
  para("DocuVault can integrate with your organisation\u2019s email system. Emails and their attachments are ingested and indexed so they become searchable through the AI assistant."),
  h3("Supported email systems"),
  bullet("Microsoft Outlook / Exchange"),
  bullet("Microsoft 365"),
  bullet("Gmail"),
  bullet("IMAP servers"),
  bullet("On-premise enterprise mail servers"),
  spacer(),
  makeTable(["Email Content", "What is indexed"], [
    ["Email body", "The full text of the email message."],
    ["Attachments", "PDF, Word, Excel, and PowerPoint files attached to emails."],
    ["Metadata", "Sender, receiver, subject line, and timestamp."],
  ], [2800, 6560]),
  para("Role-based access ensures that emails are only retrievable by users who are authorised to see them (e.g. HR emails visible to HR only, Finance emails to Finance only)."),
  spacer(),

  // 6.3 LAN Drive Sync
  h2("6.3  LAN Drive Sync (Google Drive-Style)"),
  para("Instead of manually uploading files through the web interface, users can save documents into a synchronised folder on their computer. A background sync agent watches the folder and automatically sends new or updated files to DocuVault."),
  h3("Features"),
  bullet("Automatic document synchronisation \u2014 no manual uploads required."),
  bullet("Version tracking \u2014 every save creates a new version with timestamp and user."),
  bullet("Rollback \u2014 restore any previous version from DocuVault."),
  bullet("Instant AI indexing \u2014 new documents are indexed automatically as they sync."),
  bullet("Enterprise-ready \u2014 supports multiple PCs on the same LAN."),
  spacer(),
  makeTable(["Option", "Description"], [
    ["Desktop sync agent (recommended)", "A lightweight background app installed on each user\u2019s PC."],
    ["Network shared drive monitoring", "Monitors a shared network folder without any client install."],
    ["Drive-style desktop client", "A full Google Drive-like interface with sync status indicators."],
  ], [3200, 6160]),
  spacer(),

  // 6.4 Auto-Indexing on Upload
  h2("6.4  Auto-Indexing on Upload"),
  para("By default, documents must be manually triggered for AI indexing after upload. The system can be configured to index documents automatically the moment they are uploaded, so they are immediately available to the AI assistant."),
  h3("How indexing works (not AI training)"),
  para("A common question from clients is whether uploading documents \u201Ctrains\u201D the AI. The answer is no. DocuVault uses indexing, not training."),
  makeTable(["", "AI Training", "DocuVault Indexing"], [
    ["What it is", "Modifying the AI model\u2019s internal weights.", "Reading and storing document content in a searchable format."],
    ["Time", "Hours to days.", "Seconds to minutes per document."],
    ["Effect", "Permanently changes the AI model.", "Adds document to the search index only."],
    ["Required?", "Never required in DocuVault.", "Required once per document (or on re-upload)."],
  ], [1800, 3780, 3780]),
  para("Auto-indexing can be enabled by your system administrator in the platform configuration. Once enabled, every document uploaded will be automatically indexed in the background without any action required from the user."),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 6.5 Desktop Agent (EXPANDED)
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h2("6.5  Desktop Agent \u2014 Web to Desktop"),
  para("By default, DocuVault runs entirely in a web browser \u2014 no installation needed. However, for teams who work heavily with local files, a fully-featured Desktop Agent can be installed alongside the web platform. The agent runs silently in the background, watches your folders, and keeps everything synced to DocuVault automatically."),
  spacer(),

  h3("What the Desktop Agent Does"),
  makeTable(["Capability", "Description"], [
    ["System tray icon", "The agent sits in your Windows/macOS system tray. One click opens DocuVault instantly \u2014 no browser URL to remember."],
    ["Automatic file watching", "Select one or more folders on your computer. Any file saved there is automatically detected and synced to DocuVault."],
    ["Background sync", "Files are uploaded and indexed in the background without interrupting your work."],
    ["Auto-connect on startup", "The agent starts with your computer and reconnects to the DocuVault server automatically \u2014 no manual login each day."],
    ["Local file shortcuts", "Right-click any file in Windows Explorer / macOS Finder and choose \u201CSend to DocuVault\u201D directly."],
    ["Offline queue", "If the server is temporarily unreachable, the agent queues pending files and syncs them automatically once the connection is restored."],
    ["Notification alerts", "Desktop pop-up notifications for completed uploads, indexing status, shared documents, and AI query replies."],
    ["Session persistence", "Stay logged in across sessions \u2014 the agent maintains your authentication token securely."],
    ["Smart debounce", "Rapid file saves (e.g. auto-save in Word) are debounced \u2014 the agent waits for the file to stabilise before syncing, avoiding duplicate uploads."],
    ["File type filtering", "Only syncs file types you care about (PDF, Word, Excel, PowerPoint, text, CSV by default). Temporary and system files are automatically skipped."],
    ["Folder-based organisation", "Synced files can be automatically assigned to a specific DocuVault workspace folder, keeping your documents organised."],
    ["Version tracking", "When a previously synced file is modified and saved again, the agent creates a new version in DocuVault rather than a duplicate document."],
  ], [2800, 6560]),
  spacer(),

  h3("Setup Wizard"),
  para("The Desktop Agent includes a guided setup wizard that walks through configuration in three simple steps:"),
  makeTable(["Step", "What you do"], [
    ["Step 1 \u2014 Connect", "Enter your DocuVault server URL, username, and password. The wizard validates the connection before proceeding."],
    ["Step 2 \u2014 Choose Folders", "Browse and select one or more folders on your computer to watch. You can add or remove folders at any time."],
    ["Step 3 \u2014 Confirm & Start", "Review your settings and choose whether to start the agent automatically when your computer boots. Click Finish to begin syncing."],
  ], [2400, 6960]),
  spacer(),

  h3("Web vs Desktop \u2014 Side by Side"),
  makeTable(["Aspect", "Web Browser (Standard)", "Desktop Agent (Add-On)"], [
    ["Installation", "None \u2014 open any browser", "One-time lightweight install (~20 MB)"],
    ["File access", "Manual upload via browser", "Automatic \u2014 watches selected folders"],
    ["Startup", "Open browser and navigate to URL", "Starts with computer, always ready"],
    ["Notifications", "In-browser only", "Native desktop pop-ups"],
    ["Right-click upload", "Not available", "Right-click any file to send to DocuVault"],
    ["Offline handling", "Not available", "Queues files and syncs when back online"],
    ["Version control", "Manual re-upload", "Automatic \u2014 detects changes and creates new versions"],
    ["File filtering", "You choose each file", "Automatic \u2014 filters by extension, skips temp files"],
    ["Best for", "Occasional users, mobile, tablet", "Power users who work with many local files daily"],
  ], [1800, 3780, 3780]),
  spacer(),

  h3("How the Desktop Agent Connects"),
  para("The connection flow is fully automatic after initial setup:"),
  bullet("Step 1 \u2014 File saved on your PC in a watched folder."),
  bullet("Step 2 \u2014 Agent detects the change using real-time file system monitoring (watchdog)."),
  bullet("Step 3 \u2014 Agent debounces rapid saves (waits for file to stabilise, default 3 seconds)."),
  bullet("Step 4 \u2014 File is uploaded to DocuVault via the secure Agent API with token authentication."),
  bullet("Step 5 \u2014 If auto-indexing is enabled, the document is immediately indexed for AI search."),
  bullet("Step 6 \u2014 File is available everywhere \u2014 web browser, desktop, and AI assistant."),
  spacer(),

  h3("Agent API & Authentication"),
  para("The Desktop Agent communicates with DocuVault through a dedicated, secure API. This is separate from the web interface and designed specifically for automated file synchronisation."),
  makeTable(["Feature", "Details"], [
    ["Authentication", "Token-based. The agent authenticates once with username/password and receives a secure API token that is stored locally."],
    ["Heartbeat", "The agent sends a heartbeat every 60 seconds so the server knows it is online. The web dashboard shows agent status in real-time."],
    ["Upload API", "Supports multipart file uploads with metadata (filename, category, workspace folder, change notes)."],
    ["Deduplication", "Files are identified by their full path. Re-saving an existing file creates a new version instead of a duplicate document."],
    ["Token management", "Tokens can be revoked and regenerated from the web dashboard if needed (e.g. if a device is lost)."],
    ["Activity logging", "All agent actions (uploads, version updates) are recorded in the DocuVault audit trail with a \u201CDesktop Agent\u201D tag."],
  ], [2800, 6560]),
  spacer(),

  h3("Web Management Panel"),
  para("Administrators and users can manage the Desktop Agent directly from the DocuVault web interface at /workspace/agent/."),
  makeTable(["Panel Feature", "What it does"], [
    ["Agent Status", "Shows whether the agent is online (green) or offline, based on the last heartbeat."],
    ["Recent Syncs", "Displays the last 15 documents auto-synced by the agent, with timestamps and status."],
    ["Configuration Editor", "Edit agent settings directly from the browser \u2014 server URL, watched folders, extensions, sync intervals."],
    ["Start / Stop Agent", "Start or stop the agent process remotely if it is running on the same machine."],
    ["Download Agent", "Download the agent as a standalone EXE (Windows) or as a Python ZIP package for other platforms."],
    ["Build EXE", "Admins can trigger a fresh PyInstaller build of the agent directly from the web panel."],
    ["Build Logs", "View build output and logs for troubleshooting."],
  ], [2800, 6560]),
  spacer(),

  h3("Deployment & Configuration"),
  makeTable(["Setting", "Details"], [
    ["Supported OS", "Windows 10/11, macOS 12+, Ubuntu 20.04+"],
    ["Server connection", "Connects to DocuVault over LAN or internet (HTTPS)"],
    ["Authentication", "Uses the same username / password as the web platform"],
    ["Watched folders", "Configurable \u2014 multiple folders with individual extension filters and workspace mapping"],
    ["File types (default)", ".pdf, .docx, .xlsx, .pptx, .txt, .csv"],
    ["Debounce interval", "3 seconds (configurable) \u2014 prevents duplicate uploads from rapid saves"],
    ["Heartbeat interval", "60 seconds \u2014 keeps the server informed of agent status"],
    ["Retry on failure", "Up to 5 retries with automatic recovery"],
    ["Logging", "Logs to desktop_agent.log (max 10 MB, auto-rotated)"],
    ["Auto-start", "Can be added to Windows startup via registry or macOS login items"],
    ["Configuration file", "Stored in %APPDATA%\\DocuVaultAgent\\config.json (user-specific, not in Program Files)"],
    ["Distribution", "Installer provided by Renata AI \u2014 deployable via Group Policy (Windows) or MDM (macOS)"],
  ], [2800, 6560]),
  spacer(),

  h3("Who Should Use the Desktop Agent?"),
  para("The Desktop Agent is ideal for users who regularly save documents locally (reports, drawings, scanned files, spreadsheets) and want them available in DocuVault without any manual effort. The web platform remains fully functional for all users \u2014 the agent is an optional add-on for power users."),
  makeTable(["User Profile", "Why the Agent Helps"], [
    ["Finance teams", "Auto-sync invoices, reports, and statements as they are saved locally."],
    ["HR departments", "Employee documents, policies, and forms sync to DocuVault automatically."],
    ["Engineering teams", "Technical drawings, specifications, and manuals stay current without manual uploads."],
    ["Executives", "Reports from other tools are synced and immediately searchable via AI."],
    ["Field workers", "Scanned documents and photos sync from the field laptop to the central system."],
  ], [2800, 6560]),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 6.6 Offline Operation
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h2("6.6  Offline Operation \u2014 No Internet Required"),
  para("DocuVault is designed to run entirely on your local network or on a single machine with no internet connection required at any point during normal operation."),
  h3("What runs locally"),
  makeTable(["Component", "How it runs offline"], [
    ["AI Language Model (LLM)", "Ollama runs the model directly on your server CPU or GPU. Downloaded once during setup."],
    ["Embedding Model", "all-MiniLM-L6-v2 runs on-device via sentence-transformers and PyTorch. No external API needed."],
    ["Vector Database", "ChromaDB stores all document embeddings as local files on the server disk."],
    ["Document Storage", "All uploaded files are stored in the local file system under /media/."],
    ["Web Application", "Django serves the web interface on your local network. No internet required."],
    ["Database", "SQLite or PostgreSQL runs locally. All user data, roles, and activity logs stay on-site."],
    ["Desktop Agent", "Connects to the DocuVault server over LAN (HTTPS). Never calls any external service."],
    ["Voice AI", "Speech recognition and synthesis run in the browser. Server-side Whisper runs locally."],
  ], [2800, 6560]),
  spacer(),

  h3("Setup \u2014 one-time steps (internet needed once only)"),
  bullet("Step 1 \u2014 Install DocuVault: Install the platform on your server. This requires the internet to download the software package once."),
  bullet("Step 2 \u2014 Download the AI model: Run: ollama pull qwen2.5:7b (downloads ~4.7 GB). Done once \u2014 never again."),
  bullet("Step 3 \u2014 Download embedding model: The all-MiniLM-L6-v2 (~90 MB) is downloaded automatically on first run and cached locally."),
  bullet("Step 4 \u2014 Go fully offline: Once both models are cached, disconnect from the internet. DocuVault continues to operate with full AI functionality indefinitely."),
  spacer(),

  h3("Offline capability summary"),
  makeTable(["Feature", "Works Offline?", "Notes"], [
    ["Document upload & management", "Yes", "Files saved locally on server."],
    ["AI assistant (Q&A)", "Yes", "Ollama runs the model locally \u2014 no API call."],
    ["Document indexing", "Yes", "Embeddings generated on-device."],
    ["User login & access control", "Yes", "Authentication handled by local Django server."],
    ["Search & filters", "Yes", "ChromaDB vector search runs locally."],
    ["Voice assistant", "Yes", "Web Speech API runs in the browser. Whisper runs on local server."],
    ["Email integration", "Yes", "Connects to on-premise mail server on LAN."],
    ["Desktop Agent sync", "Yes", "Communicates with DocuVault server over LAN."],
    ["LLM model updates", "Internet once", "New model pulled via ollama pull, then offline again."],
    ["Software updates", "Internet once", "Update package downloaded, then offline again."],
  ], [2600, 1600, 5160]),
  spacer(),

  h3("Hardware recommendations for offline deployment"),
  makeTable(["Component", "Minimum", "Recommended"], [
    ["CPU", "4 cores (model runs on CPU)", "8\u201316 cores for faster AI responses"],
    ["RAM", "16 GB", "32 GB for smooth multi-user operation"],
    ["Storage", "80 GB free", "200 GB+ SSD for large document libraries"],
    ["GPU", "Not required (slower responses)", "NVIDIA GPU with 8\u201324 GB VRAM (e.g. RTX 3060/4090)"],
    ["OS", "Ubuntu 20.04+ / Windows Server", "Ubuntu 22.04 LTS (recommended)"],
    ["Network", "LAN only (no internet needed)", "1 Gbps LAN for fast file sync"],
    ["Estimated Users", "1\u20133 concurrent (15\u201330s responses)", "5\u201320 concurrent with fast responses"],
  ], [1800, 3780, 3780]),
  para("Your data stays on your premises \u2014 always. Because DocuVault runs entirely on your own hardware with no cloud dependency, your documents, queries, and AI responses are never transmitted to any external server.", { bold: true }),
  spacer(),

  // 6.7 External Document System Integration
  h2("6.7  External Document System Integration"),
  para("DocuVault can integrate with existing document management systems and cloud storage platforms, allowing organisations to unify knowledge without migrating all data manually."),
  bullet("Custom API-based integrations"),
  new Paragraph({ children: [new PageBreak()] })
);

// ══════════════════════════════════════════════════════════════════════════════
// 7. CLIENT Q&A SUMMARY
// ══════════════════════════════════════════════════════════════════════════════
children.push(
  h1("7.  Client Q&A Summary"),
  para("The following table summarises the most common questions raised by clients during technical discussions about DocuVault."),
  makeTable(["Client Question", "Answer"], [
    ["Can you offer an AMC for LLM upgrades?", "Yes. An AMC covers LLM upgrades, performance improvements, security patches, and UI enhancements."],
    ["Do you need to retrain the AI when upgrading the LLM?", "No. DocuVault uses RAG \u2014 the LLM is not trained on documents. Upgrades do not affect indexed data."],
    ["When is re-indexing required?", "Only if the embedding model itself is changed. This is handled automatically under AMC."],
    ["Can DocuVault integrate with our email system?", "Yes. Emails and attachments are ingested and indexed. Users can query email content through the AI assistant."],
    ["Can it work like Google Drive with automatic sync?", "Yes. A LAN Sync Connector or the Desktop Agent can sync documents automatically from user folders."],
    ["Does the AI train automatically when I upload a document?", "No. Uploading triggers indexing, which is fast and does not change the AI model."],
    ["How is DocuVault different from BigQuery?", "BigQuery is for structured data analytics using SQL. DocuVault is for semantic search and AI Q&A over unstructured documents."],
    ["Do users have to open a browser every time?", "No. With the Desktop Agent, DocuVault runs in the system tray. Files sync automatically and the platform is one click away."],
    ["Can the Desktop Agent work if the server is offline?", "Yes. The agent queues pending files locally and syncs them automatically once the server is reachable."],
    ["Does the AI require an internet connection or API key?", "No. The AI runs fully offline using Ollama. No cloud API key is needed. Downloaded once during setup."],
    ["Does data ever leave our network?", "Never. All documents, queries, AI responses, and user data stay entirely on your own hardware."],
    ["What happens if our internet goes down?", "Nothing \u2014 DocuVault continues to work exactly as normal. All components run on your local server."],
    ["How much disk space does the AI model need?", "The default model requires approximately 4.7 GB. Downloaded once. Additional models can be added."],
    ["Does DocuVault support voice interaction?", "Yes. The built-in Voice AI Assistant lets you speak questions and hear answers aloud. It works in any modern browser with no extra software."],
    ["Does the voice feature require internet?", "No. Speech recognition runs in the browser. The server-side Whisper fallback also runs locally. No cloud services involved."],
    ["Can the Desktop Agent auto-index documents?", "Yes. When auto-indexing is enabled, documents synced by the agent are immediately indexed for AI search without any manual action."],
    ["How do I manage the Desktop Agent remotely?", "The web dashboard at /workspace/agent/ shows agent status, recent syncs, and lets you edit configuration or download the agent."],
  ], [3200, 6160]),
);

// ── Build document ───────────────────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: MED_BLUE },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: MED_BLUE },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: MED_BLUE, space: 1 } },
          children: [new TextRun({ text: "DocuVault Client Reference Guide  \u2014  Confidential", font: "Arial", size: 18, color: "999999", italics: true })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 1 } },
          children: [
            new TextRun({ text: "DocuVault v3.0  \u2014  Renata AI  \u2014  Page ", font: "Arial", size: 18, color: "999999" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "999999" }),
          ],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  const outPath = "D:/AI_Model_Renata/Document-management/Group/V2/DocuVault/DocuVault_Client_Reference_Guide_v3.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("Document written to:", outPath);
});
