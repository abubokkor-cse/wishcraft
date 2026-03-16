import { TalkingHead } from "./modules/edumindHead.js";
import { LiveChatController } from "./modules/liveChat.js";
import { GeminiCollaborator } from "./modules/geminiCollaborator.js";
import { SmokeSystem } from "./smoke.js";

const AVATARS = {
    male: { url: './avatar/69435286403c000063429870.glb', body: 'M', voice: 'Charon' },
    female: { url: './avatar/694febf38f9c70cbc97ec46e.glb', body: 'F', voice: 'Aoede' }
};

const VOICES = ['Puck', 'Charon', 'Kore', 'Fenrir', 'Aoede', 'Leda', 'Orus', 'Zephyr'];
const VOICE_GENDER = {
    Charon: 'male', Fenrir: 'male', Orus: 'male', Puck: 'male',
    Aoede: 'female', Kore: 'female', Leda: 'female', Zephyr: 'female'
};

const LANGUAGES = {
    en: { name: 'English', instruction: 'Reply in English.' },
    bn: { name: 'বাংলা', instruction: 'Reply in Bangla (বাংলা). Use Bangla script.' },
    hi: { name: 'हिन्दी', instruction: 'Reply in Hindi (हिन्दी). Use Devanagari script.' },
    ar: { name: 'العربية', instruction: 'Reply in Arabic (العربية). Use Arabic script.' },
    es: { name: 'Español', instruction: 'Reply in Spanish (Español).' },
    zh: { name: '中文', instruction: 'Reply in Chinese (中文). Use Chinese characters.' },
    ja: { name: '日本語', instruction: 'Reply in Japanese (日本語). Use Japanese characters.' },
    fr: { name: 'Français', instruction: 'Reply in French (Français).' },
    af: { name: 'Afrikaans', instruction: 'Reply in Afrikaans.' },
    sq: { name: 'Shqip', instruction: 'Reply in Albanian (Shqip).' },
    am: { name: 'አማርኛ', instruction: 'Reply in Amharic (አማርኛ). Use Ethiopic script.' },
    hy: { name: 'Հայերեն', instruction: 'Reply in Armenian (Հայերեն). Use Armenian script.' },
    as: { name: 'অসমীয়া', instruction: 'Reply in Assamese (অসমীয়া).' },
    az: { name: 'Azərbaycan', instruction: 'Reply in Azerbaijani.' },
    eu: { name: 'Euskara', instruction: 'Reply in Basque (Euskara).' },
    be: { name: 'Беларуская', instruction: 'Reply in Belarusian.' },
    bs: { name: 'Bosanski', instruction: 'Reply in Bosnian.' },
    bg: { name: 'Български', instruction: 'Reply in Bulgarian.' },
    ca: { name: 'Català', instruction: 'Reply in Catalan.' },
    hr: { name: 'Hrvatski', instruction: 'Reply in Croatian.' },
    cs: { name: 'Čeština', instruction: 'Reply in Czech.' },
    da: { name: 'Dansk', instruction: 'Reply in Danish.' },
    nl: { name: 'Nederlands', instruction: 'Reply in Dutch.' },
    et: { name: 'Eesti', instruction: 'Reply in Estonian.' },
    fil: { name: 'Filipino', instruction: 'Reply in Filipino.' },
    fi: { name: 'Suomi', instruction: 'Reply in Finnish.' },
    gl: { name: 'Galego', instruction: 'Reply in Galician.' },
    ka: { name: 'ქართული', instruction: 'Reply in Georgian.' },
    de: { name: 'Deutsch', instruction: 'Reply in German (Deutsch).' },
    el: { name: 'Ελληνικά', instruction: 'Reply in Greek.' },
    gu: { name: 'ગુજરાતી', instruction: 'Reply in Gujarati.' },
    iw: { name: 'עברית', instruction: 'Reply in Hebrew.' },
    hu: { name: 'Magyar', instruction: 'Reply in Hungarian.' },
    is: { name: 'Íslenska', instruction: 'Reply in Icelandic.' },
    id: { name: 'Bahasa Indonesia', instruction: 'Reply in Indonesian.' },
    it: { name: 'Italiano', instruction: 'Reply in Italian.' },
    kn: { name: 'ಕನ್ನಡ', instruction: 'Reply in Kannada.' },
    kk: { name: 'Қазақ', instruction: 'Reply in Kazakh.' },
    km: { name: 'ខ្មែរ', instruction: 'Reply in Khmer.' },
    ko: { name: '한국어', instruction: 'Reply in Korean.' },
    lo: { name: 'ລາວ', instruction: 'Reply in Lao.' },
    lv: { name: 'Latviešu', instruction: 'Reply in Latvian.' },
    lt: { name: 'Lietuvių', instruction: 'Reply in Lithuanian.' },
    mk: { name: 'Македонски', instruction: 'Reply in Macedonian.' },
    ms: { name: 'Bahasa Melayu', instruction: 'Reply in Malay.' },
    ml: { name: 'മലയാളം', instruction: 'Reply in Malayalam.' },
    mr: { name: 'मराठी', instruction: 'Reply in Marathi.' },
    mn: { name: 'Монгол', instruction: 'Reply in Mongolian.' },
    ne: { name: 'नेपाली', instruction: 'Reply in Nepali.' },
    no: { name: 'Norsk', instruction: 'Reply in Norwegian.' },
    or: { name: 'ଓଡ଼ିଆ', instruction: 'Reply in Odia.' },
    pl: { name: 'Polski', instruction: 'Reply in Polish.' },
    pt: { name: 'Português', instruction: 'Reply in Portuguese.' },
    pa: { name: 'ਪੰਜਾਬੀ', instruction: 'Reply in Punjabi.' },
    ro: { name: 'Română', instruction: 'Reply in Romanian.' },
    ru: { name: 'Русский', instruction: 'Reply in Russian.' },
    sr: { name: 'Српски', instruction: 'Reply in Serbian.' },
    sk: { name: 'Slovenčina', instruction: 'Reply in Slovak.' },
    sl: { name: 'Slovenščina', instruction: 'Reply in Slovenian.' },
    sw: { name: 'Kiswahili', instruction: 'Reply in Swahili.' },
    sv: { name: 'Svenska', instruction: 'Reply in Swedish.' },
    ta: { name: 'தமிழ்', instruction: 'Reply in Tamil.' },
    te: { name: 'తెలుగు', instruction: 'Reply in Telugu.' },
    th: { name: 'ไทย', instruction: 'Reply in Thai.' },
    tr: { name: 'Türkçe', instruction: 'Reply in Turkish.' },
    uk: { name: 'Українська', instruction: 'Reply in Ukrainian.' },
    ur: { name: 'اردو', instruction: 'Reply in Urdu. Use Urdu script.' },
    uz: { name: "O'zbek", instruction: 'Reply in Uzbek.' },
    vi: { name: 'Tiếng Việt', instruction: 'Reply in Vietnamese.' },
    zu: { name: 'isiZulu', instruction: 'Reply in Zulu.' },
};

const CONFIG = {
    backendUrl: 'https://wishcraft-server-47389095635.us-central1.run.app',
    currentAvatar: 'male',
    currentLang: 'en',
    currentVoice: null, // null = use avatar default voice
    userName: '',
    speechBubbleTimeMs: 5000,
};

let taskList = JSON.parse(localStorage.getItem('wishcraft_tasks') || '[]');

let conversationLog = [];
const MAX_LOG_ENTRIES = 40;

function addToLog(role, content) {
    conversationLog.push({ role, content, time: new Date().toLocaleTimeString() });
    if (conversationLog.length > MAX_LOG_ENTRIES) conversationLog.shift();
}

function getConversationContext() {
    if (conversationLog.length === 0) return '';
    const lines = conversationLog.map(e => {
        const prefix = e.role === 'user' ? 'User' : e.role === 'genie' ? 'Genie' : 'Tool';
        return `[${e.time}] ${prefix}: ${e.content}`;
    });
    return `\n\n<recent_conversation>\nThis is a reconnected session. Here is what happened before the reconnection:\n${lines.join('\n')}\n</recent_conversation>`;
}

function saveTasks() {
    localStorage.setItem('wishcraft_tasks', JSON.stringify(taskList));
    window.wishcraft.sendToPanel({ type: 'tasks-updated', tasks: taskList });
}

let head = null;
let liveChatController = null;
let isLiveSessionActive = false;
let isScreenSharing = false;
let isWebcamActive = false;
let collaborator = null;
let genieState = 'idle';
let isTaskRunning = false;  // Prevents overlapping computer/automation tasks
let isLiveSessionStarting = false;  // Prevents double session starts
let wasGenieDismissed = false;  // Track if genie was explicitly dismissed (vs auto-reconnect)
let sessionStartTime = 0;  // Timestamp when session started, used for greeting grace period
const GREETING_GRACE_MS = 10000;  // Block tool calls for 10s after session start (greeting period)
let smokeSystem = null;
let speechTimer = null;
let hasPickedLanguage = false;
let initDone = false;  // Track when init() has completed loading settings

// DOM
const avatarContainer = document.getElementById('avatar-container');
const glowRing = document.getElementById('glow-ring');
const statusEl = document.getElementById('status');
const speechBubble = document.getElementById('speech-bubble');
const smokeCanvas = document.getElementById('smoke-canvas');
const langPicker = document.getElementById('lang-picker');

smokeSystem = new SmokeSystem(smokeCanvas);

document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        CONFIG.currentLang = btn.dataset.lang;
        hasPickedLanguage = true;
        langPicker.classList.add('hidden');
        const greeting = btn.dataset.greeting;
        showSpeech(greeting, 6000);
        startLiveSession(greeting);
        window.wishcraft.sendToPanel({ type: 'lang-changed', lang: btn.dataset.lang, name: LANGUAGES[btn.dataset.lang].name });
    });
});

function showSpeech(text, duration) {
    clearTimeout(speechTimer);
    speechBubble.textContent = text;
    speechBubble.classList.add('visible');
    speechTimer = setTimeout(() => speechBubble.classList.remove('visible'), duration || CONFIG.speechBubbleTimeMs);
}

function hideSpeech() {
    clearTimeout(speechTimer);
    speechBubble.classList.remove('visible');
}

function setGenieState(state) {
    genieState = state;
    console.log('🧞 State:', state);
    switch (state) {
        case 'idle': setStatus(''); if (head) head.setMood('neutral'); break;
        case 'summoned':
            avatarContainer.classList.add('visible');
            glowRing.classList.add('visible');
            if (head) head.setMood('happy');
            break;
        case 'listening':
            setStatus('🎤 Listening...');
            if (head) { head.setMood('neutral'); if (head.lookAt) head.lookAt(0.5, 0.5, 3000); }
            break;
        case 'acting':
            setStatus('🖱️ Working...');
            if (head) head.setMood('happy');
            break;
        case 'complete':
            setStatus('');
            showSpeech('✅ Done!', 3000);
            if (head) head.setMood('happy');
            setTimeout(() => setGenieState('idle'), 3000);
            break;
        case 'dismissed':
            setStatus(''); hideSpeech();
            avatarContainer.classList.remove('visible');
            glowRing.classList.remove('visible');
            break;
    }
}

function setStatus(text) {
    if (text) { statusEl.textContent = text; statusEl.classList.add('visible'); }
    else statusEl.classList.remove('visible');
}

async function initializeAvatar(avatarKey) {
    const av = AVATARS[avatarKey || CONFIG.currentAvatar];
    try {
        head = new TalkingHead(avatarContainer, {
            lipsyncModules: ["en"], lipsyncLang: "en",
            avatarMood: "neutral", avatarMute: false,
            avatarIdleEyeContact: 0.4, avatarIdleHeadMove: 0.5,
            avatarSpeakingEyeContact: 0.7, avatarSpeakingHeadMove: 0.6,
            modelPixelRatio: window.devicePixelRatio || 1,
            modelFPS: 30, modelMovementFactor: 0.8,
            cameraZoomEnable: false, cameraRotateEnable: false, cameraPanEnable: false,
            lightAmbientColor: 0x00ccff, lightAmbientIntensity: 0.6,
            lightDirectColor: 0xffffff, lightDirectIntensity: 1.5,
            lightDirectPhi: 1, lightDirectTheta: 2
        });
        window.head = head;
        await head.showAvatar({
            url: av.url, body: av.body, avatarMood: "neutral",
            ttsLang: "en-GB", lipsyncLang: "en",
            avatarIdleEyeContact: 0.4, avatarSpeakingEyeContact: 0.7,
            avatarIdleHeadMove: 0.5, avatarSpeakingHeadMove: 0.6
        });
        if (head.scene) head.scene.background = null;
        if (head.renderer) head.renderer.setClearColor(0x000000, 0);
        console.log('✅ Avatar loaded!', avatarKey || CONFIG.currentAvatar);
        return true;
    } catch (error) { console.error('❌ Avatar error:', error); return false; }
}

async function switchAvatar(avatarKey) {
    if (avatarKey === CONFIG.currentAvatar) return;
    CONFIG.currentAvatar = avatarKey;
    avatarContainer.innerHTML = '';
    head = null;
    await initializeAvatar(avatarKey);
    avatarContainer.classList.add('visible');
    glowRing.classList.add('visible');
    // Restart session with new voice
    if (isLiveSessionActive) { stopLiveSession(); setTimeout(() => startLiveSession(), 500); }
}

