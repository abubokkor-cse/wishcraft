const { app, BrowserWindow, Tray, Menu, screen, ipcMain, globalShortcut, desktopCapturer } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  console.log('Another instance already running. Quitting.');
  app.quit();
}

try {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf-8');
    envContent.split('\n').forEach(line => {
      const [key, ...val] = line.split('=');
      if (key && val.length) process.env[key.trim()] = val.join('=').trim();
    });
  }
} catch (e) { console.warn('No .env file'); }

// Encrypted config store (API key, settings, memory)
const configStore = require('./config-store');

// Skill registry (discovers and loads skills from skills/ directory and reference repos)
const { getRegistry } = require('./skills/skill-registry');
const skillRegistry = getRegistry(path.join(__dirname, 'skills'));

// API key priority: encrypted store > .env > empty
function getApiKey() {
  const stored = configStore.getApiKey();
  if (stored) return stored;
  // Migrate from .env if exists
  const envKey = process.env.GEMINI_API_KEY || '';
  if (envKey) {
    configStore.setApiKey(envKey);
    console.log('🔐 Migrated API key from .env to encrypted store');
  }
  return envKey;
}

let avatarWindow;
let panelWindow;
let tray;
let isGenieVisible = false;
let isPanelOpen = false;
let pythonProcess = null;

function startPythonBridge() {
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  const scriptPath = path.join(__dirname, 'python', 'executor.py');
  const pythonEnv = { ...process.env, GEMINI_API_KEY: getApiKey() };
  pythonProcess = spawn(pythonPath, [scriptPath], { stdio: ['pipe', 'pipe', 'pipe'], env: pythonEnv });

  pythonProcess.stdout.on('data', (data) => {
    data.toString().split('\n').filter(l => l.trim()).forEach(line => {
      try {
        const result = JSON.parse(line);
        const logSafe = { ...result };
        delete logSafe.api_key;
        delete logSafe.screenshot;
        console.log('🐍 PyAutoGUI:', logSafe);

        // Progress logs → panel only (Live Execution Log)
        if (result.progress) {
          if (panelWindow && !panelWindow.isDestroyed()) {
            panelWindow.webContents.send('execution-log', result);
          }
          return;
        }

        // Final results → avatar (for tool call responses)
        if (avatarWindow && !avatarWindow.isDestroyed()) {
          avatarWindow.webContents.send('action-result', result);
        }
      } catch (e) { console.log('🐍', line); }
    });
  });

  pythonProcess.stderr.on('data', d => console.error('🐍 Error:', d.toString()));
  pythonProcess.on('close', code => { console.log(`🐍 Exited: ${code}`); pythonProcess = null; });
  console.log('🐍 Python bridge started');
}

function sendToPython(action) {
  if (pythonProcess && pythonProcess.stdin.writable) {
    pythonProcess.stdin.write(JSON.stringify(action) + '\n');
  }
}

async function captureScreenshot() {
  try {
    const sources = await desktopCapturer.getSources({ types: ['screen'], thumbnailSize: { width: 1440, height: 900 } });
    if (sources.length > 0) return sources[0].thumbnail.toJPEG(40).toString('base64');
  } catch (e) { console.error('📸 Error:', e); }
  return null;
}

function createAvatarWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  avatarWindow = new BrowserWindow({
    width: 280, height: 380,
    x: width - 320, y: height - 420,
    transparent: true, frame: false,
    alwaysOnTop: true, skipTaskbar: true,
    resizable: false, hasShadow: false, focusable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
      backgroundThrottling: false
    }
  });

  avatarWindow.loadFile(path.join(__dirname, 'renderer', 'avatar.html'));
  if (process.argv.includes('--dev')) avatarWindow.webContents.openDevTools({ mode: 'detach' });
  avatarWindow.setIgnoreMouseEvents(false);
  avatarWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  avatarWindow.setAlwaysOnTop(true, 'screen-saver', 1);
  avatarWindow.hide();
}

function createPanelWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  panelWindow = new BrowserWindow({
    width: 380, height: 520,
    x: Math.round((width - 380) / 2), y: Math.round((height - 520) / 2),
    transparent: true, frame: false,
    alwaysOnTop: true, skipTaskbar: true,
    resizable: true, hasShadow: false, focusable: true,
    minWidth: 320, minHeight: 400, show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
      backgroundThrottling: false
    }
  });

  panelWindow.loadFile(path.join(__dirname, 'renderer', 'panel.html'));
  panelWindow.setVisibleOnAllWorkspaces(true);
  panelWindow.setAlwaysOnTop(true, 'floating', 1);

  panelWindow.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      panelWindow.hide();
      isPanelOpen = false;
    }
  });
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'assets', 'lamp-icon.png'));
  tray.setToolTip('WishCraft — Click to summon your genie!');

  // Click lamp: summon genie if hidden, show menu if visible
  tray.on('click', () => {
    if (!isGenieVisible) {
      summonGenie();
    } else {
      const menu = Menu.buildFromTemplate([
        { label: '💬 Open Chat Panel', click: () => togglePanel() },
        { label: '📋 Tasks', click: () => showTasks() },
        { label: '⚙️ Settings', click: () => showSettings() },
        { label: '💤 Dismiss Genie', click: () => dismissGenie() },
        { type: 'separator' },
        { label: '❌ Quit', click: () => { app.isQuitting = true; app.quit(); } }
      ]);
      tray.popUpContextMenu(menu);
    }
  });

  // Right-click always shows full menu
  tray.on('right-click', () => {
    const menu = Menu.buildFromTemplate([
      { label: '🧞 Summon Genie', click: () => summonGenie() },
      { label: '💬 Open Chat Panel', click: () => togglePanel() },
      { label: '📋 Tasks', click: () => showTasks() },
      { label: '⚙️ Settings', click: () => showSettings() },
      { label: '💤 Dismiss Genie', click: () => dismissGenie() },
      { type: 'separator' },
      { label: '❌ Quit', click: () => { app.isQuitting = true; app.quit(); } }
    ]);
    tray.popUpContextMenu(menu);
  });
}

function showTasks() {
  if (!isPanelOpen) { panelWindow.show(); panelWindow.focus(); isPanelOpen = true; }
  panelWindow.webContents.send('show-section', 'tasks');
  // Request tasks from avatar
  if (avatarWindow && !avatarWindow.isDestroyed()) {
    avatarWindow.webContents.send('from-panel', { type: 'get-tasks' });
  }
}

function showSettings() {
  if (!isPanelOpen) { panelWindow.show(); panelWindow.focus(); isPanelOpen = true; }
  panelWindow.webContents.send('show-section', 'settings');
}

function summonGenie() {
  if (isGenieVisible) return;
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  avatarWindow.setPosition(width - 320, height - 420);
  avatarWindow.show();
  avatarWindow.webContents.send('show-genie');
  isGenieVisible = true;
}

function dismissGenie() {
  if (!isGenieVisible) return;
  avatarWindow.webContents.send('hide-genie');
  setTimeout(() => {
    avatarWindow.hide();
    isGenieVisible = false;
  }, 800);
}

function togglePanel() {
  if (isPanelOpen) {
    panelWindow.hide();
    isPanelOpen = false;
  } else {
    panelWindow.show();
    panelWindow.focus();
    isPanelOpen = true;
  }
}

ipcMain.on('move-window', (event, { x, y }) => {
  const win = BrowserWindow.fromWebContents(event.sender);
  if (win) { const [cx, cy] = win.getPosition(); win.setPosition(cx + x, cy + y); }
});

