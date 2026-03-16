/**
 * WishCraft Encrypted Config Store
 * 
 * Stores config (API key, settings, memory) in ~/.wishcraft/config.enc
 * Uses same AES-256-GCM encryption as contacts.js
 * Key derived from machine-specific identifier + app secret
 * 
 * Supports:
 * - Local-only storage (default)
 * - Cloud sync via WishCraft Cloud Run server
 * - Custom API key vs managed credits
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

const WISHCRAFT_DIR = path.join(os.homedir(), '.wishcraft');
const CONFIG_FILE = path.join(WISHCRAFT_DIR, 'config.enc');
const MEMORY_FILE = path.join(WISHCRAFT_DIR, 'memory.enc');
const CHATS_FILE = path.join(WISHCRAFT_DIR, 'chats.enc');
const APP_SECRET = 'wishcraft-genie-2026-config-key';

// Encryption (same pattern as contacts.js)
function getMachineKey() {
    const raw = [os.hostname(), os.userInfo().username, os.homedir(), APP_SECRET].join('|');
    return crypto.createHash('sha256').update(raw).digest();
}

function encrypt(text) {
    const key = getMachineKey();
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag().toString('hex');
    return iv.toString('hex') + ':' + authTag + ':' + encrypted;
}

function decrypt(encryptedText) {
    const key = getMachineKey();
    const parts = encryptedText.split(':');
    if (parts.length !== 3) throw new Error('Invalid encrypted data');
    const iv = Buffer.from(parts[0], 'hex');
    const authTag = Buffer.from(parts[1], 'hex');
    const encrypted = parts[2];
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(authTag);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}

function ensureDir() {
    if (!fs.existsSync(WISHCRAFT_DIR)) {
        fs.mkdirSync(WISHCRAFT_DIR, { recursive: true, mode: 0o700 });
    }
}

// Config Store (API key, settings)
function loadConfig() {
    try {
        ensureDir();
        if (!fs.existsSync(CONFIG_FILE)) return {};
        const encrypted = fs.readFileSync(CONFIG_FILE, 'utf8');
        return JSON.parse(decrypt(encrypted));
    } catch (e) {
        console.error('⚙️ Failed to load config:', e.message);
        return {};
    }
}

function saveConfig(config) {
    try {
        ensureDir();
        const encrypted = encrypt(JSON.stringify(config, null, 2));
        fs.writeFileSync(CONFIG_FILE, encrypted, { mode: 0o600 });
        return true;
    } catch (e) {
        console.error('⚙️ Failed to save config:', e.message);
        return false;
    }
}

function getApiKey() {
    const config = loadConfig();
    return config.apiKey || '';
}

function setApiKey(apiKey) {
    const config = loadConfig();
    config.apiKey = apiKey;
    return saveConfig(config);
}

function getSetting(key, defaultValue = null) {
    const config = loadConfig();
    return config.settings ? (config.settings[key] ?? defaultValue) : defaultValue;
}

function setSetting(key, value) {
    const config = loadConfig();
    if (!config.settings) config.settings = {};
    config.settings[key] = value;
    return saveConfig(config);
}

function getAllSettings() {
    const config = loadConfig();
    return config.settings || {};
}

// Memory Store (user context, preferences, summaries)
function loadMemory() {
    try {
        ensureDir();
        if (!fs.existsSync(MEMORY_FILE)) return { user: {}, context: {}, history: [] };
        const encrypted = fs.readFileSync(MEMORY_FILE, 'utf8');
        return JSON.parse(decrypt(encrypted));
    } catch (e) {
        console.error('🧠 Failed to load memory:', e.message);
        return { user: {}, context: {}, history: [] };
    }
}

function saveMemory(memory) {
    try {
        ensureDir();
        const encrypted = encrypt(JSON.stringify(memory));
        fs.writeFileSync(MEMORY_FILE, encrypted, { mode: 0o600 });
        return true;
    } catch (e) {
        console.error('🧠 Failed to save memory:', e.message);
        return false;
    }
}

function setUserFact(key, value) {
    const memory = loadMemory();
    memory.user[key] = value;
    return saveMemory(memory);
}

function getUserFact(key) {
    const memory = loadMemory();
    return memory.user[key] || null;
}

function getAllUserFacts() {
    const memory = loadMemory();
    return memory.user || {};
}

function setContext(key, value) {
    const memory = loadMemory();
    memory.context[key] = value;
    return saveMemory(memory);
}

function getContext(key) {
    const memory = loadMemory();
    return memory.context[key] || null;
}

function addHistoryEntry(summary) {
    const memory = loadMemory();
    if (!memory.history) memory.history = [];
    memory.history.push({
        summary,
        timestamp: new Date().toISOString()
    });
    // Keep only last 50 entries
    if (memory.history.length > 50) {
        memory.history = memory.history.slice(-50);
    }
    return saveMemory(memory);
}

function getHistory(count = 10) {
    const memory = loadMemory();
    return (memory.history || []).slice(-count);
}

function getFullMemory() {
    return loadMemory();
}

function clearMemory() {
    return saveMemory({ user: {}, context: {}, history: [] });
}

// Chat History (full conversation persistence)
function loadChats() {
    try {
        ensureDir();
        if (!fs.existsSync(CHATS_FILE)) return { conversations: [] };
        const encrypted = fs.readFileSync(CHATS_FILE, 'utf8');
        return JSON.parse(decrypt(encrypted));
    } catch (e) {
        console.error('💬 Failed to load chats:', e.message);
        return { conversations: [] };
    }
}

function saveChats(chats) {
    try {
        ensureDir();
        const encrypted = encrypt(JSON.stringify(chats));
        fs.writeFileSync(CHATS_FILE, encrypted, { mode: 0o600 });
        return true;
    } catch (e) {
        console.error('💬 Failed to save chats:', e.message);
        return false;
    }
}

// Generate a smart, concise chat title from the user's first message
function generateSmartTitle(text) {
    if (!text || text.trim().length === 0) return 'New Chat';
    const cleaned = text.trim();

    // Pattern-based title extraction for common wishes
    const patterns = [
        // Email
        { regex: /send\s+(?:an?\s+)?email\s+to\s+(\S+)/i, title: (m) => `Email to ${m[1].split('@')[0]}` },
        { regex: /reply\s+(?:to\s+)?(?:the\s+)?(?:(\w+)\s+)?email/i, title: () => 'Email Reply' },
        { regex: /forward\s+(?:the\s+)?email/i, title: () => 'Forward Email' },
        { regex: /check\s+(?:my\s+)?(?:gmail|email|inbox|mail)/i, title: () => 'Check Email' },
        { regex: /(?:how many|unread)\s+(?:emails?|messages?)/i, title: () => 'Unread Emails' },
        { regex: /read\s+(?:my\s+)?(?:emails?|inbox|mail)/i, title: () => 'Read Emails' },
        // Apps
        { regex: /open\s+(.+)/i, title: (m) => `Open ${m[1].substring(0, 25).trim()}` },
        { regex: /close\s+(.+)/i, title: (m) => `Close ${m[1].substring(0, 25).trim()}` },
        // Web
        { regex: /(?:search|google|look up)\s+(?:for\s+)?(.+)/i, title: (m) => `Search: ${m[1].substring(0, 30).trim()}` },
        { regex: /(?:go to|open|navigate)\s+(?:to\s+)?(\S+\.(?:com|org|net|io|dev)\S*)/i, title: (m) => `Visit ${m[1].substring(0, 30)}` },
        // YouTube
        { regex: /play\s+(.+)\s+(?:on\s+)?youtube/i, title: (m) => `YouTube: ${m[1].substring(0, 30).trim()}` },
        { regex: /(?:youtube|play)\s+(.+)/i, title: (m) => `YouTube: ${m[1].substring(0, 30).trim()}` },
        // Documents
        { regex: /(?:create|make|write)\s+(?:a\s+)?(?:new\s+)?(?:word\s+)?(?:document|doc|letter|essay|report|cv|resume)\s*(?:about|for|on)?\s*(.*)/i, title: (m) => `Document: ${(m[1] || 'New').substring(0, 25).trim() || 'New'}` },
        { regex: /(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:presentation|slides?|pptx|deck)\s*(?:about|for|on)?\s*(.*)/i, title: (m) => `Slides: ${(m[1] || 'New').substring(0, 25).trim() || 'New'}` },
        { regex: /(?:create|make)\s+(?:a\s+)?(?:new\s+)?(?:spreadsheet|excel|budget|tracker)\s*(?:about|for|on|with)?\s*(.*)/i, title: (m) => `Spreadsheet: ${(m[1] || 'New').substring(0, 25).trim() || 'New'}` },
        // System
        { regex: /(?:check|what(?:'s| is))\s+(?:my\s+)?(?:battery|wifi|wi-fi|disk|storage|volume)/i, title: (m) => `System: ${cleaned.match(/battery|wifi|wi-fi|disk|storage|volume/i)[0]}` },
        { regex: /(?:set|change|adjust)\s+(?:the\s+)?(?:volume|brightness)/i, title: () => 'Adjust Settings' },
        { regex: /(?:empty|clear)\s+(?:the\s+)?trash/i, title: () => 'Empty Trash' },
        { regex: /(?:take|capture)\s+(?:a\s+)?screenshot/i, title: () => 'Screenshot' },
        { regex: /(?:lock|sleep)\s+(?:the\s+)?(?:screen|computer|mac)/i, title: () => 'Lock Screen' },
        // Files
        { regex: /(?:organize|clean|sort|tidy)\s+(?:my\s+)?(?:files?|folder|desktop|downloads)/i, title: () => 'Organize Files' },
        { regex: /(?:find|search|where)\s+(?:is\s+)?(?:the\s+)?(?:file|document|folder)\s*(.*)/i, title: (m) => `Find: ${(m[1] || 'file').substring(0, 25).trim()}` },
        // Reminders/Calendar
        { regex: /(?:remind|reminder)\s*(?:me\s+)?(?:to\s+)?(.*)/i, title: (m) => `Reminder: ${(m[1] || '').substring(0, 25).trim() || 'New'}` },
        { regex: /(?:calendar|event|meeting|schedule)\s*(.*)/i, title: (m) => `Calendar: ${(m[1] || '').substring(0, 25).trim() || 'Event'}` },
        // WhatsApp
        { regex: /(?:send|whatsapp)\s+(?:a\s+)?(?:whatsapp\s+)?(?:message\s+)?(?:to\s+)?(.*)/i, title: (m) => `WhatsApp: ${(m[1] || '').split(/\s+(?:saying|with|that)/i)[0].substring(0, 25).trim() || 'Message'}` },
        // Notes
        { regex: /(?:create|make|write|add)\s+(?:a\s+)?(?:new\s+)?note\s*(?:about|for|on|called)?\s*(.*)/i, title: (m) => `Note: ${(m[1] || 'New').substring(0, 25).trim() || 'New'}` },
        // Transcribe
        { regex: /transcribe/i, title: () => 'Transcribe Audio' },
        // Background
        { regex: /(?:remove|delete)\s+(?:the\s+)?background/i, title: () => 'Remove Background' },
    ];

    for (const p of patterns) {
        const match = cleaned.match(p.regex);
        if (match) {
            const title = p.title(match);
            return title.length > 40 ? title.substring(0, 40) + '...' : title;
        }
    }

    // Fallback: take first sentence or first 40 chars, clean up
    const firstSentence = cleaned.split(/[.!?\n]/)[0].trim();
    const fallback = firstSentence.length > 40 ? firstSentence.substring(0, 40) + '...' : firstSentence;
    // Capitalize first letter
    return fallback.charAt(0).toUpperCase() + fallback.slice(1);
}

function chatCreate(title) {
    const chats = loadChats();
    const id = crypto.randomBytes(8).toString('hex');
    chats.conversations.unshift({
        id,
        title: title || 'New Chat',
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
        messages: []
    });
    // Keep max 100 conversations
    if (chats.conversations.length > 100) chats.conversations = chats.conversations.slice(0, 100);
    saveChats(chats);
    return id;
}

function chatAddMessage(conversationId, role, text) {
    const chats = loadChats();
    const conv = chats.conversations.find(c => c.id === conversationId);
    if (!conv) return false;
    conv.messages.push({
        role, // 'user' | 'genie' | 'system'
        text,
        time: new Date().toISOString()
    });
    conv.updated = new Date().toISOString();
    // Auto-title from first user message — generate smart title based on the wish
    if (conv.title === 'New Chat' && role === 'user' && text) {
        conv.title = generateSmartTitle(text);
    }
    // Keep max 500 messages per conversation
    if (conv.messages.length > 500) conv.messages = conv.messages.slice(-500);
    saveChats(chats);
    return true;
}

// Get conversation list (id, title, created, updated, messageCount)
function chatListConversations() {
    const chats = loadChats();
    return chats.conversations.map(c => ({
        id: c.id,
        title: c.title,
        created: c.created,
        updated: c.updated,
        messageCount: c.messages.length
    }));
}

function chatGetConversation(id) {
    const chats = loadChats();
    return chats.conversations.find(c => c.id === id) || null;
}

// Delete a conversation
function chatDeleteConversation(id) {
    const chats = loadChats();
    chats.conversations = chats.conversations.filter(c => c.id !== id);
    saveChats(chats);
    return true;
}

// Rename a conversation
function chatRenameConversation(id, title) {
    const chats = loadChats();
    const conv = chats.conversations.find(c => c.id === id);
    if (!conv) return false;
    conv.title = title;
    saveChats(chats);
    return true;
}

// Device ID (unique per machine, for cloud sync)
function getDeviceId() {
    const config = loadConfig();
    if (config.deviceId) return config.deviceId;
    // Generate once, persist
    const deviceId = crypto.randomBytes(16).toString('hex');
    config.deviceId = deviceId;
    saveConfig(config);
    return deviceId;
}

// Cloud Sync (upload/download encrypted files)
async function cloudSyncUpload(serverUrl, fileName) {
    const filePath = path.join(WISHCRAFT_DIR, fileName);
    if (!fs.existsSync(filePath)) return { success: false, message: 'File does not exist locally' };

    const encryptedData = fs.readFileSync(filePath, 'utf8');
    const deviceId = getDeviceId();

    try {
        const response = await fetch(`${serverUrl}/api/cloud-sync/upload`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deviceId, fileName, encryptedData })
        });
        return await response.json();
    } catch (e) {
        return { success: false, message: e.message };
    }
}

async function cloudSyncDownload(serverUrl, fileName) {
    const deviceId = getDeviceId();

    try {
        const response = await fetch(`${serverUrl}/api/cloud-sync/download`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ deviceId, fileName })
        });
        const result = await response.json();
        if (result.success && result.encryptedData) {
            ensureDir();
            const filePath = path.join(WISHCRAFT_DIR, path.basename(fileName));
            fs.writeFileSync(filePath, result.encryptedData, { mode: 0o600 });
            return { success: true, message: 'Downloaded and saved' };
        }
        return result;
    } catch (e) {
        return { success: false, message: e.message };
    }
}

// Sync all encrypted files to cloud
async function cloudSyncAll(serverUrl) {
    const files = ['config.enc', 'memory.enc', 'contacts.enc', 'chats.enc'];
    const results = {};
    for (const file of files) {
        const filePath = path.join(WISHCRAFT_DIR, file);
        if (fs.existsSync(filePath)) {
            results[file] = await cloudSyncUpload(serverUrl, file);
        }
    }
    return results;
}

// Download all encrypted files from cloud
async function cloudRestoreAll(serverUrl) {
    const files = ['config.enc', 'memory.enc', 'contacts.enc', 'chats.enc'];
    const results = {};
    for (const file of files) {
        results[file] = await cloudSyncDownload(serverUrl, file);
    }
    return results;
}

// API Mode (custom key vs managed credits)
function getApiMode() {
    const config = loadConfig();
    return config.apiMode || 'custom'; // 'custom' | 'credits'
}

function setApiMode(mode) {
    const config = loadConfig();
    config.apiMode = mode;
    return saveConfig(config);
}

function getServerUrl() {
    const config = loadConfig();
    return config.serverUrl || 'https://wishcraft-server-47389095635.us-central1.run.app';
}

function setServerUrl(url) {
    const config = loadConfig();
    config.serverUrl = url;
    return saveConfig(config);
}

function getStorageMode() {
    const config = loadConfig();
    return config.storageMode || 'offline'; // 'offline' | 'online'
}

function setStorageMode(mode) {
    const config = loadConfig();
    config.storageMode = mode;
    return saveConfig(config);
}

module.exports = {
    WISHCRAFT_DIR,
    // Config
    getApiKey,
    setApiKey,
    getSetting,
    setSetting,
    getAllSettings,
    // Memory
    setUserFact,
    getUserFact,
    getAllUserFacts,
    setContext,
    getContext,
    addHistoryEntry,
    getHistory,
    getFullMemory,
    clearMemory,
    // Chat History
    chatCreate,
    chatAddMessage,
    chatListConversations,
    chatGetConversation,
    chatDeleteConversation,
    chatRenameConversation,
    // Device & Cloud Sync
    getDeviceId,
    cloudSyncUpload,
    cloudSyncDownload,
    cloudSyncAll,
    cloudRestoreAll,
    // API Mode & Storage Mode
    getApiMode,
    setApiMode,
    getServerUrl,
    setServerUrl,
    getStorageMode,
    setStorageMode,
};