async function startLiveSession(initialGreeting, silentStart = false) {
    if (isLiveSessionActive || isLiveSessionStarting) return;
    isLiveSessionStarting = true;

    try {
        const apiKey = await window.wishcraft.getApiKey();
        if (!apiKey) { showSpeech('❌ No API key!', 5000); return; }
        CONFIG.apiKey = apiKey; // Store for Computer Use agent

        const langConfig = LANGUAGES[CONFIG.currentLang] || LANGUAGES.en;
        const currentVoice = CONFIG.currentVoice || AVATARS[CONFIG.currentAvatar].voice;

        const taskContext = taskList.length > 0
            ? `\n\nACTIVE TASKS (the user has these ongoing tasks):\n${taskList.map((t, i) => `${i + 1}. ${t.name} - ${t.status}`).join('\n')}`
            : '';

        let memoryContext = '';
        try {
            const facts = await window.wishcraft.memory.getAllFacts();
            const history = await window.wishcraft.memory.getHistory(5);
            const factEntries = Object.entries(facts);
            if (factEntries.length > 0) {
                memoryContext += '\n\nUSER MEMORY (things you know about this user):\n';
                memoryContext += factEntries.map(([k, v]) => `• ${k}: ${v}`).join('\n');
            }
            if (history.length > 0) {
                memoryContext += '\n\nRECENT SESSION HISTORY:\n';
                memoryContext += history.map(h => `• [${h.timestamp?.split('T')[0] || 'recent'}] ${h.summary}`).join('\n');
            }
        } catch (e) { console.warn('Memory load failed:', e); }

        let skillsContext = '';
        try {
            await window.wishcraft.skills.loadAll();
            skillsContext = await window.wishcraft.skills.getSummary();
        } catch (e) { console.warn('Skills load failed:', e); }

        const greetingInstruction = silentStart
            ? 'Do NOT speak or greet. The user is sending you a file. Wait silently for their input, then respond to it.'
            : !window._genieHasGreeted
                ? 'On your FIRST response, briefly introduce yourself as the Genie of Wishcraft and ask for a wish. IMPORTANT: Do NOT call any tools or execute any actions during your greeting. Only speak your introduction — no volume changes, no screenshots, no automation. Wait for the user to make a wish before using any tools.'
                : wasGenieDismissed
                    ? 'The user dismissed you earlier and has now summoned you back. Say briefly you are back and ready for the next wish. Do NOT call any tools or re-execute previous actions.'
                    : 'This is an automatic reconnection after a session drop. Do NOT speak, do NOT greet, do NOT say "I am back". Just silently resume and wait for the user to speak. Continue the conversation naturally when they talk to you.';

        const PLATFORM = window.wishcraft?.platform || 'darwin';
        const IS_MAC = PLATFORM === 'darwin';
        const IS_WIN = PLATFORM === 'win32';
        const IS_LINUX = PLATFORM === 'linux';
        const PLATFORM_NAME = IS_MAC ? 'Mac' : IS_WIN ? 'Windows' : 'Linux';
        const MOD_KEY = IS_MAC ? 'Command' : 'Ctrl';

        const systemInstruction = `<role>
You are the Genie of Wishcraft — a powerful, friendly AI assistant that controls the user's ${PLATFORM_NAME} computer.
Personality: warm, magical, concise. Speak like a mystical genie granting wishes.
${CONFIG.userName ? `The user's name is ${CONFIG.userName}. Use their name naturally in conversation.` : ''}
</role>

<language>
Your PRIMARY language is ${langConfig.name}. ${langConfig.instruction}
ALWAYS speak and respond in ${langConfig.name} by default — greetings, confirmations, questions, everything.
If the user speaks a different language, switch to match them, but default back to ${langConfig.name}.
</language>

<voice_rules>
You communicate via voice audio. Keep spoken responses to 1-3 sentences unless the user explicitly asks for detail.
Be direct — state what you did or will do, then ask for the next wish.
Never read out long lists, URLs, or code aloud. Summarize instead.
After completing a task, confirm briefly and ask for the next wish.
</voice_rules>

<current_context>
Current date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}.
For time-sensitive queries requiring up-to-date information, use the current date when formulating search queries.
${greetingInstruction}
</current_context>

<tools>
You have Google Search for real-time info, ${IS_MAC ? '286+ macOS automation functions' : IS_WIN ? '286+ Windows automation functions' : '55+ Linux automation functions'}, a skill library, and screen control.

TIER 1 — INSTANT (fire-and-forget, under 0.5s):
open_app, close_app, open_url, search_web, volume_control, brightness_control, dismiss_genie, run_command

TIER 2 — FAST AUTOMATION (${IS_MAC ? 'AppleScript/CLI' : 'PyAutoGUI/CLI'}, 1-3s):
desktop_automation: ${IS_MAC ? '286+' : IS_WIN ? '286+' : '55+'} deterministic ${PLATFORM_NAME} functions. Work 100% reliably WITHOUT seeing the screen.
Categories: ${IS_MAC ? 'Word, VS Code, Finder, Notes, Chrome, YouTube, Safari, Music, System, Mail, Calendar, Reminders, Messages, Terminal, Pages, Numbers, Keynote, Preview, Photos, Voice Memos, Contacts, Clipboard, Files, Spotlight, App, Keystroke, File Organizer' : IS_WIN ? 'Word, VS Code, Chrome, YouTube, System, Files, Clipboard, App, File Organizer, Gmail, WhatsApp' : 'Word, VS Code, Chrome, YouTube, System, Files, Clipboard, App, File Organizer, Gmail, WhatsApp'}.
Pattern: action = prefix_verb (e.g. word_write, chrome_new_tab, files_read_text). See tool description for full list.

IMAGE PROCESSING — AI-powered, cross-platform:
remove_background: Remove background from images. Modes: single (one file), batch (multiple files), folder (all images in a folder). Outputs transparent PNG. Works on Windows/macOS/Linux.

PRESENTATION CREATOR:
create_presentation: Generate a professional PowerPoint (.pptx) file. Gemini designs the slides with colors, shapes, layouts, and content. Saves to Desktop. Use when user asks for slides, presentation, deck, pitch deck, or lecture slides.

AUDIO TRANSCRIPTION:
transcribe_audio: Transcribe any audio/video file to text using Gemini AI. Supports MP3, WAV, M4A, OGG, FLAC, MP4, MOV. Saves transcription as .txt file. Use when user asks to transcribe, convert audio to text, or get text from recording.

TIER 3 — SLOW (screen vision, 5-30s — last resort):
find_and_click, execute_computer_task, send_whatsapp_message, read_whatsapp_messages

GOOGLE SEARCH — Real-time information (runs automatically via grounding):
Weather, news, sports, stocks, current events, facts — just answer directly.

SCREEN SHARE & WEBCAM — Live video streaming:
toggle_screen_share: Start/stop continuous screen capture (~1 FPS). Lets you see what the user is doing in real-time.
toggle_webcam: Start/stop the user's webcam feed (~1 FPS). Lets you see the user.
Note: Audio+video sessions are limited to ~2 minutes. Use these when visual context is helpful, then turn off when done.

COLLABORATOR — Deep analysis & long content generation (via Gemini 3.1 Flash Lite):
analyze_file: Read and analyze ANY file — images (jpg/png/gif/webp), PDFs (scanned or text), text files, CSV, JSON, HTML. Uses AI vision for images/PDFs. Returns detailed analysis.
generate_content: Generate long-form content — CVs, essays, reports, code, letters, business plans, study notes, translations. Returns full text that you then write to Word/Notes/VS Code using desktop_automation.

IMPORTANT COLLABORATION WORKFLOW:
1. User asks for long content (CV, essay, report, letter, etc.) → FIRST ask 2-3 quick clarifying questions to gather context:
   - CV/Resume: "What's your field? How many years of experience? Any specific role you're targeting?"
   - Essay: "What's the topic? Academic or creative? How long should it be?"
   - Cover letter: "Which company and role? What are your key strengths for this?"
   - Business plan: "What's the business idea? Target market? Stage (startup/expansion)?"
   - Report: "What's the subject? Who's the audience? Formal or informal?"
   - General: "Any specific requirements, tone, or length?"
2. After gathering info → call generate_content with ALL the user's context packed into the prompt
3. It auto-writes to Word and saves → speak a SHORT summary ("Done! Your CV is in Word with 6 sections")
4. User asks to analyze a file → call analyze_file with the path → speak key findings briefly
NEVER generate content without first understanding what the user needs. Ask, then generate.
</tools>

<decision_rules>
0. GREETING RULE: On your FIRST response after connecting, ONLY speak your greeting. Do NOT call ANY tools (no volume_control, no take_screenshot, no desktop_automation, nothing). Wait for the user's first wish before using tools. On auto-reconnection (session drop), do NOT speak at all — silently resume and wait for the user. Only say "I'm back" if the user explicitly dismissed you and summoned you again.
1. ALWAYS prefer desktop_automation (Tier 2) over find_and_click or keystrokes. It is deterministic and instant.
2. For Word, VS Code, ${IS_MAC ? 'Safari, Notes, Music, Finder' : 'Chrome, Finder'}, Excel → ALWAYS use desktop_automation. Never use find_and_click for these.
3. For writing text in Word/Pages/VS Code → use word_write / pages_write / vscode_write_code (clipboard paste, 100% reliable).
4. For real-time info (weather, news, prices) → answer using Google Search grounding.
5. For WhatsApp → use send_whatsapp_message (handles everything automatically).
6. For YouTube → use play_youtube.
7. execute_computer_task is LAST RESORT only when nothing else works. BUT if find_and_click fails or the user explicitly asks to "use computer agent" or "computer use" → use execute_computer_task immediately.
8. For multi-step tasks: plan the steps mentally, then execute sequentially. If a step fails, try an alternative before giving up. If find_and_click returns "not found" or "skipped" → escalate to execute_computer_task. For GMAIL multi-step tasks: execute ONE action at a time, read the result, tell the user what happened (e.g. "You have 5 unread emails", "Reply sent successfully"), then do the next step. Always call gmail_ensure_list_view between email operations.
9. Verify tool choice: before calling a tool, confirm you are using the highest-tier (fastest) option available.
10. For long content (CV, essay, report, code file) going to Word: use generate_content with destination="word" (auto-writes to Word). For content going to WhatsApp/email/chat: use generate_content with destination="return", then send the returned text via send_whatsapp_message or gmail_compose etc. NEVER auto-open Word when the user wants to send a message.
11. For file analysis (images, PDFs, documents): ALWAYS use analyze_file. Never ask the user to describe the file to you. Read it yourself. After finding a file with file_search or desktop_automation, you MUST call analyze_file with the file path to read its contents. Then speak a DETAILED summary: title, key sections, main points, data, and conclusions. Do NOT just say "I found the file" — always read and explain what's inside.
12. Before calling generate_content: ALWAYS ask 2-3 quick questions first to understand the user's needs, field, audience, and preferences. Then include ALL gathered info in the prompt. Better input = better output.
13. ONLY do what the user asks. Do NOT do extra tasks the user did not request. If user says "fix the code" → ONLY fix the code. Do NOT also create documents, write reports, or do anything else. If user says "make a spreadsheet" → ONLY make the spreadsheet. Do NOT also open Word or create extra files. ONE task = ONE action. Ask before doing anything extra.
14. STAY ON TASK. When a task is in progress (e.g. sending a WhatsApp message), ALL follow-up messages from the user are about THAT task until the user explicitly changes topic. Example: User says "send a short story about ant" → you are sending a WhatsApp message. If user then says "magical" → that means they want a MAGICAL ant story sent via WhatsApp. Do NOT switch to Word or any other app. Stay focused on the current task.
15. NEVER auto-open Word or create documents unless the user EXPLICITLY says "write a document", "create a Word file", "open Word", etc. If user says "write a story" during a WhatsApp conversation → they want to SEND the story via WhatsApp, NOT create a Word document. If user says "generate content" → generate it and send it through the CURRENT channel (WhatsApp, email, etc.), not Word.
16. When a WhatsApp send fails, RETRY the send. Do NOT switch to a different task. Ask the user if they want to try again or cancel.
17. For installing apps/games: use open_app("App Store") then tell the user to search for the app. Do NOT use execute_computer_task or find_and_click for installing apps. You CANNOT install apps automatically — just open the App Store and guide the user.
18. NEVER use execute_computer_task for tasks that can be done with Tier 1 or Tier 2 tools — EXCEPT these cases where you MUST use execute_computer_task DIRECTLY:
   a) The user explicitly says "computer agent", "computer use", or "use agent".
   b) MULTI-STEP WEB TASKS: shopping/add to cart, filling forms, browsing multiple pages, reading page content that chrome_read_page_text cannot read, navigating website UI (e.g. clicking tabs, buttons, links on a page). Examples: "buy X on Amazon", "search product and add to cart", "read all repos on GitHub", "book a ticket", "fill out this form".
   c) find_and_click already failed or returned "skipped" for this task.
19. ESCALATION RULE: If find_and_click returns "not found", "skipped", or "browser actions" → IMMEDIATELY retry the SAME task with execute_computer_task. NEVER give up or ask the user to do it manually.
20. AUTOMATION FALLBACK: If desktop_automation returns success=false, the system auto-escalates to Computer Use. If that also fails, tell the user what happened and suggest an alternative.
21. SPREADSHEET ONE-CALL RULE: When excel_create_spreadsheet or numbers_create_spreadsheet returns success, the spreadsheet is COMPLETE. Do NOT call ANY more excel_/numbers_ functions (type_in_cell, go_to_cell, enter_formula, save, etc.) after create_spreadsheet succeeds. The one-call function already did EVERYTHING for the data.
</decision_rules>

<workflows>
WORD — Creating a formatted document:
1. desktop_automation("word_open") → desktop_automation("word_new_document")
2. desktop_automation("word_heading_1") → desktop_automation("word_write", {text: "Title"})
3. desktop_automation("word_new_line") → desktop_automation("word_normal_text") → desktop_automation("word_write", {text: "Body..."})
4. desktop_automation("word_save", {filename: "My Document"})
Or ONE-CALL: desktop_automation("word_write_formatted_document", {title: "Report", sections: [{heading: "Intro", text: "..."}, {heading: "Points", bullet_items: ["A","B","C"]}]})

WORD — Editing:
- REWRITE: word_clear_all (select all + delete in CURRENT doc) → write new content. NEVER create a new document to rewrite — clear the existing one.
- READ: word_read_content → returns full text.
- DELETE text: word_find({text}) → word_cut.
- REPLACE: word_find_replace({find_text, replace_text}).
- APPEND: word_move_to_end → word_new_line → word_write.
- SAVE: ALWAYS save after writing with word_save({filename}).

EXCEL — Creating a spreadsheet:
ONE-CALL: desktop_automation("excel_create_spreadsheet", {title: "Budget", headers: ["Category", "Amount"], rows: [["Rent", "1500"], ["Food", "600"]], formulas: [{"cell": "B4", "formula": "=SUM(B2:B3)"}]})
This ONE call does everything: opens Excel, creates workbook, types headers, types all data, adds formulas, bolds headers, saves. AFTER this call succeeds — STOP IMMEDIATELY. Say "Done!" and ask for next wish. NEVER call type_in_cell, enter_formula, go_to_cell, save, or ANY other excel_ function after create_spreadsheet.

EXCEL EXAMPLES — Use these exact patterns:
Budget: {title:"Monthly Budget", headers:["Category","Amount"], rows:[["Rent","1500"],["Food","600"],["Transport","300"]], formulas:[{"cell":"A5","formula":"Total"},{"cell":"B5","formula":"=SUM(B2:B4)"}]}
Grades: {title:"Student Grades", headers:["Subject","Score"], rows:[["Math","85"],["Science","92"],["English","78"]], formulas:[{"cell":"A5","formula":"Average"},{"cell":"B5","formula":"=AVERAGE(B2:B4)"}]}
Sales: {title:"Sales Report", headers:["Product","Qty","Price","Revenue"], rows:[["Laptop","10","999",""],["Phone","25","699",""]], formulas:[{"cell":"D2","formula":"=B2*C2"},{"cell":"D3","formula":"=B3*C3"},{"cell":"A4","formula":"Total"},{"cell":"D4","formula":"=SUM(D2:D3)"}]}

EXCEL — Editing an existing spreadsheet (NOT creating new):
- Navigate: excel_go_to_cell({cell: "B5"}) → edit: excel_type_in_cell({text: "new value"})
- Formula: excel_go_to_cell({cell: "C10"}) → excel_enter_formula({formula: "=SUM(C2:C9)"})
- Format: excel_select_range({range: "B2:B10"}) → excel_format_currency
- Read: excel_go_to_cell({cell: "A1"}) → excel_read_cell

NUMBERS (Apple Numbers) — Creating a spreadsheet:
ONE-CALL: desktop_automation("numbers_create_spreadsheet", {title: "Budget", headers: ["Category", "Amount"], rows: [["Rent", "1500"], ["Food", "600"]], formulas: [{"cell": "B4", "formula": "=SUM(B2:B3)"}]})
This ONE call does everything: opens Numbers, creates spreadsheet, sets headers, sets all data, adds formulas, bolds headers, saves — ALL via native AppleScript (no keyboard). AFTER this call succeeds — STOP IMMEDIATELY. Say "Done!" NEVER call type_in_cell, enter_formula, go_to_cell, save, or ANY other numbers_ function after create_spreadsheet.
NOTE: If user doesn't specify which app (Excel vs Numbers), prefer Excel if installed. Use Numbers only if user specifically says "Numbers" or "Apple Numbers".

NUMBERS — Editing an existing spreadsheet (NOT creating new):
- Direct cell set: numbers_type_in_cell({text: "new value", cell: "B5"}) — sets value via native AppleScript
- Formula: numbers_enter_formula({formula: "=SUM(C2:C9)", cell: "C10"}) — sets formula via native AppleScript
- Read: numbers_read_cell({cell: "A1"}) — reads value via native AppleScript
- Navigate: numbers_go_to_cell({cell: "B5"}) — selects cell via native AppleScript

MAIL — Reading and responding to emails:
- Check new mail: desktop_automation("mail_check")
- See unread count: desktop_automation("mail_unread_count")
- List inbox: desktop_automation("mail_list_inbox", {count: 10}) or desktop_automation("mail_list_inbox", {unread_only: true})
- Read a message: desktop_automation("mail_read_message", {index: 1}) — index 1 = newest
- Reply: desktop_automation("mail_reply", {index: 1, body: "Thank you!", send: true})
- Forward: desktop_automation("mail_forward", {index: 1, to: "someone@email.com", body: "FYI", send: true})
- Compose new: desktop_automation("mail_compose", {to: "someone@email.com", subject: "Hello", body: "Hi there!", send: true})
- Search: desktop_automation("mail_search", {query: "invoice"})
MAIL WORKFLOW: When user says "check my email" or "read my mail" → first call mail_list_inbox to see messages, then tell the user what's in their inbox. When they want to respond, use mail_reply with the correct index. set send:false to let user review before sending.