ipcMain.handle('read-file-base64', async (event, filePath) => {
  try {
    const path = require('path');
    const fs = require('fs');
    let resolved = filePath;
    if (resolved.startsWith('~')) resolved = resolved.replace('~', require('os').homedir());
    resolved = path.resolve(resolved);
    // Security: block paths outside user home
    const home = require('os').homedir();
    if (!resolved.startsWith(home) && !resolved.startsWith('/tmp')) {
      return { error: 'Access denied: can only read files under home directory' };
    }
    if (!fs.existsSync(resolved)) return { error: 'File not found: ' + filePath };
    const stats = fs.statSync(resolved);
    if (stats.size > 20 * 1024 * 1024) return { error: 'File too large (max 20MB)' };
    const buffer = fs.readFileSync(resolved);
    const base64 = buffer.toString('base64');
    const ext = path.extname(resolved).toLowerCase();
    const mimeMap = {
      '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
      '.gif': 'image/gif', '.webp': 'image/webp', '.bmp': 'image/bmp',
      '.pdf': 'application/pdf', '.txt': 'text/plain', '.md': 'text/markdown',
      '.csv': 'text/csv', '.json': 'application/json', '.xml': 'text/xml',
      '.html': 'text/html', '.htm': 'text/html',
      '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
      '.m4a': 'audio/mp4', '.aac': 'audio/aac', '.flac': 'audio/flac',
      '.wma': 'audio/x-ms-wma', '.webm': 'audio/webm',
      '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
      '.mkv': 'video/x-matroska',
    };
    const mimeType = mimeMap[ext] || 'application/octet-stream';
    return { base64, mimeType, size: stats.size, path: resolved, ext };
  } catch (e) { return { error: e.message }; }
});

ipcMain.handle('save-uploaded-file', async (event, base64Data, filePath) => {
  try {
    const fs = require('fs');
    const resolved = path.resolve(filePath);
    // Only allow saving to /tmp for security
    if (!resolved.startsWith('/tmp')) {
      return { error: 'Can only save uploaded files to /tmp' };
    }
    const buffer = Buffer.from(base64Data, 'base64');
    fs.writeFileSync(resolved, buffer);
    return { success: true, path: resolved, size: buffer.length };
  } catch (e) { return { error: e.message }; }
});

ipcMain.handle('take-screenshot', async () => await captureScreenshot());

