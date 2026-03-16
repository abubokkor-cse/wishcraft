const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('wishcraft', {
    // Platform detection
    platform: process.platform,  // 'darwin', 'win32', 'linux'

    // API Key (encrypted storage)
    getApiKey: () => ipcRenderer.invoke('get-api-key'),
    setApiKey: (key) => ipcRenderer.invoke('set-api-key', key),
    hasApiKey: () => ipcRenderer.invoke('has-api-key'),

    // Settings (encrypted storage)
    getSetting: (key, defaultValue) => ipcRenderer.invoke('get-setting', key, defaultValue),
    setSetting: (key, value) => ipcRenderer.invoke('set-setting', key, value),
    getAllSettings: () => ipcRenderer.invoke('get-all-settings'),

    memory: {
        setUserFact: (key, value) => ipcRenderer.invoke('memory-set-user-fact', key, value),
        getUserFact: (key) => ipcRenderer.invoke('memory-get-user-fact', key),
        getAllFacts: () => ipcRenderer.invoke('memory-get-all-facts'),
        setContext: (key, value) => ipcRenderer.invoke('memory-set-context', key, value),
        getContext: (key) => ipcRenderer.invoke('memory-get-context', key),
        addHistory: (summary) => ipcRenderer.invoke('memory-add-history', summary),
        getHistory: (count) => ipcRenderer.invoke('memory-get-history', count),
        getFull: () => ipcRenderer.invoke('memory-get-full'),
        clear: () => ipcRenderer.invoke('memory-clear'),
    },

    // Chat History (conversation persistence)
    chatHistory: {
        create: (title) => ipcRenderer.invoke('chat-create', title),
        addMessage: (convId, role, text) => ipcRenderer.invoke('chat-add-message', convId, role, text),
        list: () => ipcRenderer.invoke('chat-list'),
        get: (id) => ipcRenderer.invoke('chat-get', id),
        delete: (id) => ipcRenderer.invoke('chat-delete', id),
        rename: (id, title) => ipcRenderer.invoke('chat-rename', id, title),
    },

    // Cloud Sync (encrypted backup to Google Cloud Storage)
    cloud: {
        getDeviceId: () => ipcRenderer.invoke('get-device-id'),
        syncUpload: (fileName) => ipcRenderer.invoke('cloud-sync-upload', fileName),
        syncDownload: (fileName) => ipcRenderer.invoke('cloud-sync-download', fileName),
        syncAll: () => ipcRenderer.invoke('cloud-sync-all'),
        restoreAll: () => ipcRenderer.invoke('cloud-restore-all'),
    },

    // API Mode & Storage Mode
    getApiMode: () => ipcRenderer.invoke('get-api-mode'),
    setApiMode: (mode) => ipcRenderer.invoke('set-api-mode', mode),
    getServerUrl: () => ipcRenderer.invoke('get-server-url'),
    setServerUrl: (url) => ipcRenderer.invoke('set-server-url', url),
    getStorageMode: () => ipcRenderer.invoke('get-storage-mode'),
    setStorageMode: (mode) => ipcRenderer.invoke('set-storage-mode', mode),

    // File reading (for analysis)
    readFileBase64: (path) => ipcRenderer.invoke('read-file-base64', path),
    saveUploadedFile: (base64, path) => ipcRenderer.invoke('save-uploaded-file', base64, path),

    // Screenshot
    takeScreenshot: () => ipcRenderer.invoke('take-screenshot'),
    saveScreenshot: (base64) => ipcRenderer.invoke('save-screenshot', base64),

    // PPTX creation
    createPptx: (slidesJSON, filename) => ipcRenderer.invoke('create-pptx', slidesJSON, filename),

    // Screen info
    getScreenSize: () => ipcRenderer.invoke('get-screen-size'),

    // Execute PyAutoGUI action
    executeAction: (action) => ipcRenderer.send('execute-action', action),

    // Window drag
    moveWindow: (x, y) => ipcRenderer.send('move-window', { x, y }),

    // Genie visibility events (removeAllListeners first to prevent stacking)
    onShowGenie: (callback) => {
        ipcRenderer.removeAllListeners('show-genie');
        ipcRenderer.on('show-genie', callback);
    },
    onHideGenie: (callback) => {
        ipcRenderer.removeAllListeners('hide-genie');
        ipcRenderer.on('hide-genie', callback);
    },

    // Action results from PyAutoGUI (single listener only)
    onActionResult: (callback) => {
        ipcRenderer.removeAllListeners('action-result');
        ipcRenderer.on('action-result', (event, result) => callback(result));
    },

    // Cancel running Computer Use task (writes cancel file directly from Node.js)
    cancelComputerTask: () => ipcRenderer.send('cancel-computer-task'),

    togglePanel: () => ipcRenderer.send('toggle-panel'),

    sendToPanel: (data) => ipcRenderer.send('avatar-to-panel', data),
    sendToAvatar: (data) => ipcRenderer.send('panel-to-avatar', data),
    onFromPanel: (callback) => {
        ipcRenderer.removeAllListeners('from-panel');
        ipcRenderer.on('from-panel', (event, data) => callback(data));
    },
    onFromAvatar: (callback) => {
        ipcRenderer.removeAllListeners('from-avatar');
        ipcRenderer.on('from-avatar', (event, data) => callback(data));
    },

    onShowSection: (callback) => {
        ipcRenderer.removeAllListeners('show-section');
        ipcRenderer.on('show-section', (event, section) => callback(section));
    },

    closePanel: () => ipcRenderer.send('close-panel'),

    // Live Execution Log (progress events from Python)
    onExecutionLog: (callback) => {
        ipcRenderer.removeAllListeners('execution-log');
        ipcRenderer.on('execution-log', (event, data) => callback(data));
    },

    // Contacts
    getContacts: () => ipcRenderer.invoke('get-contacts'),
    addContact: (name, phone) => ipcRenderer.invoke('add-contact', name, phone),
    removeContact: (name) => ipcRenderer.invoke('remove-contact', name),
    findContact: (name) => ipcRenderer.invoke('find-contact', name),
    getContactsPath: () => ipcRenderer.invoke('get-contacts-path'),
    openContactsFolder: () => ipcRenderer.invoke('open-contacts-folder'),

    // Skills
    skills: {
        loadAll: () => ipcRenderer.invoke('skills-load-all'),
        getIndex: () => ipcRenderer.invoke('skills-get-index'),
        getSkill: (name) => ipcRenderer.invoke('skills-get-skill', name),
        match: (userText, maxResults) => ipcRenderer.invoke('skills-match', userText, maxResults),
        getSummary: () => ipcRenderer.invoke('skills-get-summary'),
        getContext: (name) => ipcRenderer.invoke('skills-get-context', name),
    },

    removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});