GMAIL — Web Gmail automation (Chrome browser). All gmail_ actions auto-open Chrome with Gmail if not already open.
AVAILABLE COMMANDS:
- gmail_open — Open Gmail in Chrome
- gmail_ensure_list_view — Close any compose/reply, go back to inbox list. ALWAYS call before starting any Gmail task.
- gmail_get_state — Returns current Gmail view (list/email/compose/reply)
- gmail_unread_count — Returns {unread_count: N}
- gmail_next / gmail_prev — Move cursor to next/previous email in list
- gmail_open_email — OPEN the currently selected email (press 'o'). REQUIRED before reading or replying.
- gmail_read_email — Read the OPEN email content (sender, subject, body). Email MUST be open first.
- gmail_reply({body, send:true}) — Reply to the OPEN email. Email MUST be open first.
- gmail_reply_all({body, send:true}) — Reply all to the OPEN email.
- gmail_forward({to, body, send:true}) — Forward the OPEN email.
- gmail_compose({to, subject, body, send:true}) — Compose NEW email. Does NOT need an open email.
- gmail_search({query}) — Search Gmail
- gmail_archive / gmail_delete / gmail_star / gmail_mark_read / gmail_mark_unread / gmail_back_to_list

GMAIL STEP-BY-STEP WORKFLOWS — Follow these EXACTLY:

WORKFLOW: "Send email to X"
1. gmail_compose({to, subject, body, send: true}) — compose fills To/Subject/Body and sends in ONE call
2. Confirm send_confirmed:true → tell user "Email sent!"

WORKFLOW: "Reply to Nth email" or "Reply to latest email"
1. gmail_ensure_list_view — reset to inbox list
2. gmail_next (repeat N-1 times to reach Nth email. skip this for 1st/latest email)
3. gmail_open_email — OPEN the email (MANDATORY before reply)
4. gmail_read_email — read it to verify it's the right email
5. gmail_reply({body, send: true}) — reply to the OPEN email
6. Confirm send_confirmed:true → tell user "Reply sent!"
7. gmail_ensure_list_view — reset for next action

WORKFLOW: "How many unread emails?"
1. gmail_unread_count → tell user the count

WORKFLOW: "Read my emails" / "What's in my inbox?"
1. gmail_ensure_list_view — reset to list
2. gmail_unread_count — tell user the count
3. gmail_open_email — open first email
4. gmail_read_email — read it, tell user subject + summary
5. gmail_ensure_list_view — go back to list for next email

WORKFLOW: "Open/read the Nth email"
1. gmail_ensure_list_view — reset to list
2. gmail_next (repeat N-1 times)
3. gmail_open_email — OPEN the email
4. gmail_read_email — read content, tell user subject + summary

WORKFLOW: "Forward this email to X"
1. gmail_ensure_list_view
2. gmail_next (if needed)
3. gmail_open_email — MUST open first
4. gmail_forward({to, body, send: true})

CRITICAL GMAIL RULES:
- ALWAYS call gmail_open_email BEFORE gmail_reply, gmail_reply_all, gmail_forward, or gmail_read_email. These ONLY work on an OPEN email.
- ALWAYS call gmail_ensure_list_view before starting a NEW Gmail task.
- Execute ONE action at a time, check result, tell user what happened, then proceed.
- If gmail_reply returns send_confirmed:true → "Reply sent." If false/missing → "Reply may not have sent" and retry.
- gmail_compose is the ONLY action that works without opening an email first (it creates a new compose window).
GMAIL vs MAIL: gmail_ = web Gmail (Chrome), mail_ = Apple Mail app. If user says "Gmail" → use gmail_. If user says "email"/"mail" → ask which or default to gmail_.
GMAIL NOTE: Keyboard shortcuts must be enabled in Gmail Settings → General → "Keyboard shortcuts on".


1. desktop_automation("vscode_create_file_with_code", {folder_path: "~/Desktop/project", filename: "hello.py", code: "print('Hello!')"})
2. To run: desktop_automation("vscode_run_code") — Code Runner (Ctrl+Option+N), auto-detects language, auto-saves, PREFERRED method
3. To see output/errors: desktop_automation("vscode_read_terminal_output") — copies terminal text so you can read it
4. If output has errors → fix with desktop_automation("vscode_edit_line", {line_number: 5, new_text: "fixed code"}) → run again
5. Alternative run: desktop_automation("vscode_run_in_terminal", {command: "python3 hello.py"}) — only if Code Runner doesn't work
6. To go back to editor: desktop_automation("vscode_focus_editor")
ALWAYS use vscode_run_code to run code. ALWAYS use vscode_read_terminal_output after running to check results.

FILE ORGANIZER — Always scan first, suggest, wait for approval:
1. desktop_automation("organize_suggest_plan", {path: "~/Downloads"}) → read result
2. Tell user what you found (file count, categories, duplicates, old files) and recommend actions.
3. WAIT for user approval. Do NOT execute until user says yes.
4. Execute with dry_run: false only after approval.
Actions: organize_scan_directory, organize_find_duplicates, organize_by_type, organize_by_date, organize_cleanup_old, organize_remove_duplicates, organize_flatten_folder, organize_rename_pattern, organize_size_report
</workflows>

<cv_format>
When creating a CV/resume, use word_write_formatted_document with FAANG-style ATS-friendly structure:
1. NAME (centered, Heading 1) → title field
2. CONTACT INFO → {center: true, text: "City | Phone | Email | LinkedIn | GitHub"}
3. PROFESSIONAL SUMMARY → {heading: "Professional Summary", text: "2-3 sentences"}
4. TECHNICAL SKILLS → {heading: "Technical Skills", bullet_items: ["Languages: ...", "Frontend: ...", "Backend: ..."]}
5. EXPERIENCE → {heading: "Professional Experience", items: [{left: "Job Title", right: "Dates", subleft: "Company | Location", details: ["Achievement with metrics..."]}]}
6. PROJECTS → {heading: "Projects", items: [{left: "Name — Stack", right: "Year", details: ["Impact..."]}]}
7. EDUCATION → {heading: "Education", items: [{left: "University", right: "Dates", subleft: "Degree — Major", subright: "Location"}]}
8. CERTIFICATIONS → {heading: "Certifications", bullet_items: ["Cert | Issuer, Year"]}
Rules: Keep to 1 page. Action verbs + metrics in bullets. Ask user for info if not provided.
</cv_format>

<whatsapp_rules>
- "message [name]" → call send_whatsapp_message with contact name IN ENGLISH.
- Contact not saved → ask for phone WITH country code (+880...), save_contact first.
- Follow-up messages → call send_whatsapp_message again.
- Reading replies → call read_whatsapp_messages. Unread → check_whatsapp_messages.
- NEVER call open_app("WhatsApp") before send_whatsapp_message.
- NEVER call open_app before play_youtube.
- The "name" parameter MUST be in English/Latin characters. NEVER pass Bengali/Arabic/Hindi/non-Latin script.
- Phone numbers MUST include country code with + prefix (e.g. +8801712345678).
- After WhatsApp actions, a screenshot is sent. Look at it to confirm success.
</whatsapp_rules>

<constraints>
1. ALL tool parameters MUST be in English/Latin characters.
2. Talk to the USER in their language. Talk to TOOLS in English.
3. Exception: message content in send_whatsapp_message can be any language.
4. If user says "stop", "cancel", "bad de", "thak" during a task → call cancel_task immediately.
4. If the user says "go to the lamp", "dismiss", "goodbye" → call dismiss_genie.
5. NEVER reorganize files without scanning and getting user approval first.
</constraints>

<memory>
You can save facts about the user using remember_user_fact. Save: name, preferences, common apps, projects, nicknames.
Memory persists across sessions — use it to personalize over time.
When dismissed, save a 1-line session summary using save_session_summary.
</memory>${taskContext}${memoryContext}${skillsContext}${window._genieHasGreeted ? getConversationContext() : ''}`;

        liveChatController = new LiveChatController(apiKey, {
            serverUrl: CONFIG.backendUrl,
            voiceName: currentVoice,
            systemInstruction: systemInstruction,

            tools: [
                { google_search: {} },
                {
                    functionDeclarations: [
                        {
                            name: "open_app",
                            description: "Open an application on the user's computer. Examples: 'Chrome', 'WhatsApp', 'Spotify', 'VSCode', 'Terminal', 'Calculator', 'Finder'",
                            parameters: { type: "OBJECT", properties: { app_name: { type: "STRING", description: "App name to open" } }, required: ["app_name"] }
                        },
                        {
                            name: "close_app",
                            description: "Close/quit an application.",
                            parameters: { type: "OBJECT", properties: { app_name: { type: "STRING", description: "App name to close" } }, required: ["app_name"] }
                        },
                        {
                            name: "open_url",
                            description: "Open a URL in the default browser.",
                            parameters: { type: "OBJECT", properties: { url: { type: "STRING", description: "URL to open" } }, required: ["url"] }
                        },
                        {
                            name: "search_web",
                            description: "Search Google for something in browser.",
                            parameters: { type: "OBJECT", properties: { query: { type: "STRING", description: "Search query" } }, required: ["query"] }
                        },
                        {
                            name: "volume_control",
                            description: "Control system volume: up, down, mute, unmute.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    action: { type: "STRING", description: "'up', 'down', 'mute', 'unmute'" },
                                    amount: { type: "INTEGER", description: "Amount 0-100, default 10" }
                                }, required: ["action"]
                            }
                        },
                        {
                            name: "run_command",
                            description: "Run a shell command on the user's computer.",
                            parameters: { type: "OBJECT", properties: { command: { type: "STRING", description: "Shell command to run" } }, required: ["command"] }
                        },
                        {
                            name: "desktop_automation",
                            description: `Run any desktop automation. 358+ actions across ${IS_MAC ? '26 app categories' : IS_WIN ? '10+ app categories' : 'universal app categories'}. Pattern: action name = app_verb (e.g. word_write, excel_go_to_cell, vscode_open_folder, ${IS_MAC ? 'finder_list_folder, notes_create' : 'chrome_new_tab'}).