// ── PPTX Creation (PptxGenJS) ──
ipcMain.handle('create-pptx', async (event, slidesData, filename) => {
  try {
    const PptxGenJS = require('pptxgenjs');
    const pres = new PptxGenJS();
    pres.layout = 'LAYOUT_16x9';
    pres.title = slidesData.title || 'Presentation';
    pres.author = 'WishCraft';

    const theme = slidesData.theme || {};
    const SLIDE_W = 10, SLIDE_H = 5.625;
    const totalSlides = (slidesData.slides || []).length;

    function addFooterBar(slide, slideNum) {
      const primary = (theme.primary || '1E2761').replace('#', '');
      const accent = (theme.accent || 'F9A825').replace('#', '');
      slide.addShape(pres.shapes.RECTANGLE, {
        x: 0, y: 5.35, w: SLIDE_W, h: 0.275,
        fill: { color: primary }, line: { color: primary }
      });
      slide.addText(slidesData.title || 'Presentation', {
        x: 0.2, y: 5.36, w: 8.5, h: 0.22,
        fontSize: 7.5, fontFace: theme.fontBody || 'Calibri', color: 'AABBD6',
        align: 'left', valign: 'middle'
      });
      slide.addText(`${slideNum} / ${totalSlides}`, {
        x: 9.0, y: 5.36, w: 0.8, h: 0.22,
        fontSize: 7.5, fontFace: theme.fontBody || 'Calibri', color: accent,
        align: 'right', valign: 'middle', bold: true
      });
    }

    let slideNum = 0;
    for (const slideData of (slidesData.slides || [])) {
      slideNum++;
      const slide = pres.addSlide();

      if (slideData.background) {
        slide.background = { color: slideData.background.replace('#', '') };
      }

      for (const elem of (slideData.elements || [])) {
        const baseOpts = {
          x: elem.x ?? 0.5,
          y: elem.y ?? 0.5,
          w: elem.w || 9,
          h: elem.h || 1,
        };

        switch (elem.type) {
          case 'text': {
            slide.addText(elem.text || '', {
              ...baseOpts,
              fontSize: elem.fontSize || 18,
              fontFace: elem.fontFace || theme.fontBody || 'Calibri',
              color: (elem.color || '363636').replace('#', ''),
              bold: elem.bold || false,
              italic: elem.italic || false,
              align: elem.align || 'left',
              valign: elem.valign || 'top',
              margin: elem.margin !== undefined ? elem.margin : undefined,
            });
            break;
          }
          case 'bullets': {
            const items = (elem.items || []).map((item, i, arr) => ({
              text: typeof item === 'string' ? item : item.text || '',
              options: {
                bullet: true,
                breakLine: i < arr.length - 1,
                fontSize: elem.fontSize || 14,
                color: (elem.color || '363636').replace('#', ''),
                indentLevel: (typeof item === 'object' && item.indent) ? item.indent : 0,
              }
            }));
            slide.addText(items, {
              ...baseOpts,
              fontFace: elem.fontFace || theme.fontBody || 'Calibri',
              paraSpaceAfter: 6,
            });
            break;
          }
          case 'shape': {
            const shapeType = pres.shapes[elem.shape] || pres.shapes.RECTANGLE;
            const shapeOpts = { ...baseOpts };
            if (elem.fill) shapeOpts.fill = { color: elem.fill.replace('#', '') };
            if (elem.lineColor) shapeOpts.line = { color: elem.lineColor.replace('#', ''), width: elem.lineWidth || 1 };
            if (elem.transparency !== undefined) shapeOpts.fill = { ...(shapeOpts.fill || {}), transparency: elem.transparency };
            if (elem.shadow) shapeOpts.shadow = { type: 'outer', color: '000000', blur: 4, offset: 1, angle: 135, opacity: 0.08 };
            slide.addShape(shapeType, shapeOpts);
            break;
          }
          case 'card': {
            const cardFill = (elem.fill || 'FFFFFF').replace('#', '');
            const cardBorder = (elem.borderColor || 'C5D0E8').replace('#', '');
            slide.addShape(pres.shapes.RECTANGLE, {
              ...baseOpts,
              fill: { color: cardFill },
              line: { color: cardBorder, pt: 1 },
              shadow: { type: 'outer', color: '000000', blur: 4, offset: 1, angle: 135, opacity: 0.08 }
            });
            if (elem.accentColor) {
              slide.addShape(pres.shapes.RECTANGLE, {
                x: baseOpts.x, y: baseOpts.y, w: baseOpts.w, h: 0.06,
                fill: { color: elem.accentColor.replace('#', '') },
                line: { color: elem.accentColor.replace('#', '') }
              });
            }
            if (elem.title) {
              slide.addText(elem.title, {
                x: baseOpts.x + 0.15, y: baseOpts.y + 0.12, w: baseOpts.w - 0.3, h: 0.35,
                fontSize: elem.titleSize || 12, fontFace: theme.fontHeader || 'Georgia',
                color: (elem.titleColor || theme.primary || '1E2761').replace('#', ''), bold: true
              });
            }
            if (elem.text) {
              const textY = elem.title ? baseOpts.y + 0.5 : baseOpts.y + 0.15;
              slide.addText(elem.text, {
                x: baseOpts.x + 0.15, y: textY, w: baseOpts.w - 0.3, h: baseOpts.h - (textY - baseOpts.y) - 0.1,
                fontSize: elem.fontSize || 11, fontFace: theme.fontBody || 'Calibri',
                color: (elem.color || '546E7A').replace('#', '')
              });
            }
            break;
          }
          case 'section_header': {
            const headerColor = (elem.fill || theme.primary || '1E2761').replace('#', '');
            slide.addShape(pres.shapes.RECTANGLE, {
              x: 0, y: baseOpts.y, w: SLIDE_W, h: elem.h || 0.6,
              fill: { color: headerColor }, line: { color: headerColor }
            });
            slide.addText(elem.text || '', {
              x: 0.3, y: baseOpts.y, w: 9.4, h: elem.h || 0.6,
              fontSize: elem.fontSize || 16, fontFace: theme.fontHeader || 'Georgia',
              color: (elem.color || 'FFFFFF').replace('#', ''),
              bold: true, align: 'left', valign: 'middle'
            });
            break;
          }
          case 'stat_box': {
            const boxColor = (elem.fill || 'FFFFFF').replace('#', '');
            slide.addShape(pres.shapes.RECTANGLE, {
              ...baseOpts,
              fill: { color: boxColor },
              line: { color: (elem.borderColor || 'C5D0E8').replace('#', ''), pt: 1 },
              shadow: { type: 'outer', color: '000000', blur: 4, offset: 1, angle: 135, opacity: 0.08 }
            });
            if (elem.accentColor) {
              slide.addShape(pres.shapes.RECTANGLE, {
                x: baseOpts.x, y: baseOpts.y, w: baseOpts.w, h: 0.06,
                fill: { color: elem.accentColor.replace('#', '') },
                line: { color: elem.accentColor.replace('#', '') }
              });
            }
            if (elem.value) {
              slide.addText(elem.value, {
                x: baseOpts.x, y: baseOpts.y + 0.15, w: baseOpts.w, h: 0.5,
                fontSize: elem.valueSize || 28, fontFace: theme.fontHeader || 'Georgia',
                color: (elem.valueColor || theme.primary || '1E2761').replace('#', ''),
                bold: true, align: 'center'
              });
            }
            if (elem.label) {
              slide.addText(elem.label, {
                x: baseOpts.x + 0.1, y: baseOpts.y + 0.7, w: baseOpts.w - 0.2, h: baseOpts.h - 0.8,
                fontSize: elem.labelSize || 10, fontFace: theme.fontBody || 'Calibri',
                color: (elem.labelColor || '546E7A').replace('#', ''), align: 'center'
              });
            }
            break;
          }
          case 'table': {
            const rows = elem.rows || [];
            const tableOpts = { ...baseOpts };
            if (elem.border !== false) tableOpts.border = { pt: 1, color: (elem.borderColor || '999999').replace('#', '') };
            if (elem.colW) tableOpts.colW = elem.colW;
            if (elem.headerFill) {
              const styledRows = rows.map((row, ri) =>
                row.map(cell => {
                  const cellText = typeof cell === 'string' ? cell : (cell.text || cell);
                  return ri === 0 ? { text: cellText, options: { fill: { color: elem.headerFill.replace('#', '') }, color: 'FFFFFF', bold: true, fontSize: 11 } } : { text: cellText, options: { fontSize: 10 } };
                })
              );
              slide.addTable(styledRows, tableOpts);
            } else {
              slide.addTable(rows, tableOpts);
            }
            break;
          }
          case 'chart': {
            const chartType = pres.charts[elem.chartType] || pres.charts.BAR;
            slide.addChart(chartType, elem.data || [], {
              ...baseOpts,
              barDir: elem.barDir || 'col',
              showTitle: !!elem.chartTitle,
              title: elem.chartTitle || '',
              showValue: elem.showValue || false,
              chartColors: elem.colors ? elem.colors.map(c => c.replace('#', '')) : undefined,
              chartArea: { fill: { color: 'FFFFFF' }, roundedCorners: true },
              valGridLine: { color: 'E2E8F0', size: 0.5 },
              catGridLine: { style: 'none' },
              showLegend: elem.showLegend !== false,
            });
            break;
          }
          case 'image': {
            const imgOpts = { ...baseOpts };
            if (elem.data) {
              imgOpts.data = elem.data;
            } else if (elem.path) {
              let imgPath = elem.path;
              if (imgPath.startsWith('~')) imgPath = imgPath.replace('~', require('os').homedir());
              imgPath = require('path').resolve(imgPath);
              if (require('fs').existsSync(imgPath)) {
                const imgBuf = require('fs').readFileSync(imgPath);
                const imgExt = require('path').extname(imgPath).toLowerCase().replace('.', '');
                const imgMime = imgExt === 'jpg' ? 'jpeg' : imgExt;
                imgOpts.data = `image/${imgMime};base64,${imgBuf.toString('base64')}`;
              }
            }
            if (elem.rounding) imgOpts.rounding = true;
            if (elem.shadow) imgOpts.shadow = { type: 'outer', color: '000000', blur: 4, offset: 1, angle: 135, opacity: 0.1 };
            if (imgOpts.data || imgOpts.path) slide.addImage(imgOpts);

            if (elem.caption) {
              slide.addText(elem.caption, {
                x: baseOpts.x, y: baseOpts.y + baseOpts.h + 0.05, w: baseOpts.w, h: 0.3,
                fontSize: 9, fontFace: theme.fontBody || 'Calibri',
                color: '546E7A', align: 'center', italic: true
              });
            }
            break;
          }
        }
      }

      if (slideData.footer !== false && slideNum > 1) {
        addFooterBar(slide, slideNum);
      }
    }

    const desktopPath = require('os').homedir() + '/Desktop';
    const safeName = (filename || 'Presentation').replace(/[^a-zA-Z0-9_\- ]/g, '');
    const filePath = require('path').join(desktopPath, safeName + '.pptx');

    await pres.writeFile({ fileName: filePath });
    return { success: true, path: filePath, message: `Presentation saved: ${safeName}.pptx` };
  } catch (e) {
    console.error('PPTX creation error:', e);
    return { success: false, error: e.message };
  }
});
ipcMain.handle('save-screenshot', async (event, base64Data) => {
  try {
    const desktopPath = require('os').homedir() + '/Desktop';
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filePath = desktopPath + '/Screenshot_' + timestamp + '.png';
    const buffer = Buffer.from(base64Data, 'base64');
    require('fs').writeFileSync(filePath, buffer);
    const { shell } = require('electron');
    shell.showItemInFolder(filePath);
    return filePath;
  } catch (e) { console.error('📸 Save error:', e); return null; }
});
ipcMain.on('execute-action', (event, action) => {
  const safeAction = { ...action };
  delete safeAction.api_key;
  sendToPython(safeAction);
});
// Cancel running Computer Use task directly from Node.js (bypasses blocked Python stdin)
ipcMain.on('cancel-computer-task', () => {
  const fs = require('fs');
  try {
    fs.writeFileSync('/tmp/wishcraft_cancel', 'cancel');
    console.log('🛑 Cancel file written');
  } catch (e) {
    console.error('🛑 Failed to write cancel file:', e);
  }
});
ipcMain.handle('get-screen-size', () => {
  const d = screen.getPrimaryDisplay();
  return { width: d.size.width, height: d.size.height, scaleFactor: d.scaleFactor };
});
ipcMain.handle('get-api-key', () => getApiKey());
ipcMain.handle('set-api-key', (event, apiKey) => {
  const success = configStore.setApiKey(apiKey);
  return { success, message: success ? 'API key saved securely' : 'Failed to save' };
});
ipcMain.handle('has-api-key', () => !!getApiKey());

