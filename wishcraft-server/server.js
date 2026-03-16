/**
 * WishCraft Cloud Run Backend
 *
 * Endpoints (12):
 * - GET  /api/health               → Health check
 * - POST /api/token                → Issue ephemeral session token
 * - GET  /api/gemini-key           → Returns API key (requires valid token)
 * - POST /api/computer-use         → Runs Computer Use agent loop
 * - POST /api/wishes               → Save wish to Firestore
 * - GET  /api/wishes               → Get wish history
 * - POST /api/cloud-sync/upload    → Upload encrypted backup to Cloud Storage
 * - POST /api/cloud-sync/download  → Download encrypted backup from Cloud Storage
 * - GET  /api/credits/packages     → Available credit packages
 * - GET  /api/credits/balance      → Get user credit balance
 * - POST /api/credits/purchase     → Purchase credits (Stripe test mode)
 * - POST /api/credits/use          → Deduct credits
 */

const express = require('express');
const cors = require('cors');
const crypto = require('crypto');
const { spawn } = require('child_process');
const path = require('path');

try { require('dotenv').config(); } catch (e) { }

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' })); // Large payloads for screenshots

// GCP credentials available? (Application Default Credentials or explicit env var)
const hasGcpCredentials = !!(
    process.env.GOOGLE_APPLICATION_CREDENTIALS ||
    process.env.GOOGLE_CLOUD_PROJECT ||
    process.env.GCLOUD_PROJECT ||
    process.env.K_SERVICE // Cloud Run sets this automatically
);

// Firestore (optional — for wish history + credits)
let db = null;
if (hasGcpCredentials) {
    try {
        const { Firestore } = require('@google-cloud/firestore');
        db = new Firestore();
        console.log('🗄️ Firestore ready');
    } catch (e) {
        console.log('⚠️ Firestore init failed:', e.message);
    }
} else {
    console.log('⚠️ Firestore skipped (no GCP credentials — local mode)');
}

// Cloud Storage (optional — for encrypted sync)
let storage = null;
let bucket = null;
if (hasGcpCredentials) {
    try {
        const { Storage } = require('@google-cloud/storage');
        storage = new Storage();
        const BUCKET_NAME = process.env.GCS_BUCKET || 'wishcraft-sync';
        bucket = storage.bucket(BUCKET_NAME);
        console.log('☁️ Cloud Storage ready:', BUCKET_NAME);
    } catch (e) {
        console.log('⚠️ Cloud Storage init failed:', e.message);
    }
} else {
    console.log('⚠️ Cloud Storage skipped (no GCP credentials — local mode)');
}

// Ephemeral Token Store (in-memory, short-lived)
const tokenStore = new Map(); // token → { createdAt, expiresAt, deviceId }
const TOKEN_TTL_MS = 5 * 60 * 1000; // 5 minutes

function cleanExpiredTokens() {
    const now = Date.now();
    for (const [token, meta] of tokenStore) {
        if (now > meta.expiresAt) tokenStore.delete(token);
    }
}
setInterval(cleanExpiredTokens, 60 * 1000);

// Health Check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'wishcraft-server',
        version: '1.1.0',
        timestamp: new Date().toISOString(),
        geminiApiKey: process.env.GEMINI_API_KEY ? 'configured' : 'missing',
        firestore: db ? 'connected' : 'unavailable',
        cloudStorage: bucket ? 'connected' : 'unavailable'
    });
});

// Ephemeral Token Endpoint
// The raw Gemini API key NEVER leaves the server.
// Client gets a short-lived token to prove it's authorized.
app.post('/api/token', (req, res) => {
    const { deviceId } = req.body;
    if (!deviceId || typeof deviceId !== 'string' || deviceId.length > 256) {
        return res.status(400).json({ error: 'Invalid deviceId' });
    }

    if (!process.env.GEMINI_API_KEY) {
        return res.status(503).json({ error: 'Server API key not configured' });
    }

    // Generate ephemeral token
    const token = crypto.randomBytes(32).toString('hex');
    const now = Date.now();
    tokenStore.set(token, {
        createdAt: now,
        expiresAt: now + TOKEN_TTL_MS,
        deviceId
    });

    res.json({
        token,
        expiresIn: TOKEN_TTL_MS / 1000,
        apiKeyHint: process.env.GEMINI_API_KEY.slice(0, 8) + '...'
    });
});

// Validate ephemeral token — returns the real API key if valid (internal use only)
function validateToken(token) {
    if (!token) return null;
    const meta = tokenStore.get(token);
    if (!meta) return null;
    if (Date.now() > meta.expiresAt) {
        tokenStore.delete(token);
        return null;
    }
    return process.env.GEMINI_API_KEY;
}