${IS_MAC ? `
CATEGORIES (prefix_action format):
word_ — open, new_document, write({text}), save({filename}), heading_1/2/3, bold, italic, bullet_list, read_content, write_formatted_document({title,sections}), clear_all, find, find_replace, new_line, normal_text, move_to_end
vscode_ — open, open_folder({path}), new_file, write_code({code}), read_code, save_as({filename}), run_code, terminal_run({command}), run_in_terminal({command}), create_file_with_code({folder_path,filename,code}), install_extension({extension_id})
finder_ — open_folder({path}), list_folder({path}), search({query,folder}), create_folder({path}), move_file({source,destination}), copy_file, rename({path,new_name}), move_to_trash({path})
notes_ — create({title,body}), read({title}), list, search({query}), append({title,text})
chrome_ — open, new_tab({url}), navigate({url}), close_tab, get_url, get_title, list_tabs, read_page_text, execute_js({code}), scroll_down/up, find({text}), zoom_in/out
youtube_ — open({query}), play_pause, mute, fullscreen, seek_forward/backward, speed_up/down, next/prev_video
safari_ — open, new_tab({url}), get_url, list_tabs
music_ — play, pause, next, previous, get_current_track, set_volume({level})
system_ — volume_set({level}), dark_mode_toggle, get_battery, get_disk_space, wifi_status/on/off, screenshot_full, lock_screen
mail_ — open, compose({to,subject,body,cc,send}), list_inbox({count,unread_only}), unread_count, read_message({index}), reply({index,body,send}), forward({index,to,body,send}), search({query,count}), mark_read({index}), mark_unread({index}), delete({index}), check
gmail_ — open, get_state, ensure_list_view, compose({to,subject,body,cc,bcc,send}), search({query}), reply({body,send}), reply_all({body,send}), forward({to,body,send}), send, go_inbox, go_sent, go_drafts, go_starred, go_all_mail, open_email, back_to_list, next, prev, newer, older, archive, delete, spam, star, mark_read, mark_unread, mark_important, select, select_all, mute, label, move_to, snooze, undo, refresh, read_email, unread_count
GMAIL RULE: gmail_ = web Gmail in Chrome (keyboard shortcuts). mail_ = Apple Mail app (native AppleScript). When user says "Gmail" or "Google Mail" → use gmail_. When user says "Mail" or "Apple Mail" → use mail_. For compose: gmail_compose fills To/Subject/Body and sends in ONE call. set send:false to let user review. IMPORTANT: Before performing a new Gmail task, call gmail_ensure_list_view to auto-close any open compose/reply/email and return to inbox list. This prevents state conflicts.
calendar_ — create_event({title,start_date,end_date}), today_events
reminders_ — create({title,list_name,due_date}), list, complete | messages_ — send({recipient,text})
terminal_ — run_command({command}), open | pages_ — write({text}), save
numbers_ — open, close, new_spreadsheet, save({filename}), open_file({path}), go_to_cell({cell}), type_in_cell({text,cell}), type_and_stay({text}), enter_formula({formula,cell}), read_cell({cell}), bold, italic, underline, increase_font, decrease_font, align_center, align_left, auto_align, add_border_top/bottom/left/right, merge_cells, unmerge_cells, select_all, select_row, select_column, copy, paste, cut, paste_values, add_row_above, add_row_below, add_column_left, add_column_right, delete_row, delete_column, sort, add_filter, find({text}), read_selection, new_sheet, next_sheet, prev_sheet, undo, redo, insert_date, insert_time, autofill, create_spreadsheet({title,headers,rows,formulas})
NUMBERS RULE: To create a spreadsheet in Apple Numbers, ALWAYS use numbers_create_spreadsheet with ALL params in ONE call — include title, headers, rows, AND formulas together. Uses native AppleScript (no keyboard) to set cells directly — 100% reliable. NEVER call save, type_in_cell, enter_formula, or any other numbers_ function after create_spreadsheet. ONE call does EVERYTHING. For editing, use type_in_cell({text,cell}) or enter_formula({formula,cell}) with the cell parameter for direct access.
excel_ — open, new_workbook, save({filename}), open_file({path}), go_to_cell({cell}), type_in_cell({text}), type_and_stay({text}), enter_formula({formula}), bold, italic, format_currency, format_percent, format_number, format_date, add_border, select_range({range}), select_row, select_column, insert_row, delete_row, sort, add_filter, create_table, find({text}), find_replace, autosum, read_cell, read_selection, new_sheet, next_sheet, undo, redo, create_spreadsheet({title,headers,rows,formulas}), create_chart({data_range,chart_type,title})
CHART TYPES for create_chart: pie, bar, column, line, area, doughnut, radar, 3dpie, 3dbar, 3dcolumn, 3dline, 3darea, scatter. Default is "pie". data_range covers headers+data (e.g. "A1:B5").
EXCEL RULE: To create a spreadsheet, ALWAYS use create_spreadsheet with ALL params in ONE call — include title, headers, rows, AND formulas together. It creates workbook, enters all data, adds formulas, bolds headers, then saves — all in one step. NEVER call save, type_in_cell, enter_formula, or any other excel_ function after create_spreadsheet. ONE call does EVERYTHING. Do NOT duplicate the work with individual calls.
files_ — read_text({path}), write_text({path,content}), append_text, read_lines, insert_at_line, replace_text({path,old_text,new_text}), find_by_name, read_pdf_text({path})
clipboard_ — read, write({text}) | keystroke_ — type({text,app_name}), key({key_code,modifiers})
app_ — open({name}), close, switch, list_running | spotlight_ — search_and_open({query})
organize_ — scan_directory, find_duplicates, by_type, by_date, cleanup_old, suggest_plan, size_report` :
                                    IS_WIN ? `
CATEGORIES (prefix_action format):
word_ — open, new_document, write({text}), save({filename}), heading_1/2/3, bold, italic, underline, bullet_list, read_content, write_formatted_document({title,sections}), clear_all, find, find_replace, new_line, normal_text, move_to_end, move_to_start, center_text, left_text, right_text, justify, copy, paste, cut, undo, redo, select_all, increase_font, decrease_font, single_space, double_space, strikethrough, toggle_case, upper_case, indent, outdent, page_break, line_break, paste_plain, print, close
chrome_ — open, new_tab({url}), navigate({url}), close_tab, get_url, get_title, list_tabs, read_page_text, execute_js({code}), scroll_down/up, find({text}), zoom_in/out
youtube_ — open({query}), play_pause, mute, fullscreen, seek_forward/backward, speed_up/down, next/prev_video
gmail_ — open, get_state, ensure_list_view, compose({to,subject,body,cc,bcc,send}), search({query}), reply({body,send}), reply_all({body,send}), forward({to,body,send}), send, open_email, back_to_list, next, prev, archive, delete, star, mark_read, mark_unread, read_email, unread_count
vscode_ — open, open_folder({path}), new_file, write_code({code}), read_code, save_as({filename}), run_code, terminal_run({command}), run_in_terminal({command}), create_file_with_code({folder_path,filename,code})
files_ — read_text({path}), write_text({path,content}), append_text, read_lines, find_by_name
clipboard_ — read, write({text})` :
                                        `
CATEGORIES (prefix_action format — LibreOffice Writer on Linux):
word_ — open, new_document, write({text}), save({filename}), heading_1/2/3, bold, italic, underline, bullet_list, read_content, write_formatted_document({title,sections}), clear_all, find, find_replace, new_line, normal_text, move_to_end, move_to_start, center_text, left_text, right_text, justify, copy, paste, cut, undo, redo, select_all, increase_font, decrease_font, single_space, double_space, strikethrough, toggle_case, upper_case, indent, outdent, page_break, line_break, paste_plain, print, close, ordered_list, superscript, subscript, double_underline, spelling, thesaurus
chrome_ — open, new_tab({url}), navigate({url}), close_tab, scroll_down/up, find({text})
youtube_ — open({query}), play_pause, mute, fullscreen
vscode_ — open, open_folder({path}), new_file, write_code({code}), run_code
files_ — read_text({path}), write_text({path,content}), find_by_name
clipboard_ — read, write({text})`
                                }`,
                            parameters: {
                                type: "OBJECT",
                                properties: {
                                    action: { type: "STRING", description: "Action name (e.g. 'word_write', 'vscode_open_folder', 'finder_list_folder', 'notes_create')" },
                                    args: { type: "OBJECT", description: "Arguments object for the action. Each action has different args — see description above. Pass {} for no-arg actions." }
                                },
                                required: ["action"]
                            }
                        },
                        {
                            name: "send_whatsapp_message",
                            description: "Send a WhatsApp message. Looks up saved contacts for phone number, then uses wa.me deep link (~3s). Contact must be saved first.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    name: { type: "STRING", description: "Contact name in ENGLISH/Latin only." },
                                    message: { type: "STRING", description: "Message to send (any language)" }
                                }, required: ["name", "message"]
                            }
                        },
                        {
                            name: "save_contact",
                            description: "Save a contact for WhatsApp. ALWAYS ask user for phone WITH country code (+880...).",
                            parameters: {
                                type: "OBJECT", properties: {
                                    name: { type: "STRING", description: "Contact name in ENGLISH/Latin only." },
                                    phone: { type: "STRING", description: "Phone WITH country code. MUST start with +." }
                                }, required: ["name", "phone"]
                            }
                        },
                        {
                            name: "read_whatsapp_messages",
                            description: "Read recent messages from a WhatsApp chat. Opens chat, takes screenshot, AI reads messages.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    name: { type: "STRING", description: "Contact name in ENGLISH/Latin only." }
                                }, required: ["name"]
                            }
                        },
                        {
                            name: "check_whatsapp_messages",
                            description: "Check WhatsApp for unread messages. Takes screenshot and detects unread badges.",
                            parameters: { type: "OBJECT", properties: {} }
                        },
                        {
                            name: "find_and_click",
                            description: "AI vision: takes screenshot, sees screen, performs any described action. Use for complex visual tasks only.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    description: { type: "STRING", description: "What to do on screen." }
                                }, required: ["description"]
                            }
                        },
                        {
                            name: "scroll",
                            description: "Scroll the screen up or down.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    direction: { type: "STRING", description: "'up' or 'down'" },
                                    amount: { type: "INTEGER", description: "Scroll clicks (default 5, use 10-20 for big scrolls)" }
                                }, required: ["direction"]
                            }
                        },
                        {
                            name: "press_key",
                            description: "Press a keyboard key: enter, escape, tab, space, backspace, delete, arrows, home, end, pageup, pagedown, f1-f12.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    key: { type: "STRING", description: "Key to press" },
                                    times: { type: "INTEGER", description: "How many times (default 1)" }
                                }, required: ["key"]
                            }
                        },
                        {
                            name: "hotkey",
                            description: "Press keyboard shortcut. Examples: 'command+c', 'command+v', 'command+z', 'command+t', 'command+shift+t'.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    keys: { type: "STRING", description: "Keys joined by +. e.g. 'command+c'" }
                                }, required: ["keys"]
                            }
                        },
                        {
                            name: "type_text",
                            description: "Type text using keyboard. Any language. Set press_enter=true to submit.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    text: { type: "STRING", description: "Text to type" },
                                    press_enter: { type: "BOOLEAN", description: "Press Enter after (default false)" }
                                }, required: ["text"]
                            }
                        },
                        {
                            name: "click_screen",
                            description: "Click at pixel coordinates. Use with take_screenshot.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    x: { type: "INTEGER", description: "X pixel coordinate" },
                                    y: { type: "INTEGER", description: "Y pixel coordinate" }
                                }, required: ["x", "y"]
                            }
                        },
                        {
                            name: "double_click_screen",
                            description: "Double-click at pixel coordinates.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    x: { type: "INTEGER", description: "X pixel" },
                                    y: { type: "INTEGER", description: "Y pixel" }
                                }, required: ["x", "y"]
                            }
                        },
                        {
                            name: "right_click_screen",
                            description: "Right-click at pixel coordinates.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    x: { type: "INTEGER", description: "X pixel" },
                                    y: { type: "INTEGER", description: "Y pixel" }
                                }, required: ["x", "y"]
                            }
                        },
                        {
                            name: "drag",
                            description: "Drag from one point to another.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    from_x: { type: "INTEGER" }, from_y: { type: "INTEGER" },
                                    to_x: { type: "INTEGER" }, to_y: { type: "INTEGER" }
                                }, required: ["from_x", "from_y", "to_x", "to_y"]
                            }
                        },
                        {
                            name: "play_youtube",
                            description: "Opens YouTube and plays a video. ALWAYS use for YouTube.",
                            parameters: { type: "OBJECT", properties: { query: { type: "STRING", description: "YouTube search query" } }, required: ["query"] }
                        },
                        {
                            name: "execute_computer_task",
                            description: "SLOW FALLBACK — only when desktop_automation, find_and_click, and other tools cannot handle the task.",
                            parameters: { type: "OBJECT", properties: { goal: { type: "STRING", description: "Step-by-step goal" } }, required: ["goal"] }
                        },
                        {
                            name: "cancel_task",
                            description: "Cancel a running computer task. Use when user says 'stop', 'cancel', 'never mind', 'ata thak', 'bad de'.",
                            parameters: { type: "OBJECT", properties: {} }
                        },
                        {
                            name: "take_screenshot",
                            description: "Capture screenshot to see the user's screen.",
                            parameters: { type: "OBJECT", properties: {} }
                        },
                        {
                            name: "add_task",
                            description: "Add a recurring/scheduled task.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    name: { type: "STRING", description: "Task name" },
                                    schedule: { type: "STRING", description: "Schedule: 'daily', 'every morning', 'hourly'" }
                                }, required: ["name"]
                            }
                        },
                        {
                            name: "remove_task",
                            description: "Remove a task by index.",
                            parameters: { type: "OBJECT", properties: { index: { type: "INTEGER", description: "Task index (0-based)" } }, required: ["index"] }
                        },
                        {
                            name: "brightness_control",
                            description: "Control screen brightness: up or down.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    action: { type: "STRING", description: "'up' or 'down'" },
                                    amount: { type: "INTEGER", description: "Amount 0-100, default 10" }
                                }, required: ["action"]
                            }
                        },
                        {
                            name: "dismiss_genie",
                            description: "Dismiss genie back to lamp. Use when user says 'go to lamp', 'dismiss', 'goodbye'. Before dismissing, save a session summary.",
                            parameters: { type: "OBJECT", properties: {} }
                        },
                        {
                            name: "remember_user_fact",
                            description: "Save a fact about the user (name, preference, shorthand, project, etc.). Persists across sessions. Use when you learn something new about the user.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    key: { type: "STRING", description: "Fact key, e.g. 'name', 'favorite_editor', 'project_phoenix', 'nickname_todd'" },
                                    value: { type: "STRING", description: "Fact value, e.g. 'Abu Bokkor', 'VS Code', 'Database migration project'" }
                                }, required: ["key", "value"]
                            }
                        },
                        {
                            name: "save_session_summary",
                            description: "Save a brief summary of what was accomplished in this session. Call before dismiss_genie.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    summary: { type: "STRING", description: "1-2 sentence summary of the session" }
                                }, required: ["summary"]
                            }
                        },
                        {
                            name: "toggle_screen_share",
                            description: "Toggle continuous screen sharing ON or OFF. When ON, the user's screen is streamed to you at ~1 FPS so you can see what they're doing in real-time. Note: audio+video sessions are limited to ~2 minutes.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    enabled: { type: "BOOLEAN", description: "true to start, false to stop" }
                                }, required: ["enabled"]
                            }
                        },
                        {
                            name: "toggle_webcam",
                            description: "Toggle the user's webcam ON or OFF. When ON, the webcam feed is streamed to you at ~1 FPS so you can see the user. Note: audio+video sessions are limited to ~2 minutes.",
                            parameters: {
                                type: "OBJECT", properties: {
                                    enabled: { type: "BOOLEAN", description: "true to start, false to stop" }
                                }, required: ["enabled"]
                            }
                        },
                        {
                            name: "analyze_file",
                            description: `Analyze any file on the user's computer using AI vision/understanding. Supports: images (jpg, png, gif, webp), PDFs, text files, CSV, JSON, HTML, XML. Use this when the user asks to analyze, describe, summarize, or extract information from a file. Returns detailed analysis text. For scanned PDFs and images, uses AI vision. For text files, reads and analyzes content.`,
                            parameters: {
                                type: "OBJECT", properties: {
                                    path: { type: "STRING", description: "Full file path (supports ~). Examples: '~/Desktop/report.pdf', '~/Documents/photo.jpg'" },
                                    question: { type: "STRING", description: "What to analyze or ask about the file. Default: general analysis." }
                                }, required: ["path"]
                            }
                        },
                        {
                            name: "remove_background",
                            description: `Remove background from images using AI. Produces transparent PNG. Modes: 'single' for one image, 'batch' for multiple image paths, 'folder' for all images in a folder. Cross-platform (Windows/macOS/Linux).`,
                            parameters: {
                                type: "OBJECT", properties: {
                                    mode: { type: "STRING", description: "'single' (one file), 'batch' (list of files), 'folder' (all images in folder)" },
                                    path: { type: "STRING", description: "For single: image path. For folder: folder path. Supports ~." },
                                    paths: { type: "ARRAY", items: { type: "STRING" }, description: "For batch: array of image paths." },
                                    output_path: { type: "STRING", description: "Optional output path for single mode." },
                                    output_folder: { type: "STRING", description: "Optional output folder for folder mode." }
                                }, required: ["mode"]
                            }
                        },
                        {
                            name: "generate_content",
                            description: `Generate long-form content using a collaborator AI model. Use for: CVs/resumes, essays, reports, letters, code files, business plans, emails, study notes, translations, creative writing, structured documents. Returns the full generated text. IMPORTANT: set destination parameter to control where content goes. destination="word" auto-writes to Word (DEFAULT for documents/CVs/essays). destination="return" just returns text for YOU to send via WhatsApp/email/etc. When user is in a WhatsApp/email conversation and asks for content → use destination="return", then send the text yourself.`,
                            parameters: {
                                type: "OBJECT", properties: {
                                    prompt: { type: "STRING", description: "Detailed instructions for content generation. Include user context, requirements, format, length, and style." },
                                    system_instruction: { type: "STRING", description: "Optional role/style instruction. E.g. 'You are a professional CV writer' or 'Write in academic tone'" },
                                    destination: { type: "STRING", description: "Where to put the content. 'word' = auto-write to Word (default for documents). 'return' = just return text (use when sending via WhatsApp/email/chat). Default: 'word'" }
                                }, required: ["prompt"]
                            }
                        },
                        {
                            name: "create_presentation",
                            description: `Create a professional PowerPoint (.pptx) presentation file. Gemini AI designs beautiful slides with colors, shapes, layouts, charts, tables, and embedded images — then builds a real .pptx file saved to Desktop. User can provide: a text/PDF file to use as content source, and/or an images folder to embed. IMPORTANT: Include ALL details the user mentioned.`,
                            parameters: {
                                type: "OBJECT", properties: {
                                    prompt: { type: "STRING", description: "Detailed instructions: topic, audience, slide count, specific content to include, style preference." },
                                    content_file: { type: "STRING", description: "Optional path to a text/PDF file whose content should be used for the slides. E.g. '~/Desktop/thesis.txt'" },
                                    images_folder: { type: "STRING", description: "Optional path to a folder of images to embed in slides. E.g. '~/Desktop/figures'" },
                                    image_files: { type: "ARRAY", items: { type: "STRING" }, description: "Optional array of specific image file paths to embed. E.g. ['~/Desktop/chart.png', '~/Desktop/logo.png']" },
                                    filename: { type: "STRING", description: "Output filename (no extension). Default: 'Presentation'" },
                                    style: { type: "STRING", description: "'professional', 'creative', 'minimal', 'academic'. Default: 'professional'" }
                                }, required: ["prompt"]
                            }
                        },
                        {
                            name: "transcribe_audio",
                            description: `Transcribe audio or video files to text using Gemini AI. Supports: MP3, WAV, M4A, OGG, FLAC, AAC, WebM, MP4, MOV. Use when user asks to transcribe, convert audio to text, get text from recording, or extract speech from video. Returns full transcription text.`,
                            parameters: {
                                type: "OBJECT", properties: {
                                    path: { type: "STRING", description: "Full file path (supports ~). Examples: '~/Desktop/recording.mp3', '~/Downloads/lecture.m4a'" },
                                    language: { type: "STRING", description: "Optional language hint. E.g. 'English', 'Bengali', 'Spanish'" },
                                    save_to_file: { type: "BOOLEAN", description: "Save transcription to a .txt file next to the audio. Default: true" }
                                }, required: ["path"]
                            }
                        }
                    ]
                }],

            onToolCall: async (toolCall) => {
                const responses = [];
                // Track destructive actions already executed in this batch to prevent duplicates
                // The Gemini model sometimes sends the same tool call twice (e.g. gmail_reply x2)
                const executedDestructiveActions = new Set();
                const DESTRUCTIVE_GMAIL_ACTIONS = [
                    'gmail_reply', 'gmail_reply_all', 'gmail_forward', 'gmail_send',
                    'gmail_compose', 'gmail_delete', 'gmail_archive', 'gmail_spam'
                ];

                for (const call of toolCall.functionCalls || []) {
                    let result;

                    // Dedup: skip duplicate destructive Gmail actions in the same batch
                    if (call.name === 'desktop_automation' && call.args?.action) {
                        const macAction = call.args.action;
                        if (DESTRUCTIVE_GMAIL_ACTIONS.includes(macAction)) {
                            if (executedDestructiveActions.has(macAction)) {
                                console.log(`⚠️ Skipping duplicate ${macAction} — already executed in this batch`);
                                result = { success: true, skipped: true, message: `${macAction} already executed. Skipping duplicate.` };
                                responses.push({ id: call.id, name: call.name, response: { output: result } });
                                continue;
                            }
                            executedDestructiveActions.add(macAction);
                        }
                    }

                    // Block ALL tool calls during greeting grace period (first 10s after session start)
                    // This prevents the model from auto-executing volume/screenshot/etc during its introduction
                    if (sessionStartTime > 0 && (Date.now() - sessionStartTime) < GREETING_GRACE_MS) {
                        console.log(`⏳ Greeting grace period: blocking tool call "${call.name}" (${Math.round((Date.now() - sessionStartTime) / 1000)}s after start)`);
                        result = { success: false, error: 'Session just started. Do NOT call any tools during your greeting. Just introduce yourself with speech only. Wait for the user to ask before using tools.' };
                        responses.push({ id: call.id, name: call.name, response: { output: result } });
                        continue;
                    }

                    const slowTools = ['desktop_automation', 'execute_computer_task', 'find_and_click',
                        'send_whatsapp_message', 'read_whatsapp_messages', 'check_whatsapp_messages',
                        'play_youtube', 'analyze_file', 'generate_content', 'remove_background',
                        'create_presentation', 'transcribe_audio'];
                    if (slowTools.includes(call.name) && isTaskRunning) {
                        result = { success: false, error: 'Another task is already running. Wait for it to finish or say "cancel" to stop it.' };
                        responses.push({ id: call.id, name: call.name, response: { output: result } });
                        continue;
                    }
                    try {
                        switch (call.name) {
                            case 'open_app':
                                setGenieState('acting');
                                showSpeech('🚀 Opening ' + call.args.app_name, 3000);
                                window.wishcraft.executeAction({ action: 'open_app', app_name: call.args.app_name });
                                result = { success: true, message: 'Opened ' + call.args.app_name };
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: 'Opened ' + call.args.app_name });
                                break;
                            case 'close_app':
                                setGenieState('acting');
                                showSpeech('🔴 Closing ' + call.args.app_name, 3000);
                                window.wishcraft.executeAction({ action: 'close_app', app_name: call.args.app_name });
                                result = { success: true, message: 'Closed ' + call.args.app_name };
                                setGenieState('complete');
                                break;
                            case 'open_url':
                                window.wishcraft.executeAction({ action: 'open_url', url: call.args.url });
                                result = { success: true, message: 'Opened ' + call.args.url };
                                break;
                            case 'search_web':
                                showSpeech('🔍 Searching: ' + call.args.query, 3000);
                                window.wishcraft.executeAction({ action: 'search_web', query: call.args.query });
                                result = { success: true, message: 'Searched: ' + call.args.query };
                                break;
                            case 'volume_control':
                                window.wishcraft.executeAction({ action: 'volume_' + call.args.action, amount: call.args.amount || 10 });
                                result = { success: true, message: 'Volume ' + call.args.action };
                                break;
                            case 'brightness_control':
                                window.wishcraft.executeAction({ action: 'brightness_' + call.args.action, amount: call.args.amount || 10 });
                                result = { success: true, message: 'Brightness ' + call.args.action };
                                break;
                            case 'dismiss_genie':
                                result = { success: true, message: 'Genie dismissed' };
                                // Delay to let farewell speech play
                                setTimeout(() => {
                                    showSpeech('Until next time! 💫', 1500);
                                    smokeSystem.dismiss(() => { });
                                    setTimeout(() => { setGenieState('dismissed'); stopLiveSession(); }, 600);
                                }, 2000);
                                break;
                            case 'run_command':
                                setGenieState('acting');
                                window.wishcraft.executeAction({ action: 'run_command', command: call.args.command });
                                result = { success: true, message: 'Command executed' };
                                setGenieState('complete');
                                break;

                            case 'desktop_automation': {
                                setGenieState('acting');
                                const macAction = call.args.action || '';
                                const macArgs = call.args.args || {};
                                const localActions = ['toggle_screen_share', 'toggle_webcam', 'dismiss_genie'];
                                if (localActions.includes(macAction)) {
                                    call.name = macAction;
                                    call.args = { ...macArgs };
                                    // Re-dispatch by restarting the switch via a recursive call pattern
                                    // Simpler: just handle toggle_screen_share inline
                                    if (macAction === 'toggle_screen_share') {
                                        const enabled = macArgs.enabled !== false;
                                        if (enabled && !isScreenSharing && liveChatController) {
                                            liveChatController.startScreenShare(1);
                                            isScreenSharing = true;
                                            showSpeech('🖥️ Screen sharing ON', 3000);
                                            window.wishcraft.sendToPanel({ type: 'screen-share-status', active: true });
                                            result = { success: true, message: 'Screen sharing started.' };
                                        } else if (!enabled) {
                                            if (isScreenSharing && liveChatController) { liveChatController.stopScreenShare(); isScreenSharing = false; }
                                            showSpeech('🖥️ Screen sharing OFF', 3000);
                                            window.wishcraft.sendToPanel({ type: 'screen-share-status', active: false });
                                            result = { success: true, message: 'Screen sharing stopped.' };
                                        } else {
                                            result = { success: true, message: 'Screen sharing is already active.' };
                                        }
                                    } else if (macAction === 'toggle_webcam') {
                                        const enabled = macArgs.enabled !== false;
                                        if (enabled && !isWebcamActive && liveChatController) {
                                            liveChatController.startWebcam(1);
                                            isWebcamActive = true;
                                            showSpeech('📷 Webcam ON', 3000);
                                            result = { success: true, message: 'Webcam started.' };
                                        } else if (!enabled) {
                                            if (isWebcamActive && liveChatController) { liveChatController.stopWebcam(); isWebcamActive = false; }
                                            showSpeech('📷 Webcam OFF', 3000);
                                            result = { success: true, message: 'Webcam stopped.' };
                                        } else {
                                            result = { success: true, message: 'Webcam is already active.' };
                                        }
                                    } else if (macAction === 'dismiss_genie') {
                                        stopLiveSession(true);
                                        result = { success: true, message: 'Dismissed.' };
                                    }
                                    setGenieState('complete');
                                    break;
                                }
                                showSpeech('⚡ ' + macAction.replace(/_/g, ' '), 8000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: macAction });
                                const macPayload = { action: macAction, ...macArgs };
                                const macTimeout = macAction.startsWith('word_write_formatted') ? 60000 :
                                    macAction.startsWith('vscode_create_file') ? 30000 :
                                        macAction.startsWith('excel_create') ? 45000 :
                                            macAction.startsWith('numbers_create') ? 45000 : 30000;
                                isTaskRunning = true;
                                result = await waitForPythonAction(macPayload, macTimeout);
                                isTaskRunning = false;
                                if (result.summary && !result.message) result.message = result.summary;

                                // Auto-escalate to Computer Use if desktop_automation fails
                                if (!result.success && result.error && !macAction.startsWith('gmail_get_state') && !macAction.startsWith('gmail_ensure_list')) {
                                    const failReason = result.error || 'unknown error';
                                    console.log('🔄 desktop_automation(' + macAction + ') failed: ' + failReason + ', escalating to Computer Use...');
                                    showSpeech('🔄 Trying another approach...', 8000);
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚠️ ' + macAction.replace(/_/g, ' ') + ' failed: ' + failReason });
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '🔄 Switching to visual computer agent...' });
                                    isTaskRunning = true;
                                    const cuGoal = macAction.replace(/_/g, ' ') + (macArgs.to ? ' to ' + macArgs.to : '') + (macArgs.query ? ': ' + macArgs.query : '') + (macArgs.text ? ': ' + macArgs.text.substring(0, 100) : '');
                                    result = await executeComputerTask(cuGoal);
                                    isTaskRunning = false;
                                    if (result.summary && !result.message) result.message = result.summary;
                                    result.escalated = true;
                                    result.original_error = failReason;
                                    if (result.success) {
                                        result.SPEAK_THIS = 'I ran into a small issue with the quick method, so I switched to the visual computer agent. It worked! ' + (result.summary ? 'Here is what happened: ' + result.summary.substring(0, 800) : 'The task was completed successfully.');
                                    } else {
                                        result.SPEAK_THIS = 'I tried two different approaches but both had issues. The error was: ' + failReason + '. ' + (result.error || 'Please try again or let me know how to help.');
                                    }
                                }

                                // For email/inbox reads: send full data to panel, summarize for voice
                                if (macAction === 'mail_list_inbox') {
                                    if (result.messages && result.messages.length > 0) {
                                        const panelHtml = result.messages.map(m => typeof m === 'string' ? m : JSON.stringify(m)).join('\n\n');
                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: '📧 Inbox (' + result.count + ' emails):\n\n' + panelHtml });
                                        const unread = result.messages.filter(m => typeof m === 'string' && m.includes('[UNREAD]'));
                                        const starred = result.messages.filter(m => typeof m === 'string' && m.includes('[STARRED]'));
                                        const important = result.messages.filter(m => typeof m === 'string' && m.includes('[IMPORTANT]'));
                                        // Top 5 unread summaries
                                        const topUnread = unread.slice(0, 5).map(m => {
                                            const fromMatch = m.match(/From:\s*([^|]+)/);
                                            const subjMatch = m.match(/Subject:\s*([^|]+)/);
                                            return (fromMatch ? fromMatch[1].trim() : '') + (subjMatch ? ': ' + subjMatch[1].trim() : '');
                                        });
                                        // Important/starred summaries
                                        const topImportant = important.concat(starred).slice(0, 3).map(m => {
                                            const fromMatch = m.match(/From:\s*([^|]+)/);
                                            const subjMatch = m.match(/Subject:\s*([^|]+)/);
                                            return (fromMatch ? fromMatch[1].trim() : '') + (subjMatch ? ': ' + subjMatch[1].trim() : '');
                                        });
                                        let voiceSummary = `You have ${result.count} emails, ${result.unread_count || unread.length} unread`;
                                        if (result.starred_count || starred.length) voiceSummary += `, ${result.starred_count || starred.length} starred`;
                                        if (result.important_count || important.length) voiceSummary += `, ${result.important_count || important.length} important`;
                                        voiceSummary += '.';
                                        if (topImportant.length > 0) voiceSummary += ` Important emails: ${topImportant.join('; ')}.`;
                                        if (topUnread.length > 0) voiceSummary += ` Top unread: ${topUnread.join('; ')}.`;
                                        voiceSummary += ' Full details are shown in the panel. Summarize briefly for the user, mentioning important or starred emails first.';
                                        result = {
                                            success: true,
                                            count: result.count,
                                            unread_count: result.unread_count || unread.length,
                                            starred_count: result.starred_count || starred.length,
                                            important_count: result.important_count || important.length,
                                            SPEAK_THIS: voiceSummary
                                        };
                                    }
                                } else if (macAction === 'gmail_read_email' || macAction === 'mail_read_message') {
                                    if (result.content) {
                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: '📧 Email:\n\n' + result.content });
                                        // Truncate for Live API
                                        result = {
                                            success: true,
                                            SPEAK_THIS: 'Email content (summarize for user): ' + result.content.substring(0, 800)
                                        };
                                    }
                                } else if (macAction.startsWith('gmail_') || macAction.startsWith('mail_')) {
                                    // Show detailed result for all other Gmail/Mail actions in the panel
                                    let panelText = '';
                                    if (macAction === 'gmail_unread_count') {
                                        panelText = '📬 Unread: ' + (result.unread_count != null ? result.unread_count : 'unknown');
                                    } else if (macAction === 'gmail_compose') {
                                        panelText = '✉️ Compose → To: ' + (result.to || '?') + ' | Subject: ' + (result.subject || '?') + (result.sent ? ' | Sent ✅' : ' | Draft (review)');
                                    } else if (macAction === 'gmail_reply') {
                                        panelText = '↩️ Reply' + (result.sent ? ' sent ✅' : ' drafted');
                                        if (result.send_confirmed) panelText += ' (confirmed)';
                                    } else if (macAction === 'gmail_reply_all') {
                                        panelText = '↩️ Reply All' + (result.sent ? ' sent ✅' : ' drafted');
                                        if (result.send_confirmed) panelText += ' (confirmed)';
                                    } else if (macAction === 'gmail_forward') {
                                        panelText = '➡️ Forward → ' + (result.to || '?') + (result.sent ? ' sent ✅' : ' drafted');
                                        if (result.send_confirmed) panelText += ' (confirmed)';
                                    } else if (macAction === 'gmail_send') {
                                        panelText = '📤 Send' + (result.send_confirmed ? ' ✅ confirmed' : '');
                                    } else if (macAction === 'gmail_archive') {
                                        panelText = '📦 Archived';
                                    } else if (macAction === 'gmail_delete') {
                                        panelText = '🗑️ Deleted';
                                    } else if (macAction === 'gmail_star') {
                                        panelText = '⭐ Star toggled';
                                    } else if (macAction === 'gmail_mark_read') {
                                        panelText = '📖 Marked as read';
                                    } else if (macAction === 'gmail_mark_unread') {
                                        panelText = '📩 Marked as unread';
                                    } else if (macAction === 'gmail_mark_important') {
                                        panelText = '❗ Marked important';
                                    } else if (macAction === 'gmail_search') {
                                        panelText = '🔍 Search: ' + (macArgs.query || '?');
                                    } else if (macAction === 'gmail_get_state') {
                                        panelText = '📋 Gmail view: ' + (result.view || 'unknown');
                                    } else if (macAction === 'gmail_ensure_list_view') {
                                        panelText = '📋 Reset to list (' + (result.action || 'done') + ')';
                                    } else if (macAction === 'gmail_open') {
                                        panelText = '🌐 Gmail opened';
                                    } else if (macAction === 'gmail_open_email') {
                                        panelText = '📧 Email opened';
                                    } else if (macAction === 'gmail_back_to_list') {
                                        panelText = '⬅️ Back to inbox';
                                    } else if (macAction === 'gmail_next' || macAction === 'gmail_prev') {
                                        panelText = macAction === 'gmail_next' ? '⬇️ Next email' : '⬆️ Previous email';
                                    } else if (macAction === 'gmail_go_inbox') {
                                        panelText = '📥 Inbox';
                                    } else if (macAction === 'gmail_go_sent') {
                                        panelText = '📤 Sent folder';
                                    } else if (macAction === 'gmail_go_drafts') {
                                        panelText = '📝 Drafts folder';
                                    } else if (macAction === 'gmail_go_starred') {
                                        panelText = '⭐ Starred folder';
                                    } else if (macAction === 'gmail_go_all_mail') {
                                        panelText = '📬 All Mail';
                                    } else if (macAction === 'gmail_refresh') {
                                        panelText = '🔄 Refreshed';
                                    } else {
                                        panelText = macAction.replace(/_/g, ' ') + (result.success ? ' ✅' : ' ❌');
                                    }
                                    if (!result.success && result.error) panelText += ' | Error: ' + result.error;
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: panelText });
                                }

                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error || 'Done' });
                                break;
                            }

                            case 'send_whatsapp_message': {
                                setGenieState('acting');
                                showSpeech('📱 Messaging ' + call.args.name + '...', 60000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Messaging ' + call.args.name });
                                // Look up contact for phone number
                                const contact = await window.wishcraft.findContact(call.args.name);
                                const phone = contact ? contact.phone : '';
                                isTaskRunning = true;
                                result = await waitForPythonAction({
                                    action: 'whatsapp_send',
                                    name: call.args.name,
                                    phone: phone,
                                    message: call.args.message
                                }, 60000);
                                if (result.needs_login) {
                                    result.message = 'WhatsApp needs login. Please scan the QR code and try again.';
                                }
                                if (result.summary && !result.message) result.message = result.summary;
                                if (result.screenshot) {
                                    delete result.screenshot;
                                }
                                isTaskRunning = false;
                                // Auto-escalate to Computer Use if WhatsApp send fails
                                if (!result.success && !result.needs_login) {
                                    console.log('🔄 whatsapp_send failed, escalating to Computer Use...');
                                    showSpeech('🔄 Trying another approach...', 8000);
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚠️ WhatsApp send failed: ' + (result.error || result.message || 'unknown') });
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '🔄 Switching to visual computer agent...' });
                                    isTaskRunning = true;
                                    result = await executeComputerTask('Send WhatsApp message to ' + call.args.name + ': ' + call.args.message);
                                    isTaskRunning = false;
                                    if (result.summary && !result.message) result.message = result.summary;
                                    result.escalated = true;
                                    if (result.success) {
                                        result.SPEAK_THIS = 'I had a small issue with the quick method, so I used the visual agent to send the message. It worked!';
                                    } else {
                                        result.SPEAK_THIS = 'I tried two approaches but could not send the WhatsApp message. ' + (result.error || 'Please try again.');
                                    }
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error || 'Done' });
                                break;
                            }
                            case 'save_contact': {
                                setGenieState('acting');
                                showSpeech('💾 Saving contact: ' + call.args.name, 3000);
                                const saveResult = await window.wishcraft.addContact(call.args.name, call.args.phone);
                                result = saveResult;
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || 'Contact saved' });
                                break;
                            }
                            case 'read_whatsapp_messages': {
                                setGenieState('acting');
                                showSpeech('📖 Reading messages from ' + call.args.name + '...', 30000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Reading messages from ' + call.args.name });
                                const readContact = await window.wishcraft.findContact(call.args.name);
                                const readPhone = readContact ? readContact.phone : '';
                                result = await waitForPythonAction({
                                    action: 'whatsapp_read',
                                    name: call.args.name,
                                    phone: readPhone,
                                    num_messages: 10
                                }, 30000);
                                if (result.summary && !result.message) result.message = result.summary;
                                if (result.screenshot) { delete result.screenshot; }
                                // Auto-escalate to Computer Use if WhatsApp read fails
                                if (!result.success) {
                                    console.log('🔄 whatsapp_read failed, escalating to Computer Use...');
                                    showSpeech('🔄 Trying another approach...', 8000);
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚠️ Read failed → switching to visual agent...' });
                                    isTaskRunning = true;
                                    result = await executeComputerTask('Read WhatsApp messages from ' + call.args.name);
                                    isTaskRunning = false;
                                    if (result.summary && !result.message) result.message = result.summary;
                                    result.escalated = true;
                                    if (result.summary) {
                                        result.SPEAK_THIS = 'I used the visual agent to read the messages. Here is what I found: ' + result.summary.substring(0, 800);
                                    }
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.summary || 'Done' });
                                break;
                            }
                            case 'check_whatsapp_messages': {
                                setGenieState('acting');
                                showSpeech('🔔 Checking WhatsApp...', 15000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Checking WhatsApp messages' });
                                isTaskRunning = true;
                                result = await waitForPythonAction({
                                    action: 'whatsapp_check_unread'
                                }, 20000);
                                isTaskRunning = false;
                                if (!result.message) {
                                    if (result.has_unread && result.unread_chats) {
                                        const names = result.unread_chats.map(c => c.name + ' (' + c.unread_count + ')').join(', ');
                                        result.message = 'Unread messages from: ' + names;
                                    } else {
                                        result.message = 'No unread messages';
                                    }
                                }
                                if (result.screenshot) {
                                    delete result.screenshot; // Don't send huge base64 — structured unread data is sufficient
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message });
                                break;
                            }

                            case 'find_and_click':
                                setGenieState('acting');
                                showSpeech('👁️ ' + call.args.description, 30000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: call.args.description });
                                isTaskRunning = true;
                                result = await waitForPythonAction({
                                    action: 'find_and_click',
                                    description: call.args.description
                                }, 30000);
                                isTaskRunning = false;
                                // Auto-escalate to computer agent if find_and_click fails
                                if (!result.found) {
                                    console.log('🔄 find_and_click failed, escalating to execute_computer_task...');
                                    showSpeech('🔄 Trying another approach...', 8000);
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚠️ Could not find: ' + call.args.description });
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '🔄 Switching to visual computer agent...' });
                                    isTaskRunning = true;
                                    result = await executeComputerTask(call.args.description);
                                    isTaskRunning = false;
                                    if (result.summary && !result.message) result.message = result.summary;
                                    result.escalated = true;
                                    if (result.summary && result.summary.length > 50) {
                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: '🖱️ Computer Use Report:\n\n' + result.summary });
                                    }
                                    if (result.success) {
                                        result.found = true; // Mark as found so panel shows 'Done!'
                                        result.SPEAK_THIS = 'I had a small issue finding it directly, so I switched to the visual agent. ' + (result.summary ? 'Here is what happened: ' + result.summary.substring(0, 800) : 'The task was completed successfully.');
                                    } else {
                                        result.SPEAK_THIS = 'I tried two different approaches but could not complete the task. ' + (result.error || 'Please try again or describe what you need differently.');
                                    }
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || (result.found ? 'Done!' : 'Not found') });
                                break;

                            case 'scroll':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'scroll',
                                    direction: call.args.direction || 'down',
                                    magnitude: call.args.amount || 5
                                }, 5000);
                                break;

                            case 'press_key':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'press',
                                    key: call.args.key,
                                    times: call.args.times || 1
                                }, 5000);
                                break;

                            case 'hotkey':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'hotkey',
                                    keys: call.args.keys
                                }, 5000);
                                break;

                            case 'type_text':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'type',
                                    text: call.args.text,
                                    press_enter: call.args.press_enter || false
                                }, 10000);
                                break;

                            case 'click_screen':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'click',
                                    x: call.args.x,
                                    y: call.args.y
                                }, 5000);
                                break;

                            case 'double_click_screen':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'double_click',
                                    x: call.args.x,
                                    y: call.args.y
                                }, 5000);
                                break;

                            case 'right_click_screen':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'right_click',
                                    x: call.args.x,
                                    y: call.args.y
                                }, 5000);
                                break;

                            case 'drag':
                                setGenieState('acting');
                                result = await waitForPythonAction({
                                    action: 'drag_and_drop',
                                    x: call.args.from_x,
                                    y: call.args.from_y,
                                    destination_x: call.args.to_x,
                                    destination_y: call.args.to_y
                                }, 10000);
                                break;

                            case 'play_youtube':
                                setGenieState('acting');
                                showSpeech('🎵 Playing: ' + call.args.query, 30000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Playing ' + call.args.query });
                                isTaskRunning = true;
                                result = await waitForPythonAction({
                                    action: 'play_youtube',
                                    query: call.args.query
                                }, 30000);
                                isTaskRunning = false;
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || 'Playing' });
                                break;

                            case 'execute_computer_task':
                                setGenieState('acting');
                                showSpeech('🖱️ ' + call.args.goal, 8000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: call.args.goal });
                                isTaskRunning = true;
                                result = await executeComputerTask(call.args.goal);
                                isTaskRunning = false;
                                if (result.summary && !result.message) result.message = result.summary;
                                // Send the full detailed report to the Chat Panel so user can read it
                                if (result.summary && result.summary.length > 50) {
                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: '🖱️ Computer Use Report:\n\n' + result.summary });
                                }
                                if (result.summary) {
                                    result.SPEAK_THIS = 'The computer agent found these results. You MUST summarize and speak them to the user: ' + result.summary.substring(0, 1000);
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.summary || result.error || 'Done' });
                                break;
                            case 'cancel_task':
                                window.wishcraft.cancelComputerTask();
                                isTaskRunning = false;
                                setGenieState('idle');
                                result = { success: true, message: 'Task cancelled.' };
                                showSpeech('🛑 Cancelled', 2000);
                                break;
                            case 'take_screenshot':
                                const ssData = await window.wishcraft.takeScreenshot();
                                if (ssData) {
                                    window.wishcraft.saveScreenshot(ssData);
                                    window.wishcraft.sendToPanel({ type: 'screenshot', image: ssData });
                                }
                                result = { success: true, message: 'Screenshot saved to Desktop' };
                                break;

                            case 'add_task':
                                taskList.push({ name: call.args.name, schedule: call.args.schedule || 'once', status: 'active', createdAt: Date.now() });
                                saveTasks();
                                result = { success: true, message: 'Task added: ' + call.args.name };
                                window.wishcraft.sendToPanel({ type: 'task-added', task: call.args.name });
                                break;
                            case 'remove_task':
                                const idx = call.args.index;
                                if (idx >= 0 && idx < taskList.length) {
                                    const removed = taskList.splice(idx, 1)[0];
                                    saveTasks();
                                    result = { success: true, message: 'Removed: ' + removed.name };
                                } else {
                                    result = { success: false, error: 'Task not found' };
                                }
                                break;

                            case 'remember_user_fact': {
                                try {
                                    await window.wishcraft.memory.setUserFact(call.args.key, call.args.value);
                                    result = { success: true, message: `Remembered: ${call.args.key} = ${call.args.value}` };
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                break;
                            }
                            case 'save_session_summary': {
                                try {
                                    await window.wishcraft.memory.addHistory(call.args.summary);
                                    result = { success: true, message: 'Session summary saved' };
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                break;
                            }

                            case 'toggle_screen_share': {
                                if (call.args.enabled) {
                                    if (!isScreenSharing && liveChatController) {
                                        liveChatController.startScreenShare(1);
                                        isScreenSharing = true;
                                        showSpeech('🖥️ Screen sharing ON', 3000);
                                        window.wishcraft.sendToPanel({ type: 'screen-share-status', active: true });
                                        result = { success: true, message: 'Screen sharing started at ~1 FPS. I can now see your screen continuously.' };
                                    } else {
                                        result = { success: true, message: 'Screen sharing is already active.' };
                                    }
                                } else {
                                    if (isScreenSharing && liveChatController) {
                                        liveChatController.stopScreenShare();
                                        isScreenSharing = false;
                                        showSpeech('🖥️ Screen sharing OFF', 3000);
                                        window.wishcraft.sendToPanel({ type: 'screen-share-status', active: false });
                                    }
                                    result = { success: true, message: 'Screen sharing stopped.' };
                                }
                                break;
                            }
                            case 'toggle_webcam': {
                                try {
                                    if (call.args.enabled) {
                                        if (!isWebcamActive && liveChatController) {
                                            await liveChatController.startWebcam();
                                            isWebcamActive = true;
                                            showSpeech('📷 Webcam ON', 3000);
                                            window.wishcraft.sendToPanel({ type: 'webcam-status', active: true });
                                            result = { success: true, message: 'Webcam started at ~1 FPS. I can now see you.' };
                                        } else {
                                            result = { success: true, message: 'Webcam is already active.' };
                                        }
                                    } else {
                                        if (isWebcamActive && liveChatController) {
                                            liveChatController.stopWebcam();
                                            isWebcamActive = false;
                                            showSpeech('📷 Webcam OFF', 3000);
                                            window.wishcraft.sendToPanel({ type: 'webcam-status', active: false });
                                        }
                                        result = { success: true, message: 'Webcam stopped.' };
                                    }
                                } catch (e) {
                                    result = { success: false, error: 'Webcam access denied or unavailable: ' + e.message };
                                }
                                break;
                            }

                            case 'analyze_file': {
                                setGenieState('acting');
                                showSpeech('🔍 Analyzing file...', 30000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Analyzing: ' + call.args.path });
                                try {
                                    const fileData = await window.wishcraft.readFileBase64(call.args.path);
                                    if (fileData.error) {
                                        result = { success: false, error: fileData.error };
                                    } else {
                                        if (!collaborator) collaborator = new GeminiCollaborator(CONFIG.apiKey);
                                        const question = call.args.question || 'Analyze this file in detail. Describe what you see and extract all important information.';
                                        const analysis = await collaborator.analyzeFile(fileData.base64, fileData.mimeType, question);
                                        if (analysis.success) {
                                            if (fileData.mimeType.startsWith('image/') && liveChatController) {
                                                liveChatController.sendImage(fileData.base64, fileData.mimeType, 'File: ' + call.args.path);
                                            }
                                            result = { success: true, message: analysis.text };
                                        } else {
                                            result = { success: false, error: analysis.error };
                                        }
                                    }
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error });
                                break;
                            }
                            case 'remove_background': {
                                setGenieState('acting');
                                isTaskRunning = true;
                                const mode = call.args.mode || 'single';
                                showSpeech('🖼️ Removing background...', 120000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: `Removing background (${mode})...` });
                                try {
                                    let action = 'remove_background';
                                    let payload = {};
                                    if (mode === 'batch') {
                                        action = 'remove_background_batch';
                                        payload = { paths: call.args.paths || [] };
                                    } else if (mode === 'folder') {
                                        action = 'remove_background_folder';
                                        payload = { folder: call.args.path || '', output_folder: call.args.output_folder || '' };
                                    } else {
                                        payload = { path: call.args.path || '', output_path: call.args.output_path || '' };
                                    }
                                    const bgResult = await new Promise((resolve) => {
                                        window.wishcraft.executeAction({ action, ...payload });
                                        const handler = (r) => {
                                            if (r.progress) {
                                                window.wishcraft.sendToPanel({ type: 'genie-message', text: '🖼️ ' + r.message });
                                            } else {
                                                resolve(r);
                                            }
                                        };
                                        window.wishcraft.onActionResult(handler);
                                        setTimeout(() => resolve({ success: false, error: 'Timed out (120s)' }), 120000);
                                    });
                                    result = bgResult;
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                isTaskRunning = false;
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error });
                                break;
                            }
                            case 'create_presentation': {
                                setGenieState('acting');
                                isTaskRunning = true;
                                showSpeech('📊 Creating presentation...', 120000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Designing presentation slides...' });
                                try {
                                    if (!collaborator) collaborator = new GeminiCollaborator(CONFIG.apiKey);
                                    const prompt = call.args.prompt || '';
                                    const style = call.args.style || 'professional';
                                    const filename = call.args.filename || 'Presentation';

                                    let contentText = '';
                                    if (call.args.content_file) {
                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: '📄 Reading content file...' });
                                        const contentData = await window.wishcraft.readFileBase64(call.args.content_file);
                                        if (!contentData.error) {
                                            if (contentData.mimeType === 'application/pdf') {
                                                const analysis = await collaborator.analyzeFile(contentData.base64, contentData.mimeType, 'Extract ALL text content from this document. Return the full text organized by sections.');
                                                if (analysis.success) contentText = analysis.text;
                                            } else {
                                                contentText = atob(contentData.base64);
                                            }
                                        }
                                    }

                                    const imageNames = [];
                                    let imagePaths = call.args.image_files || [];
                                    if (call.args.images_folder) {
                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: '🖼️ Scanning images folder...' });
                                        const scanResult = await new Promise(resolve => {
                                            window.wishcraft.executeAction({ action: 'run_command', command: `ls -1 "${call.args.images_folder.replace('~', '$HOME')}" 2>/dev/null | grep -iE '\\.(jpg|jpeg|png|gif|webp|bmp)$'` });
                                            window.wishcraft.onActionResult(r => resolve(r));
                                            setTimeout(() => resolve({ success: false }), 5000);
                                        });
                                        if (scanResult.success && scanResult.output) {
                                            const folder = call.args.images_folder;
                                            const files = scanResult.output.trim().split('\n').filter(f => f);
                                            imagePaths = [...imagePaths, ...files.map(f => `${folder}/${f}`)];
                                        }
                                    }

                                    for (const imgPath of imagePaths) {
                                        const imgData = await window.wishcraft.readFileBase64(imgPath);
                                        if (!imgData.error && imgData.mimeType?.startsWith('image/')) {
                                            const name = imgPath.split('/').pop().replace(/\.[^/.]+$/, '');
                                            imageNames.push({ name, path: imgPath });
                                        }
                                    }

                                    let fullPrompt = prompt;
                                    if (contentText) {
                                        fullPrompt += `\n\n--- SOURCE CONTENT (use this for slide text) ---\n${contentText.substring(0, 30000)}`;
                                    }
                                    if (imageNames.length > 0) {
                                        fullPrompt += `\n\n--- AVAILABLE IMAGES (embed these in slides using type "image") ---\n`;
                                        fullPrompt += imageNames.map((img, i) => `Image ${i}: "${img.name}" → use path: "${img.path}"`).join('\n');
                                        fullPrompt += `\nFor image elements use: { "type": "image", "path": "${imageNames[0].path}", "x": ..., "y": ..., "w": ..., "h": ... }`;
                                    }

                                    window.wishcraft.sendToPanel({ type: 'genie-message', text: `🎨 Gemini is designing slides...${contentText ? ' (with source content)' : ''}${imageNames.length ? ` (${imageNames.length} images)` : ''}` });
                                    const genResult = await collaborator.generateSlides(fullPrompt, style);

                                    if (!genResult.success) {
                                        result = { success: false, error: genResult.error || 'Failed to generate slides' };
                                    } else {
                                        let slidesData;
                                        let text = genResult.text.trim();
                                        if (text.startsWith('```json')) text = text.slice(7);
                                        if (text.startsWith('```')) text = text.slice(3);
                                        if (text.endsWith('```')) text = text.slice(0, -3);
                                        text = text.trim();

                                        try {
                                            slidesData = JSON.parse(text);
                                        } catch (parseErr) {
                                            console.error('PPTX JSON parse error:', parseErr, 'Raw:', text.substring(0, 500));
                                            result = { success: false, error: 'Failed to parse slide design. Please try again.' };
                                            break;
                                        }

                                        window.wishcraft.sendToPanel({ type: 'genie-message', text: `📄 Building ${slidesData.slides?.length || 0} slides...` });
                                        const pptxResult = await window.wishcraft.createPptx(slidesData, filename);

                                        if (pptxResult.success) {
                                            window.wishcraft.executeAction({ action: 'run_command', command: `open "${pptxResult.path}"` });
                                            result = { success: true, message: `Presentation created: ${filename}.pptx with ${slidesData.slides?.length || 0} slides. Saved to Desktop and opened.` };
                                        } else {
                                            result = { success: false, error: pptxResult.error || 'Failed to build PPTX file' };
                                        }
                                    }
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                isTaskRunning = false;
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error });
                                break;
                            }
                            case 'transcribe_audio': {
                                setGenieState('acting');
                                isTaskRunning = true;
                                showSpeech('🎤 Transcribing audio...', 120000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Transcribing: ' + call.args.path });
                                try {
                                    const fileData = await window.wishcraft.readFileBase64(call.args.path);
                                    if (fileData.error) {
                                        result = { success: false, error: fileData.error };
                                    } else {
                                        if (!collaborator) collaborator = new GeminiCollaborator(CONFIG.apiKey);
                                        const language = call.args.language || '';
                                        const transcription = await collaborator.transcribeAudio(fileData.base64, fileData.mimeType, language);

                                        if (transcription.success) {
                                            const saveToFile = call.args.save_to_file !== false;
                                            let savedPath = '';
                                            if (saveToFile) {
                                                const basePath = call.args.path.replace(/\.[^/.]+$/, '') + '_transcription.txt';
                                                window.wishcraft.executeAction({ action: 'run_command', command: `cat > "${basePath}" << 'TRANSCRIPTION_EOF'\n${transcription.text}\nTRANSCRIPTION_EOF` });
                                                savedPath = basePath;
                                            }
                                            const summary = transcription.text.length > 300 ? transcription.text.substring(0, 300) + '...' : transcription.text;
                                            result = { success: true, message: `Transcription complete (${transcription.text.length} chars).${savedPath ? ' Saved to: ' + savedPath : ''}\n\nPreview: ${summary}`, full_text: transcription.text };
                                        } else {
                                            result = { success: false, error: transcription.error };
                                        }
                                    }
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                isTaskRunning = false;
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message || result.error });
                                break;
                            }
                            case 'generate_content': {
                                setGenieState('acting');
                                showSpeech('✍️ Generating content...', 60000);
                                window.wishcraft.sendToPanel({ type: 'wish-executing', text: 'Generating content...' });
                                try {
                                    if (!collaborator) collaborator = new GeminiCollaborator(CONFIG.apiKey);
                                    const prompt = call.args.prompt || '';
                                    // Auto-detect content type for domain-specific expertise
                                    const contentExpertise = (() => {
                                        if (/\b(cv|resume|curriculum vitae)\b/i.test(prompt)) return `
You are a professional CV/Resume writer.
STRUCTURE: Name → Contact (City | Phone | Email | LinkedIn) → PROFESSIONAL SUMMARY (3-4 sentences, action-oriented, no "I") → SKILLS (grouped by category, bullet list) → EXPERIENCE (reverse chronological: Title, Company | Location | Dates, then 3-5 achievement sentences with action verbs and metrics) → EDUCATION → CERTIFICATIONS → PROJECTS → VOLUNTEER.
RULES: Use action verbs (Led, Developed, Optimized, Spearheaded). Quantify ("Increased revenue 30%", "Managed team of 8"). No "Responsibilities included" — achievements only. Tailor to field. 1-2 pages. Enhance limited info professionally but stay truthful.`;
                                        if (/\b(essay|thesis|paper|dissertation|research)\b/i.test(prompt)) return `
You are an academic writing expert.
STRUCTURE: Title → Introduction (hook, context, thesis statement) → Body paragraphs (topic sentence, evidence, analysis, transition) → Conclusion (restate thesis, synthesize, broader implications).
RULES: Formal academic tone. Support claims with reasoning. Use transition words. Avoid first person unless specified. Proper paragraph structure. Clear argumentation flow.`;
                                        if (/\b(cover letter|application letter)\b/i.test(prompt)) return `
You are a professional cover letter writer.
STRUCTURE: Header (contact info) → Date → Employer address → Salutation → Opening (position + enthusiasm) → Body (2-3 paragraphs matching skills to job) → Closing (call to action + thank you) → Signature.
RULES: Personalize to the company. Show specific value. Mirror job posting keywords. Keep under 1 page. Enthusiastic but professional.`;
                                        if (/\b(business plan|proposal|pitch)\b/i.test(prompt)) return `
You are a business strategy consultant.
STRUCTURE: Executive Summary → Problem/Opportunity → Solution → Market Analysis → Business Model → Marketing Strategy → Financial Projections → Team → Timeline.
RULES: Data-driven. Clear value proposition. Realistic projections. Professional tone. Address risks.`;
                                        if (/\b(email|formal letter|official letter)\b/i.test(prompt)) return `
You are a professional communication expert.
RULES: Clear subject context. Professional greeting. Concise body (purpose → details → action needed). Professional closing. Appropriate tone for audience.`;
                                        if (/\b(report|analysis|brief)\b/i.test(prompt)) return `
You are a professional report writer.
STRUCTURE: Title → Executive Summary → Introduction → Methodology → Findings → Analysis → Recommendations → Conclusion.
RULES: Objective tone. Data-supported. Clear headings. Actionable recommendations.`;
                                        if (/\b(story|creative|poem|fiction|narrative)\b/i.test(prompt)) return `
You are a creative writing expert.
RULES: Vivid imagery. Show don't tell. Strong voice. Engaging opening. Sensory details. Character development. Satisfying structure.`;
                                        if (/\b(study notes|summary|revision|notes)\b/i.test(prompt)) return `
You are an expert educator and note-taker.
RULES: Clear organization by topic. Key concepts highlighted. Concise definitions. Examples for complex ideas. Logical flow. Easy to scan and review.`;
                                        return '\nYou are an expert professional writer. Produce polished, well-structured, audience-appropriate content. Use clear organization with logical flow.';
                                    })();
                                    const sysInst = (call.args.system_instruction || '') + contentExpertise + `

OUTPUT FORMAT RULES (MANDATORY):
- Output ONLY plain text. This will be pasted into Microsoft Word.
- Section headings: write them in ALL CAPS on their own line (e.g. PROFESSIONAL SUMMARY)
- Do NOT use markdown: no **, no ##, no \`backticks\`, no __, no *italic*, no > blockquotes, no --- separators.
- Use bullet points (- item) ONLY for short grouped lists like skills or coursework.
- For experience/education entries, write on separate lines:
  Job Title or Degree
  Company/University | Location | Date Range
  Then detail as normal text paragraphs, NOT as bullet points.
- Separate sections with a blank line.
- Write clean, professional, copy-paste-ready text.`;
                                    const genResult = await collaborator.generateContent(
                                        call.args.prompt,
                                        sysInst
                                    );
                                    if (genResult.success) {
                                        window._lastGeneratedContent = genResult.text;
                                        const cleanMd = (s) => s
                                            .replace(/\*\*\*(.+?)\*\*\*/g, '$1')   // ***bold italic***
                                            .replace(/\*\*(.+?)\*\*/g, '$1')       // **bold**
                                            .replace(/\*(.+?)\*/g, '$1')           // *italic*
                                            .replace(/__(.+?)__/g, '$1')           // __underline__
                                            .replace(/(?<!\w)_(.+?)_(?!\w)/g, '$1')// _italic_ (not mid_word)
                                            .replace(/`{1,3}(.+?)`{1,3}/g, '$1')  // `code` or ```code```
                                            .replace(/^#{1,6}\s+/gm, '')           // ## headings
                                            .replace(/^>\s?/gm, '')                // > blockquotes
                                            .replace(/^---+$/gm, '')               // --- separators
                                            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // [text](url) → text
                                            .trim();
                                        // Auto-write to Word ONLY if destination is 'word' (or not specified)
                                        const destination = (call.args.destination || 'word').toLowerCase();
                                        if (destination === 'return') {
                                            // Just return the text — genie will send it via WhatsApp/email/etc.
                                            result = { success: true, text: genResult.text, message: `Content generated (${genResult.text.length} chars). Use it as needed.` };
                                        } else {
                                            try {
                                                const lines = genResult.text.split('\n');
                                                const title = cleanMd(lines[0].replace(/^#+\s*/, '')) || 'Generated Document';
                                                const sections = [];
                                                let currentSection = null;
                                                for (let i = 1; i < lines.length; i++) {
                                                    const trimmed = lines[i].trim();
                                                    if (!trimmed) continue;
                                                    // Detect headings: ## Heading, **HEADING**, or ALL CAPS line (plain text)
                                                    const headingMatch = trimmed.match(/^#{1,3}\s+(.+)/) || trimmed.match(/^\*\*([A-Z][A-Z\s&/|,.-]+?)\*\*$/) || (trimmed === trimmed.toUpperCase() && /^[A-Z][A-Z\s&/|,.\-:()]{2,}$/.test(trimmed) ? [null, trimmed] : null);
                                                    if (headingMatch) {
                                                        if (currentSection) sections.push(currentSection);
                                                        currentSection = { heading: cleanMd(headingMatch[1]), text: '' };
                                                    } else if (currentSection) {
                                                        // Detect bullets ONLY for short list-style items (skills, coursework)
                                                        const bulletMatch = trimmed.match(/^[-•*]\s+(.+)/) || trimmed.match(/^\t[-•*]\s+(.+)/);
                                                        if (bulletMatch) {
                                                            if (!currentSection.bullet_items) currentSection.bullet_items = [];
                                                            currentSection.bullet_items.push(cleanMd(bulletMatch[1]));
                                                        } else {
                                                            const cleaned = cleanMd(trimmed);
                                                            if (cleaned) {
                                                                currentSection.text += (currentSection.text ? '\n' : '') + cleaned;
                                                            }
                                                        }
                                                    }
                                                }
                                                if (currentSection) sections.push(currentSection);
                                                if (sections.length > 0) {
                                                    showSpeech('📝 Writing to Word...', 30000);
                                                    let wordReady = false;
                                                    try {
                                                        const pathResult = await waitForPythonAction({ action: 'word_get_document_path' }, 3000);
                                                        if (pathResult.success && pathResult.path !== undefined) {
                                                            await waitForPythonAction({ action: 'word_clear_all' }, 3000);
                                                            wordReady = true;
                                                        }
                                                    } catch (e) { /* Word not open */ }
                                                    if (!wordReady) {
                                                        await waitForPythonAction({ action: 'word_open' }, 5000);
                                                        await waitForPythonAction({ action: 'word_new_document' }, 3000);
                                                    }
                                                    await waitForPythonAction({
                                                        action: 'word_write_formatted_document',
                                                        title: title,
                                                        sections: sections
                                                    }, 60000);
                                                    // Auto-save the document
                                                    await waitForPythonAction({ action: 'word_save', filename: title }, 5000);
                                                    result = { success: true, message: `Content written and saved to Word: "${title}" with ${sections.length} sections. The document is saved and open in Microsoft Word.` };
                                                } else {
                                                    await waitForPythonAction({
                                                        action: 'notes_create',
                                                        title: 'Generated Content',
                                                        body: genResult.text
                                                    }, 30000);
                                                    result = { success: true, message: `Content saved to Notes app (${genResult.text.length} chars). Open Notes to see it.` };
                                                }
                                            } catch (writeErr) {
                                                console.error('Auto-write failed:', writeErr);
                                                result = { success: true, message: `Content generated (${genResult.text.length} chars) but auto-write failed: ${writeErr.message}. Content is stored — ask me to write it somewhere.` };
                                            }
                                        } // end else (destination === 'word')
                                    } else {
                                        result = { success: false, error: genResult.error };
                                    }
                                } catch (e) {
                                    result = { success: false, error: e.message };
                                }
                                setGenieState('complete');
                                window.wishcraft.sendToPanel({ type: 'wish-complete', text: result.message?.substring(0, 200) || result.error });
                                break;
                            }

                            default:
                                result = { success: false, error: 'Unknown tool' };
                        }
                    } catch (error) { result = { success: false, error: error.message }; }
                    responses.push({ id: call.id, name: call.name, response: { output: result } });
                }
                // Log tool calls for conversation continuity
                const toolSummary = responses.map(r => `${r.name}(${r.response?.output?.success !== undefined ? (r.response.output.success ? '✓' : '✗') : '→'})`).join(', ');
                addToLog('tool', toolSummary);
                if (liveChatController) liveChatController.sendToolResponse(responses);
            },

            onStreamStart: async () => {
                if (head && head.streamStart) {
                    if (head._streamPreWarmed) { head.isSpeaking = true; return; }
                    try { await head.streamStart({ sampleRate: 24000, lipsyncLang: 'en' }, () => { }, () => { head.isSpeaking = false; }); head.isSpeaking = true; }
                    catch (e) { console.error('streamStart:', e); }
                }
            },
            onAudioChunk: (pcmData) => { if (head && head.streamAudio) head.streamAudio({ audio: pcmData }); },
            onInterrupted: () => { if (head) head.streamInterrupt(); },
            onStreamEnd: () => {
                if (head && head.streamNotifyEnd) head.streamNotifyEnd();
                if (head) head._streamPreWarmed = false;
            },

            onStatusChange: (status) => {
                console.log('🔴 Live:', status);
                if (status === 'connected') {
                    isLiveSessionActive = true;
                    isLiveSessionStarting = false;
                    sessionStartTime = Date.now();
                    window._genieHasGreeted = true;
                    setGenieState('listening');
                    window.wishcraft.sendToPanel({ type: 'status', text: 'connected' });
                    if (head && head.streamStart) {
                        head.streamStart({ sampleRate: 24000, lipsyncLang: 'en' }, () => { }, () => { head.isSpeaking = false; })
                            .then(() => { head._streamPreWarmed = true; })
                            .catch(() => { });
                    }
                } else if (status === 'disconnected' || status === 'error') {
                    const wasActive = isLiveSessionActive;
                    const wasDismissedBeforeDisconnect = genieState === 'dismissed';
                    isLiveSessionActive = false;
                    isLiveSessionStarting = false;
                    if (!wasDismissedBeforeDisconnect) setGenieState('idle');
                    window.wishcraft.sendToPanel({ type: 'status', text: status });
                    // Auto-reconnect after unexpected disconnect (NOT after dismiss)
                    if (wasActive && CONFIG.apiKey && !wasDismissedBeforeDisconnect) {
                        console.log('🔄 Auto-reconnecting in 1 second...');
                        showSpeech('🔄 Reconnecting...', 2000);
                        setTimeout(async () => {
                            try {
                                if (!isLiveSessionActive && genieState !== 'dismissed') {
                                    console.log('🔄 Reconnecting now...');
                                    await startLiveSession();
                                    showSpeech('✨ Back online!', 2000);
                                }
                            } catch (err) {
                                console.error('🔄 Reconnect failed:', err);
                                showSpeech('❌ Reconnect failed', 3000);
                            }
                        }, 1000);
                    }
                }
            },
            onUserSpeaking: () => setGenieState('listening'),
            onAIResponse: (text, isComplete) => {
                if (isComplete && text) {
                    addToLog('genie', text);
                    showSpeech(text, 5000);
                    window.wishcraft.sendToPanel({ type: 'genie-message', text });
                }
            },
            onUserTranscript: (text, isComplete) => {
                if (isComplete && text) {
                    addToLog('user', text);
                    window.wishcraft.sendToPanel({ type: 'user-message', text });

                    if (isTaskRunning) {
                        const lower = text.toLowerCase();
                        const cancelKeywords = ['cancel', 'stop', 'bad de', 'thak', 'বাদ দে', 'থাক', 'bad dao', 'thako', 'never mind', 'abort'];
                        const confirmKeywords = ['yes', 'yeah', 'ha', 'haa', 'হ্যাঁ', 'হা', 'confirm', 'ok', 'okay', 'sure'];
                        if (window._cancelPending) {
                            if (confirmKeywords.some(kw => lower.includes(kw)) || cancelKeywords.some(kw => lower.includes(kw))) {
                                // User confirmed cancel
                                console.log('🛑 Cancel confirmed:', text);
                                window._cancelPending = false;
                                window.wishcraft.cancelComputerTask();
                                isTaskRunning = false;
                                showSpeech('🛑 Cancelling...', 2000);
                                if (window._cancelCurrentTask) {
                                    window._cancelCurrentTask();
                                }
                            } else {
                                // User said something else — cancel the cancel, keep going
                                console.log('🛑 Cancel dismissed, continuing task');
                                window._cancelPending = false;
                                showSpeech('✅ Continuing task...', 2000);
                            }
                        } else if (cancelKeywords.some(kw => lower.includes(kw))) {
                            // First cancel — ask genie to confirm
                            console.log('🛑 Cancel requested, asking confirmation:', text);
                            window._cancelPending = true;
                            showSpeech('⚠️ Are you sure you want to cancel? Say "yes" to confirm.', 10000);
                        }
                    }
                }
            },
            onError: (error) => {
                showSpeech('❌ ' + (error.message || 'Failed'), 5000);
                stopLiveSession();
            }
        });

        await liveChatController.start();
        liveChatController.resumeAudio();

        // Trigger greeting (or reconnection message)
        setTimeout(() => {
            if (liveChatController && isLiveSessionActive) {
                let msg;
                if (initialGreeting) {
                    msg = 'You just appeared from the lamp. Say this greeting: "' + initialGreeting + '" — ONLY speak this greeting, do NOT call any tools or execute any actions.';
                } else if (!window._genieFirstGreetDone && conversationLog.length === 0) {
                    // First app launch — trigger the greeting
                    window._genieFirstGreetDone = true;
                    msg = 'You just appeared from the lamp for the first time. Introduce yourself briefly as the Genie of Wishcraft and ask for a wish. ONLY speak — do NOT call any tools or execute any actions.';
                } else if (wasGenieDismissed && conversationLog.length > 0) {
                    // User dismissed and came back — say "I'm back" with context
                    const recentEntries = conversationLog.slice(-10)
                        .filter(e => e.role !== 'tool')
                        .map(e => `${e.role === 'user' ? 'User' : 'Genie'}: ${e.content}`)
                        .join('\n');
                    const taskInfo = taskList.length > 0
                        ? '\n\nACTIVE TASKS:\n' + taskList.map((t, i) => `${i + 1}. ${t.name} - ${t.status}`).join('\n')
                        : '';
                    msg = 'The user summoned you back. Here is the recent conversation:\n' + recentEntries + taskInfo + '\nSay briefly you are back and ready. If there are active tasks, mention them. Do NOT re-execute any previous tool calls.';
                    wasGenieDismissed = false;
                } else if (conversationLog.length > 0) {
                    // Auto-reconnect — silently restore context with tasks, do NOT speak
                    const recentEntries = conversationLog.slice(-10)
                        .filter(e => e.role !== 'tool')
                        .map(e => `${e.role === 'user' ? 'User' : 'Genie'}: ${e.content}`)
                        .join('\n');
                    const taskInfo = taskList.length > 0
                        ? '\n\nACTIVE TASKS (still running):\n' + taskList.map((t, i) => `${i + 1}. ${t.name} - ${t.status}`).join('\n')
                        : '';
                    msg = '[SYSTEM] Session auto-reconnected. Here is the recent conversation and task status for context ONLY:\n' + recentEntries + taskInfo + '\nDo NOT speak. Do NOT say "I am back". Do NOT re-execute any tools. Just silently resume and wait for the user to talk. When the user speaks next, you already know the full context — continue naturally.';
                }
                // Only send if there's a specific message (greeting or reconnection context).
                // For first-time sessions, the system instruction already tells genie to introduce itself.
                if (msg) liveChatController.sendText(msg);
            }
        }, 500);

    } catch (error) {
        showSpeech('❌ ' + error.message, 5000);
        isLiveSessionActive = false;
        isLiveSessionStarting = false;
    }
}