// Settings IPC
ipcMain.handle('get-setting', (event, key, defaultValue) => configStore.getSetting(key, defaultValue));
ipcMain.handle('set-setting', (event, key, value) => configStore.setSetting(key, value));
ipcMain.handle('get-all-settings', () => configStore.getAllSettings());

// Memory IPC
ipcMain.handle('memory-set-user-fact', (event, key, value) => configStore.setUserFact(key, value));
ipcMain.handle('memory-get-user-fact', (event, key) => configStore.getUserFact(key));
ipcMain.handle('memory-get-all-facts', () => configStore.getAllUserFacts());
ipcMain.handle('memory-set-context', (event, key, value) => configStore.setContext(key, value));
ipcMain.handle('memory-get-context', (event, key) => configStore.getContext(key));
ipcMain.handle('memory-add-history', (event, summary) => configStore.addHistoryEntry(summary));
ipcMain.handle('memory-get-history', (event, count) => configStore.getHistory(count || 10));
ipcMain.handle('memory-get-full', () => configStore.getFullMemory());
ipcMain.handle('memory-clear', () => configStore.clearMemory());

// Chat History IPC
ipcMain.handle('chat-create', (event, title) => configStore.chatCreate(title));
ipcMain.handle('chat-add-message', (event, convId, role, text) => configStore.chatAddMessage(convId, role, text));
ipcMain.handle('chat-list', () => configStore.chatListConversations());
ipcMain.handle('chat-get', (event, id) => configStore.chatGetConversation(id));
ipcMain.handle('chat-delete', (event, id) => configStore.chatDeleteConversation(id));
ipcMain.handle('chat-rename', (event, id, title) => configStore.chatRenameConversation(id, title));

