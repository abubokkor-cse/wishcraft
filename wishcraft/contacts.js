/**
 * WishCraft Encrypted Contacts Store
 * 
 * Stores contacts in ~/.wishcraft/contacts.enc using AES-256-GCM
 * Key derived from machine-specific identifier + app secret
 * 
 * Format: { "rushafa": { phone: "+8801774757994", name: "Rushafa" }, ... }
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const os = require('os');

const WISHCRAFT_DIR = path.join(os.homedir(), '.wishcraft');
const CONTACTS_FILE = path.join(WISHCRAFT_DIR, 'contacts.enc');
const APP_SECRET = 'wishcraft-genie-2026-enc-key';

// Encryption Key (machine-specific)
function getMachineKey() {
    // Derive key from: hostname + username + homedir + app secret
    // This makes the file useless on another machine
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

// CRUD Operations
function ensureDir() {
    if (!fs.existsSync(WISHCRAFT_DIR)) {
        fs.mkdirSync(WISHCRAFT_DIR, { recursive: true, mode: 0o700 });
    }
}

function loadContacts() {
    try {
        ensureDir();
        if (!fs.existsSync(CONTACTS_FILE)) return {};
        const encrypted = fs.readFileSync(CONTACTS_FILE, 'utf8');
        const json = decrypt(encrypted);
        return JSON.parse(json);
    } catch (e) {
        console.error('📇 Failed to load contacts:', e.message);
        return {};
    }
}

function saveContacts(contacts) {
    try {
        ensureDir();
        const json = JSON.stringify(contacts, null, 2);
        const encrypted = encrypt(json);
        fs.writeFileSync(CONTACTS_FILE, encrypted, { mode: 0o600 });
        return true;
    } catch (e) {
        console.error('📇 Failed to save contacts:', e.message);
        return false;
    }
}

function addContact(name, phone) {
    const contacts = loadContacts();
    const trimmedName = name.trim();

    // Reject non-Latin names
    if (/[^\x00-\x7F]/.test(trimmedName)) {
        return { error: `Contact name must be in English/Latin characters. Got: "${trimmedName}"` };
    }

    if (!phone || !phone.trim()) {
        return { error: 'Phone number is required.' };
    }
    phone = phone.trim();
    if (!phone.startsWith('+')) phone = '+' + phone;
    // Must have at least country code + number (e.g. +8801...)
    if (phone.replace(/[^0-9]/g, '').length < 10) {
        return { error: `Phone number too short. Include country code, e.g. +8801712345678. Got: "${phone}"` };
    }

    const key = trimmedName.toLowerCase();
    contacts[key] = { name: trimmedName, phone: phone };
    saveContacts(contacts);
    return contacts[key];
}

function removeContact(name) {
    const contacts = loadContacts();
    const key = name.toLowerCase().trim();
    if (contacts[key]) {
        delete contacts[key];
        saveContacts(contacts);
        return true;
    }
    return false;
}

function _levenshtein(a, b) {
    const m = a.length, n = b.length;
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    for (let i = 1; i <= m; i++)
        for (let j = 1; j <= n; j++)
            dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
    return dp[m][n];
}

function findContact(name) {
    const contacts = loadContacts();
    const key = name.toLowerCase().trim();

    // Exact match
    if (contacts[key]) return contacts[key];

    // Substring match
    for (const [k, v] of Object.entries(contacts)) {
        if (k.includes(key) || key.includes(k)) return v;
        if (v.name && v.name.toLowerCase().includes(key)) return v;
    }

    // Fuzzy match — Levenshtein distance (handles typos, dropped letters)
    // "rahan" vs "raihan" = distance 1, "abubokkor" vs "abubokkor" = 0
    let bestMatch = null, bestDist = Infinity;
    for (const [k, v] of Object.entries(contacts)) {
        const dist = _levenshtein(key, k);
        // Allow up to 2 edits for short names, 3 for longer names
        const maxDist = Math.max(2, Math.floor(k.length * 0.3));
        if (dist < bestDist && dist <= maxDist) {
            bestDist = dist;
            bestMatch = v;
        }
    }
    return bestMatch;
}

function getAllContacts() {
    return loadContacts();
}

function getContactsFilePath() {
    return CONTACTS_FILE;
}

module.exports = {
    loadContacts,
    saveContacts,
    addContact,
    removeContact,
    findContact,
    getAllContacts,
    getContactsFilePath,
    WISHCRAFT_DIR,
    CONTACTS_FILE
};