function stopLiveSession() {
    // Auto-save session summary on disconnect if we had a conversation
    if (conversationLog.length > 2) {
        const userMsgs = conversationLog.filter(e => e.role === 'user').map(e => e.content);
        const summary = userMsgs.length > 0
            ? `User asked about: ${userMsgs.slice(-5).join('; ').substring(0, 200)}`
            : 'Short session with tool interactions';
        try { window.wishcraft.memory.addHistory(summary); } catch (e) { /* ignore */ }
    }
    const wasDismissed = genieState === 'dismissed';
    if (liveChatController) { liveChatController.stop(); liveChatController = null; }
    if (head && head.streamStop) head.streamStop();
    isLiveSessionActive = false; isScreenSharing = false; isWebcamActive = false; isTaskRunning = false;
    if (!wasDismissed) setGenieState('idle');
}

function waitForPythonAction(actionPayload, timeoutMs = 60000) {
    return new Promise((resolve) => {
        window.wishcraft.executeAction(actionPayload);

        const timeout = setTimeout(() => {
            resolve({ success: false, error: `Action timed out (${timeoutMs / 1000}s)` });
        }, timeoutMs);

        const handler = (result) => {
            if (result.progress) {
                window.wishcraft.sendToPanel({ type: 'genie-message', text: '🤖 ' + result.message });
            } else if (result.executing) {
                window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚡ ' + result.executing });
            } else {
                clearTimeout(timeout);
                resolve(result);
            }
        };
        window.wishcraft.onActionResult(handler);
    });
}