// Cloud Sync IPC
ipcMain.handle('get-device-id', () => configStore.getDeviceId());
ipcMain.handle('cloud-sync-upload', (event, fileName) => {
  const serverUrl = configStore.getServerUrl();
  return configStore.cloudSyncUpload(serverUrl, fileName);
});
ipcMain.handle('cloud-sync-download', (event, fileName) => {
  const serverUrl = configStore.getServerUrl();
  return configStore.cloudSyncDownload(serverUrl, fileName);
});
ipcMain.handle('cloud-sync-all', () => {
  const serverUrl = configStore.getServerUrl();
  return configStore.cloudSyncAll(serverUrl);
});
ipcMain.handle('cloud-restore-all', () => {
  const serverUrl = configStore.getServerUrl();
  return configStore.cloudRestoreAll(serverUrl);
});

// API Mode & Storage Mode IPC
ipcMain.handle('get-api-mode', () => configStore.getApiMode());
ipcMain.handle('set-api-mode', (event, mode) => configStore.setApiMode(mode));
ipcMain.handle('get-server-url', () => configStore.getServerUrl());
ipcMain.handle('set-server-url', (event, url) => configStore.setServerUrl(url));
ipcMain.handle('get-storage-mode', () => configStore.getStorageMode());
ipcMain.handle('set-storage-mode', (event, mode) => configStore.setStorageMode(mode));

