/**
 * GeminiCollaborator — Worker model for heavy analysis & generation tasks.
 * 
 * The Live API agent is fast but voice-optimized (short responses).
 * This collaborator handles:
 * - PDF analysis (scanned & text)
 * - Image analysis (any format)
 * - Long content generation (CVs, essays, code, reports)
 * - File understanding
 * 
 * Uses Gemini 3 Flash Preview via REST generateContent API.
 */

const COLLABORATOR_MODEL = 'gemini-3-flash-preview';
const COLLABORATOR_LITE_MODEL = 'gemini-3-flash-preview';
const API_BASE = 'https://generativelanguage.googleapis.com/v1beta';

export class GeminiCollaborator {
    constructor(apiKey) {
        this.apiKey = apiKey;
    }

    /**
     * Analyze a file (image, PDF, text, etc.) — uses full model for vision
     */
    async analyzeFile(base64Data, mimeType, question = 'Analyze this file in detail. Describe what you see and extract all important information.') {
        const parts = [
            { inlineData: { mimeType, data: base64Data } },
            { text: question }
        ];
        return this._generateContent(parts, '', COLLABORATOR_MODEL);
    }

    /**
     * Transcribe audio/video file — Gemini 3 Flash accepts audio natively
     */
    async transcribeAudio(base64Data, mimeType, language = '') {
        const langHint = language ? ` The audio is in ${language}.` : '';
        const parts = [
            { inlineData: { mimeType, data: base64Data } },
            { text: `Transcribe this audio file accurately. Output ONLY the transcription text, nothing else. Preserve paragraphs and speaker changes if detectable.${langHint}` }
        ];
        return this._generateContent(parts, 'You are a professional audio transcription service. Produce accurate, clean transcriptions.', COLLABORATOR_MODEL);
    }

    /**
     * Analyze multiple files at once — uses full model for vision
     */
    async analyzeMultipleFiles(files, question) {
        const parts = [];
        for (const file of files) {
            parts.push({ inlineData: { mimeType: file.mimeType, data: file.base64 } });
        }
        parts.push({ text: question });
        return this._generateContent(parts, '', COLLABORATOR_MODEL);
    }

    /**
     * Generate long-form content — uses lite model for speed
     */
    async generateContent(prompt, systemInstruction = '') {
        const parts = [{ text: prompt }];
        return this._generateContent(parts, systemInstruction, COLLABORATOR_LITE_MODEL);
    }