async function executeComputerTask(goal) {
    return new Promise((resolve) => {
        window.wishcraft.executeAction({
            action: 'computer_use_task',
            goal: goal,
            max_turns: 10
        });

        const timeout = setTimeout(() => {
            window._cancelCurrentTask = null;
            resolve({ success: false, error: 'Computer Use task timed out (120s)' });
        }, 120000);

        window._cancelCurrentTask = () => {
            clearTimeout(timeout);
            window._cancelCurrentTask = null;
            resolve({ success: true, summary: 'Task cancelled by user' });
        };

        const handler = (result) => {
            if (result.progress) {
                window.wishcraft.sendToPanel({ type: 'genie-message', text: '🤖 ' + result.message });
                showSpeech('🤖 ' + result.message, 8000);
            } else if (result.executing) {
                const actionLabels = {
                    'click_at': '👆 Clicking...',
                    'type_text_at': '⌨️ Typing...',
                    'navigate': '🌐 Opening page...',
                    'scroll_document': '📜 Scrolling...',
                    'scroll_at': '📜 Scrolling...',
                    'key_combination': '⌨️ Pressing keys...',
                    'open_application': '📱 Opening app...',
                    'open_web_browser': '🌐 Opening browser...',
                    'search': '🔍 Searching...',
                    'wait_5_seconds': '⏳ Waiting for page...',
                    'hover_at': '👆 Hovering...',
                    'drag_and_drop': '👆 Dragging...',
                    'read_clipboard': '📋 Reading clipboard...',
                    'get_browser_url': '🌐 Reading URL...',
                    'get_running_apps': '📱 Checking apps...',
                    'get_frontmost_app': '📱 Checking active app...',
                };
                const label = actionLabels[result.executing] || '⚡ ' + result.executing;
                window.wishcraft.sendToPanel({ type: 'genie-message', text: '⚡ ' + result.executing });
                showSpeech(label, 5000);
            } else if (result.action === 'cancel') {
                // Ignore cancel confirmation — _cancelCurrentTask() already resolved
            } else {
                clearTimeout(timeout);
                window._cancelCurrentTask = null;
                resolve(result);
            }
        };
        window.wishcraft.onActionResult(handler);
    });
}