// Skill Registry IPC
ipcMain.handle('skills-load-all', () => skillRegistry.loadAll());
ipcMain.handle('skills-get-index', () => skillRegistry.getIndex());
ipcMain.handle('skills-get-skill', (event, name) => {
  const skill = skillRegistry.getSkill(name);
  return skill ? { name: skill.name, description: skill.description, body: skill.body, source: skill.source } : null;
});
ipcMain.handle('skills-match', (event, userText, maxResults) => skillRegistry.matchSkills(userText, maxResults || 3));
ipcMain.handle('skills-get-summary', () => skillRegistry.getSkillsSummary());
ipcMain.handle('skills-get-context', (event, name) => skillRegistry.getSkillContext(name));

ipcMain.on('toggle-panel', () => togglePanel());
ipcMain.on('avatar-to-panel', (event, data) => {
  if (panelWindow && !panelWindow.isDestroyed()) panelWindow.webContents.send('from-avatar', data);
});
ipcMain.on('panel-to-avatar', (event, data) => {
  if (avatarWindow && !avatarWindow.isDestroyed()) avatarWindow.webContents.send('from-panel', data);
});
ipcMain.on('close-panel', () => { if (panelWindow) { panelWindow.hide(); isPanelOpen = false; } });

const contacts = require('./contacts');
ipcMain.handle('get-contacts', () => {
  const obj = contacts.getAllContacts();
  return Object.values(obj);
});
ipcMain.handle('add-contact', (event, name, phone) => {
  const result = contacts.addContact(name, phone);
  if (result.error) return { success: false, message: result.error };
  return { success: true, message: `Saved ${result.name} (${result.phone})` };
});
ipcMain.handle('remove-contact', (event, name) => {
  const removed = contacts.removeContact(name);
  return { success: removed, message: removed ? `Removed ${name}` : `${name} not found` };
});
ipcMain.handle('find-contact', (event, name) => contacts.findContact(name));
ipcMain.handle('get-contacts-path', () => contacts.getContactsFilePath());
ipcMain.handle('open-contacts-folder', () => {
  const { shell } = require('electron');
  const dir = contacts.WISHCRAFT_DIR;
  if (!require('fs').existsSync(dir)) require('fs').mkdirSync(dir, { recursive: true, mode: 0o700 });
  shell.openPath(dir);
  return dir;
});

app.isQuitting = false;

app.whenReady().then(() => {
  try { fs.unlinkSync('/tmp/wishcraft_cancel'); } catch (e) {}

  createAvatarWindow();
  createPanelWindow();
  createTray();
  startPythonBridge();

  globalShortcut.register('CommandOrControl+Shift+G', () => {
    if (isGenieVisible) dismissGenie(); else summonGenie();
  });
  globalShortcut.register('CommandOrControl+Shift+P', () => togglePanel());

  console.log('✨ WishCraft ready!');
  console.log('🧞 Click the lamp icon to summon your genie');
});

app.on('before-quit', () => { app.isQuitting = true; });
app.on('will-quit', () => { globalShortcut.unregisterAll(); if (pythonProcess) pythonProcess.kill(); });
// Keep app alive even when windows are hidden
app.on('window-all-closed', (e) => { e.preventDefault(); });
app.on('activate', () => { if (!avatarWindow || avatarWindow.isDestroyed()) createAvatarWindow(); });