    /**
     * Generate structured slide content for PPTX creation — uses full model
     */
    async generateSlides(prompt, style = 'professional') {
        const sysPrompt = `You are an EXPERT presentation designer who creates pixel-perfect, visually stunning PowerPoint slides. Create slide content as a JSON object.

SLIDE DIMENSIONS: LAYOUT_16x9 = 10" wide x 5.625" tall. All x/y/w/h in INCHES.
Footer auto-added on slides 2+, so keep content above y=5.3.

DESIGN PHILOSOPHY:
- The palette should feel DESIGNED FOR THIS TOPIC. Not generic.
- One color dominates (60-70%), 1-2 supporting, one accent for highlights.
- Dark bg for title + conclusion. Light bg for content. "Sandwich" structure.
- Pick ONE distinctive visual motif and repeat it (accent bars, colored circles, card borders).
- NEVER create text-only slides. Every slide MUST have shapes, cards, or images.
- NEVER repeat the same layout twice. Vary: two-column, stat boxes, cards, image+text, tables.

COLOR PALETTES (pick one that MATCHES the topic, not random):
- Midnight Executive: primary 1E2761, secondary CADCFC, accent F9A825 — business, corporate, finance
- Forest & Moss: primary 2C5F2D, secondary 97BC62, accent F5F5F5 — nature, sustainability, health
- Coral Energy: primary F96167, secondary F9E795, accent 2F3C7E — marketing, creative, youth
- Ocean Gradient: primary 065A82, secondary 1C7293, accent 21295C — technology, science, data
- Charcoal Minimal: primary 36454F, secondary F2F2F2, accent 212121 — minimal, elegant, luxury
- Teal Trust: primary 028090, secondary 00A896, accent 02C39A — healthcare, consulting, trust
- Berry & Cream: primary 6D2E46, secondary A26769, accent ECE2D0 — fashion, beauty, lifestyle
- Cherry Bold: primary 990011, secondary FCF6F5, accent 2F3C7E — bold statements, startups
- Golden Hour: primary F4A900, secondary C1666B, accent 4A403A — food, hospitality, autumn
- Cosmic Night: primary 2B1E3E, secondary 4A4E8F, accent A490C2 — entertainment, gaming, creative
Or create a CUSTOM palette that matches the specific topic.

TYPOGRAPHY: titles 36-44pt bold, section headers 16-20pt, body 11-14pt, captions 9-10pt italic.
Font pairings: Georgia/Calibri, or Arial Black/Arial. 0.5" minimum margins.

Style preference: ${style}

ELEMENT TYPES (use a MIX of these — not just text and bullets):

1. "text" — { type, text, x, y, w, h, fontSize, fontFace, color, bold, italic, align, valign }
2. "bullets" — { type, items[], x, y, w, h, fontSize, color }
3. "shape" — { type, shape (RECTANGLE/OVAL/LINE), x, y, w, h, fill, lineColor, lineWidth, transparency, shadow(bool) }
4. "card" — Rounded card with shadow + optional accent top bar:
   { type:"card", x, y, w, h, fill, borderColor, accentColor, title, titleColor, text, color, fontSize }
5. "section_header" — Full-width colored header bar:
   { type:"section_header", text, y:0, h:0.6, fill, color, fontSize }
6. "stat_box" — Stat/metric display box with large number + label:
   { type:"stat_box", x, y, w, h, value:"98%", label:"Accuracy", accentColor, valueColor, borderColor }
7. "table" — { type, rows[][], x, y, w, h, headerFill, borderColor, colW[] }
8. "chart" — { type, chartType (BAR/PIE/LINE/DOUGHNUT), data[{name,labels[],values[]}], x, y, w, h, colors[], showLegend, showValue }
9. "image" — { type, path (EXACT file path from AVAILABLE IMAGES), x, y, w, h, shadow(bool), caption }

LAYOUT PATTERNS TO USE (vary these across slides):

Pattern A — Section Header + Cards Row:
  section_header at top → 3 cards in a row below

Pattern B — Two Column (text + image):
  section_header → left side: bullets or cards, right side: image

Pattern C — Stats Row:
  section_header → 3-4 stat_boxes in a row showing key numbers

Pattern D — Comparison (left vs right):
  Two colored cards side by side with contrasting colors

Pattern E — Full Image + Caption:
  section_header → large image centered → caption below

Pattern F — Table Slide:
  section_header → table with headerFill matching theme

IMAGE RULES:
- If AVAILABLE IMAGES are listed, you MUST embed them using type:"image" with the EXACT path.
- Place images in two-column layouts: text on left (w:4.5), image on right (w:4.5).
- Or full-width (w:9, h:3.5) with caption below.
- Add shadow:true and caption for professional look.

CONTENT FILE RULES:
- If source content provided, organize into clear sections.
- Summarize into slide-friendly points. Do NOT copy verbatim.
- Extract key data/stats and present as stat_boxes.
- Maintain the narrative flow of the original.

OUTPUT — Return ONLY valid JSON (no markdown, no backticks, no explanation):
{
  "title": "Presentation Title",
  "theme": { "primary": "HEX", "secondary": "HEX", "accent": "HEX", "fontHeader": "Georgia", "fontBody": "Calibri" },
  "slides": [
    {
      "background": "HEX",
      "footer": false,
      "elements": [...]
    }
  ]
}

MANDATORY STRUCTURE:
1. Slide 1 = Title slide (dark bg, "footer":false, large title, subtitle, accent shapes)
2. Slides 2-N = Content slides (USE DIFFERENT PATTERNS, not all the same!)
3. Last slide = Thank You / Summary (dark bg)

Make it look like a PROFESSIONAL designer created it. Use cards, stat_boxes, section_headers, shapes. NOT just text and bullets.`;

        const parts = [{ text: prompt }];
        return this._generateContent(parts, sysPrompt, COLLABORATOR_MODEL);
    }

    /**
     * Core API call to Gemini generateContent
     */
    async _generateContent(parts, systemInstruction = '', model = COLLABORATOR_MODEL) {
        const url = `${API_BASE}/models/${model}:generateContent?key=${this.apiKey}`;

        const body = {
            contents: [{ parts }],
            generationConfig: {
                maxOutputTokens: 16384,
                temperature: 0.7,
            }
        };

        if (systemInstruction) {
            body.systemInstruction = {
                parts: [{ text: systemInstruction }]
            };
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errText = await response.text();
                console.error('Collaborator API error:', response.status, errText);
                return { success: false, error: `API error ${response.status}: ${errText.substring(0, 200)}` };
            }

            const data = await response.json();

            if (data.candidates && data.candidates[0]?.content?.parts) {
                const text = data.candidates[0].content.parts
                    .filter(p => p.text)
                    .map(p => p.text)
                    .join('\n');
                return { success: true, text };
            }

            if (data.candidates && data.candidates[0]?.finishReason === 'SAFETY') {
                return { success: false, error: 'Content was blocked by safety filters.' };
            }

            return { success: false, error: 'No content in response' };
        } catch (err) {
            console.error('Collaborator fetch error:', err);
            return { success: false, error: err.message };
        }
    }
}