let isDragging = false, lastPos = { x: 0, y: 0 };
document.addEventListener('mousedown', (e) => {
    if (e.target.closest('.avatar-btn') || e.target.closest('.lang-btn') || e.target.closest('#lang-picker')) return;
    isDragging = true; lastPos = { x: e.screenX, y: e.screenY };
});
document.addEventListener('mousemove', (e) => {
    if (isDragging) { window.wishcraft.moveWindow(e.screenX - lastPos.x, e.screenY - lastPos.y); lastPos = { x: e.screenX, y: e.screenY }; }
});
document.addEventListener('mouseup', () => { isDragging = false; });

document.getElementById('btn-chat')?.addEventListener('click', () => window.wishcraft.togglePanel());
document.getElementById('btn-mic')?.addEventListener('click', () => {
    if (!isLiveSessionActive) startLiveSession();
    else stopLiveSession();
});

window.wishcraft.onShowGenie(async () => {
    console.log('🧞 Summoning...');
    smokeSystem.summon(() => { });
    setTimeout(() => setGenieState('summoned'), 400);
    // Wait for init() to finish loading settings (so hasPickedLanguage is correct)
    if (!initDone) {
        for (let i = 0; i < 30; i++) { // wait up to 3 seconds
            await new Promise(r => setTimeout(r, 100));
            if (initDone) break;
        }
    }
    if (!hasPickedLanguage) {
        langPicker.classList.remove('hidden');
    } else if (!isLiveSessionActive) {
        setTimeout(() => startLiveSession(), 800);
    }
});