// Middleware: extract API key from token or direct header
function resolveApiKey(req, res, next) {
    // Priority: ephemeral token > direct API key header
    const authHeader = req.headers.authorization || '';
    const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;

    if (bearerToken) {
        const key = validateToken(bearerToken);
        if (key) {
            req.geminiApiKey = key;
            return next();
        }
    }

    // Fallback: server's own key (for direct server calls)
    if (process.env.GEMINI_API_KEY) {
        req.geminiApiKey = process.env.GEMINI_API_KEY;
        return next();
    }

    return res.status(401).json({ error: 'No valid API key or token' });
}

// Computer Use Endpoint
app.post('/api/computer-use', resolveApiKey, async (req, res) => {
    const { goal, screenshot, screenWidth, screenHeight, scaleFactor } = req.body;

    if (!goal) {
        return res.status(400).json({ error: 'Missing goal parameter' });
    }

    try {
        const result = await runComputerUse(goal, screenshot, screenWidth, screenHeight, scaleFactor, req.geminiApiKey);
        res.json(result);
    } catch (error) {
        console.error('Computer Use error:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Run the Python Computer Use agent loop.
 * Sends screenshot + goal, gets back a list of actions to execute.
 */
function runComputerUse(goal, screenshot, screenWidth, screenHeight, scaleFactor, apiKey) {
    return new Promise((resolve, reject) => {
        const pythonPath = process.env.PYTHON_PATH || 'python3';
        const scriptPath = path.join(__dirname, 'computer_use.py');

        const input = JSON.stringify({
            goal,
            screenshot,
            screen_width: screenWidth || 1440,
            screen_height: screenHeight || 900,
            scale_factor: scaleFactor || 1,
            api_key: apiKey
        });

        const python = spawn(pythonPath, [scriptPath], {
            env: { ...process.env }
        });

        let stdout = '';
        let stderr = '';

        python.stdin.write(input);
        python.stdin.end();

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
            console.error('Python stderr:', data.toString());
        });

        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Python exited with code ${code}: ${stderr}`));
                return;
            }

            try {
                const lines = stdout.trim().split('\n').filter(l => l.trim());
                const lastLine = lines[lines.length - 1];
                const result = JSON.parse(lastLine);
                resolve(result);
            } catch (e) {
                reject(new Error(`Failed to parse Python output: ${stdout}`));
            }
        });

        // Timeout after 30 seconds
        setTimeout(() => {
            python.kill();
            reject(new Error('Computer Use timed out after 30s'));
        }, 30000);
    });
}

// Cloud Sync Endpoints (encrypted backup)
app.post('/api/cloud-sync/upload', resolveApiKey, async (req, res) => {
    const { deviceId, fileName, encryptedData } = req.body;
    if (!deviceId || !fileName || !encryptedData) {
        return res.status(400).json({ error: 'Missing deviceId, fileName, or encryptedData' });
    }

    const safeFileName = path.basename(fileName);
    if (safeFileName !== fileName || fileName.includes('..')) {
        return res.status(400).json({ error: 'Invalid fileName' });
    }

    if (!bucket) {
        return res.json({ success: true, message: 'Cloud Storage not available (stored locally only)' });
    }

    try {
        const filePath = `users/${deviceId}/${safeFileName}`;
        const file = bucket.file(filePath);
        await file.save(encryptedData, {
            contentType: 'application/octet-stream',
            metadata: {
                cacheControl: 'no-cache',
                metadata: { uploadedAt: new Date().toISOString() }
            }
        });
        res.json({ success: true, path: filePath });
    } catch (error) {
        console.error('Cloud sync upload error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/cloud-sync/download', resolveApiKey, async (req, res) => {
    const { deviceId, fileName } = req.body;
    if (!deviceId || !fileName) {
        return res.status(400).json({ error: 'Missing deviceId or fileName' });
    }

    const safeFileName = path.basename(fileName);
    if (safeFileName !== fileName || fileName.includes('..')) {
        return res.status(400).json({ error: 'Invalid fileName' });
    }

    if (!bucket) {
        return res.json({ success: false, message: 'Cloud Storage not available' });
    }

    try {
        const filePath = `users/${deviceId}/${safeFileName}`;
        const file = bucket.file(filePath);
        const [exists] = await file.exists();
        if (!exists) {
            return res.json({ success: false, message: 'File not found in cloud' });
        }
        const [contents] = await file.download();
        res.json({ success: true, encryptedData: contents.toString() });
    } catch (error) {
        console.error('Cloud sync download error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Credits System (managed API key usage)

const CREDIT_PACKAGES = {
    small:  { id: 'small',  name: '55 Credits',  credits: 50,  bonus: 5,  price: 2.99 },
    medium: { id: 'medium', name: '175 Credits', credits: 150, bonus: 25, price: 7.99 },
    large:  { id: 'large',  name: '480 Credits', credits: 400, bonus: 80, price: 19.99 },
};

app.get('/api/credits/packages', (req, res) => {
    res.json({ packages: CREDIT_PACKAGES });
});

app.get('/api/credits/balance', async (req, res) => {
    const deviceId = req.query.deviceId;
    if (!deviceId) return res.status(400).json({ error: 'Missing deviceId' });

    if (!db) {
        return res.json({ credits: 0, message: 'Firestore unavailable' });
    }

    try {
        const doc = await db.collection('credits').doc(deviceId).get();
        const balance = doc.exists ? (doc.data().balance || 0) : 0;
        res.json({ credits: balance });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/credits/use', resolveApiKey, async (req, res) => {
    const { deviceId, amount } = req.body;
    if (!deviceId || !amount || amount <= 0) {
        return res.status(400).json({ error: 'Invalid deviceId or amount' });
    }

    if (!db) {
        return res.json({ success: true, remaining: 0, message: 'Credits not tracked (Firestore offline)' });
    }

    try {
        const ref = db.collection('credits').doc(deviceId);
        const doc = await ref.get();
        const current = doc.exists ? (doc.data().balance || 0) : 0;

        if (current < amount) {
            return res.status(402).json({ error: 'Insufficient credits', balance: current });
        }

        const remaining = current - amount;
        await ref.set({ balance: remaining, lastUsed: new Date().toISOString() }, { merge: true });
        res.json({ success: true, remaining });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/credits/purchase', async (req, res) => {
    const { deviceId, packageId, paymentMethodId } = req.body;
    if (!deviceId || !packageId) {
        return res.status(400).json({ error: 'Missing deviceId or packageId' });
    }

    const pkg = CREDIT_PACKAGES[packageId];
    if (!pkg) return res.status(400).json({ error: 'Invalid package' });

    const totalCredits = pkg.credits + pkg.bonus;

    if (!db) {
        return res.json({ success: true, creditsAdded: totalCredits, newBalance: totalCredits, message: 'Test mode (Firestore offline)' });
    }

    try {
        const ref = db.collection('credits').doc(deviceId);
        const doc = await ref.get();
        const current = doc.exists ? (doc.data().balance || 0) : 0;
        const newBalance = current + totalCredits;

        await ref.set({
            balance: newBalance,
            lastPurchase: new Date().toISOString(),
            lastPackage: packageId
        }, { merge: true });

        // Log transaction
        await db.collection('transactions').add({
            deviceId,
            packageId,
            creditsAdded: totalCredits,
            amount: pkg.price,
            paymentMethodId: paymentMethodId || 'test',
            timestamp: new Date().toISOString()
        });

        res.json({ success: true, creditsAdded: totalCredits, newBalance: newBalance, message: `Added ${totalCredits} credits` });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Wish History Endpoints
app.post('/api/wishes', async (req, res) => {
    const { wish, result, timestamp } = req.body;

    if (!db) {
        return res.json({ success: true, message: 'Wish recorded (Firestore not available)' });
    }

    try {
        const docRef = await db.collection('wishes').add({
            wish,
            result,
            timestamp: timestamp || new Date().toISOString(),
            createdAt: new Date()
        });
        res.json({ success: true, id: docRef.id });
    } catch (error) {
        console.error('Firestore error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/wishes', async (req, res) => {
    if (!db) {
        return res.json({ wishes: [] });
    }

    try {
        const snapshot = await db.collection('wishes')
            .orderBy('createdAt', 'desc')
            .limit(20)
            .get();

        const wishes = [];
        snapshot.forEach(doc => wishes.push({ id: doc.id, ...doc.data() }));
        res.json({ wishes });
    } catch (error) {
        console.error('Firestore error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Gemini API Key Proxy (for Electron client — requires valid ephemeral token)
app.get('/api/gemini-key', (req, res) => {
    const authHeader = req.headers.authorization || '';
    const bearerToken = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;

    if (bearerToken) {
        const key = validateToken(bearerToken);
        if (key) return res.json({ apiKey: key });
    }

    // No valid token — reject (don't fallback to server key for this sensitive endpoint)
    return res.status(401).json({ error: 'Valid ephemeral token required. POST /api/token first.' });
});

app.listen(PORT, () => {
    console.log(`\n✨ WishCraft Server running on port ${PORT}`);
    console.log(`   Health:       GET  http://localhost:${PORT}/api/health`);
    console.log(`   Token:        POST http://localhost:${PORT}/api/token`);
    console.log(`   Gemini Key:   GET  http://localhost:${PORT}/api/gemini-key`);
    console.log(`   Computer Use: POST http://localhost:${PORT}/api/computer-use`);
    console.log(`   Cloud Sync:   POST http://localhost:${PORT}/api/cloud-sync/upload`);
    console.log(`   Packages:     GET  http://localhost:${PORT}/api/credits/packages`);
    console.log(`   Credits:      GET  http://localhost:${PORT}/api/credits/balance`);
    console.log(`   Purchase:     POST http://localhost:${PORT}/api/credits/purchase`);
    console.log(`   Wishes:       GET  http://localhost:${PORT}/api/wishes\n`);
});