window.wishcraft.onHideGenie(() => {
    console.log('🧞 Dismissing...');
    wasGenieDismissed = true;
    showSpeech('Until next time! 💫', 1500);
    smokeSystem.dismiss(() => { });
    setTimeout(() => { setGenieState('dismissed'); stopLiveSession(); }, 600);
});

// Messages from panel
window.wishcraft.onFromPanel((data) => {
    switch (data.type) {
        case 'send-text':
            if (liveChatController && isLiveSessionActive) {
                addToLog('user', data.text);
                liveChatController.sendText(data.text);
                showSpeech('📝 "' + data.text + '"', 3000);
            } else {
                window._genieHasGreeted = true;
                startLiveSession(null, true).then(() => {
                    setTimeout(() => {
                        if (liveChatController) liveChatController.sendText(data.text);
                        showSpeech('📝 "' + data.text + '"', 3000);
                    }, 2000);
                });
            }
            break;
        case 'send-screenshot':
            window.wishcraft.takeScreenshot().then(ss => {
                if (ss) {
                    if (liveChatController) liveChatController.sendImage(ss, 'image/jpeg', 'Here is my screen.', true);
                    window.wishcraft.sendToPanel({ type: 'screenshot', image: ss });
                }
            });
            break;
        case 'send-file': {
            const sendFileToGenie = async () => {
                const { fileName, mimeType, base64, size, message } = data;
                const fileType = mimeType.startsWith('image/') ? 'image' :
                    (mimeType.startsWith('audio/') || mimeType.startsWith('video/')) ? 'audio' : 'document';

                showSpeech('📎 Received: ' + fileName, 3000);

                const ensureSession = () => new Promise((resolve) => {
                    if (liveChatController && isLiveSessionActive) {
                        resolve();
                    } else {
                        // Start session silently — no greeting, genie waits for the file
                        window._genieHasGreeted = true;
                        startLiveSession(null, true).then(() => {
                            setTimeout(resolve, 2500);
                        });
                    }
                });

                await ensureSession();

                // Use Gemini 3 Flash REST API to analyze the file first,
                // then send the analysis text to the Live API genie
                try {
                    if (!collaborator) collaborator = new GeminiCollaborator(CONFIG.apiKey);
                    showSpeech('🔍 Analyzing ' + fileName + '...', 15000);
                    window.wishcraft.sendToPanel({ type: 'wish-executing', text: '🔍 Analyzing: ' + fileName });

                    let analysis;
                    const userMessage = message !== 'Analyze this file' ? message : '';

                    if (fileType === 'image') {
                        const question = userMessage
                            ? userMessage + '\n\nAnalyze this image in detail. Extract ALL text, numbers, data, tables, charts, and visual elements. Provide structured data that can be used to recreate the content.'
                            : 'Analyze this image in detail. Describe what you see. Extract ALL text, numbers, data, tables, charts, and visual elements. Provide structured data.';
                        analysis = await collaborator.analyzeFile(base64, mimeType, question);
                    } else if (fileType === 'audio') {
                        analysis = await collaborator.transcribeAudio(base64, mimeType);
                    } else {
                        const question = userMessage
                            ? userMessage + '\n\nAnalyze this document in detail. Extract all content, data, and structure.'
                            : 'Analyze this document in detail. Extract all content, text, data, tables, and structure.';
                        analysis = await collaborator.analyzeFile(base64, mimeType, question);
                    }

                    if (analysis.success) {
                        const contextText = userMessage
                            ? `User uploaded "${fileName}" and says: "${userMessage}"\n\nHere is the file analysis from Gemini 3 Flash:\n${analysis.text}`
                            : `User uploaded "${fileName}". Here is the analysis:\n${analysis.text}`;
                        if (liveChatController) liveChatController.sendText(contextText);
                        window.wishcraft.sendToPanel({ type: 'wish-complete', text: '✅ File analyzed' });
                    } else {
                        // Fallback: send raw text to genie
                        const fallbackText = userMessage
                            ? userMessage + ' (User uploaded file: ' + fileName + ', but analysis failed: ' + analysis.error + ')'
                            : 'User uploaded ' + fileName + ' but I could not analyze it: ' + analysis.error;
                        if (liveChatController) liveChatController.sendText(fallbackText);
                        window.wishcraft.sendToPanel({ type: 'wish-complete', text: '⚠️ Analysis failed, sent to genie' });
                    }
                } catch (e) {
                    console.error('Failed to analyze uploaded file:', e);
                    // Fallback: just tell genie about the file
                    if (liveChatController) liveChatController.sendText('User uploaded ' + fileName + ' but analysis failed: ' + e.message);
                    window.wishcraft.sendToPanel({ type: 'genie-message', text: 'Analysis failed: ' + e.message });
                }
            };
            sendFileToGenie();
            break;
        }
        case 'change-lang':
            CONFIG.currentLang = data.lang;
            if (isLiveSessionActive) { stopLiveSession(); setTimeout(() => startLiveSession(), 500); }
            break;
        case 'change-avatar':
            switchAvatar(data.avatar);
            break;
        case 'change-voice':
            CONFIG.currentVoice = data.voice;
            if (isLiveSessionActive) { stopLiveSession(); setTimeout(() => startLiveSession(), 500); }
            break;
        case 'change-username':
            CONFIG.userName = data.name || '';
            break;
        case 'remove-task':
            if (data.index >= 0 && data.index < taskList.length) {
                taskList.splice(data.index, 1);
                saveTasks();
            }
            break;
        case 'add-task-manual':
            taskList.push({ name: data.name, schedule: data.schedule || 'daily', status: 'active', createdAt: Date.now() });
            saveTasks();
            break;
        case 'get-tasks':
            window.wishcraft.sendToPanel({ type: 'tasks-updated', tasks: taskList });
            break;
        case 'toggle-screen-share':
            if (liveChatController && isLiveSessionActive) {
                if (!isScreenSharing) {
                    liveChatController.startScreenShare(1);
                    isScreenSharing = true;
                    showSpeech('🖥️ Screen sharing ON', 3000);
                } else {
                    liveChatController.stopScreenShare();
                    isScreenSharing = false;
                    showSpeech('🖥️ Screen sharing OFF', 3000);
                }
                window.wishcraft.sendToPanel({ type: 'screen-share-status', active: isScreenSharing });
            }
            break;
        case 'toggle-webcam':
            if (liveChatController && isLiveSessionActive) {
                if (!isWebcamActive) {
                    liveChatController.startWebcam().then(() => {
                        isWebcamActive = true;
                        showSpeech('📷 Webcam ON', 3000);
                        window.wishcraft.sendToPanel({ type: 'webcam-status', active: true });
                    }).catch(e => {
                        showSpeech('❌ Webcam: ' + e.message, 3000);
                    });
                } else {
                    liveChatController.stopWebcam();
                    isWebcamActive = false;
                    showSpeech('📷 Webcam OFF', 3000);
                    window.wishcraft.sendToPanel({ type: 'webcam-status', active: false });
                }
            }
            break;
    }
});

async function init() {
    console.log('✨ WishCraft Avatar initializing...');

    try {
        const savedAvatar = await window.wishcraft.getSetting('avatar', 'male');
        const savedLang = await window.wishcraft.getSetting('language', 'en');
        const savedVoice = await window.wishcraft.getSetting('voice', null);
        const savedName = await window.wishcraft.memory.getUserFact('userName');
        const setupDone = await window.wishcraft.getSetting('setupComplete', false);
        CONFIG.currentAvatar = savedAvatar;
        CONFIG.currentLang = savedLang;
        CONFIG.currentVoice = savedVoice;
        CONFIG.userName = savedName || '';
        // Skip language picker if user has applied settings at least once
        // Also treat having a saved name or voice as proof of prior setup (for configs created before setupComplete flag)
        if (setupDone || savedName || savedVoice) hasPickedLanguage = true;
        console.log('⚙️ Loaded settings:', { avatar: savedAvatar, lang: savedLang, voice: savedVoice, name: savedName, setupDone });
    } catch (e) { console.warn('Settings load failed:', e); }

    initDone = true;
    const ok = await initializeAvatar();
    if (ok) console.log('✅ Avatar ready!');
    window.wishcraft.sendToPanel({ type: 'tasks-updated', tasks: taskList });
}
init();
