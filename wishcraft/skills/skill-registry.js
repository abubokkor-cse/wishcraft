/**
 * WishCraft Skill Registry — Discovers, loads, and matches skills to user requests.
 *
 * Pattern inspired by gemini-skills (SKILL.md with YAML frontmatter)
 * and knowledge-work-plugins (plugin.json + skills/ directory).
 *
 * Skills are loaded from:
 *   1. Built-in: ./skills/{skill-name}/SKILL.md
 *   2. Gemini Skills repo: ../gemini-skills-main/skills/
 *   3. Knowledge Work Plugins: ../knowledge-work-plugins-main/{plugin}/skills/
 *
 * Each SKILL.md has YAML frontmatter with:
 *   name: skill identifier
 *   description: when to use this skill (matched against user intent)
 *   triggers: optional array of keyword triggers
 */

const fs = require('fs');
const path = require('path');

// Simple YAML frontmatter parser (no dependency needed)
function parseFrontmatter(content) {
    const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
    if (!match) return { meta: {}, body: content };

    const yamlStr = match[1];
    const body = match[2];
    const meta = {};

    for (const line of yamlStr.split('\n')) {
        const colonIdx = line.indexOf(':');
        if (colonIdx === -1) continue;
        const key = line.substring(0, colonIdx).trim();
        let value = line.substring(colonIdx + 1).trim();
        if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
            value = value.slice(1, -1);
        }
        meta[key] = value;
    }

    return { meta, body };
}

class SkillRegistry {
    constructor(basePath) {
        this.basePath = basePath || path.join(__dirname);
        this.skills = new Map(); // name → { meta, body, source, path }
        this.loaded = false;
    }

    /**
     * Discover and index all built-in skills.
     */
    loadAll() {
        this.skills.clear();

        // Built-in skills only (./skills/{name}/SKILL.md)
        this._loadFromDir(this.basePath, 'built-in');

        this.loaded = true;
        return this.getIndex();
    }

    _loadFromDir(dirPath, source) {
        if (!fs.existsSync(dirPath)) return;

        // Map process.platform to skill platform values
        const platformMap = { darwin: 'darwin', win32: 'win32', linux: 'linux' };
        const currentPlatform = platformMap[process.platform] || process.platform;

        for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
            if (!entry.isDirectory()) continue;
            const skillFile = path.join(dirPath, entry.name, 'SKILL.md');
            if (!fs.existsSync(skillFile)) continue;

            try {
                const content = fs.readFileSync(skillFile, 'utf-8');
                const { meta, body } = parseFrontmatter(content);
                const name = meta.name || entry.name;

                // Skip skills that don't match current platform
                const skillPlatform = (meta.platform || 'all').trim().toLowerCase();
                if (skillPlatform !== 'all' && skillPlatform !== currentPlatform) {
                    continue;
                }

                this.skills.set(name, {
                    meta,
                    body,
                    source,
                    path: skillFile,
                    name,
                    description: meta.description || '',
                    triggers: meta.triggers ? meta.triggers.split(',').map(t => t.trim()) : []
                });
            } catch (err) {
                console.warn(`[SkillRegistry] Failed to load ${skillFile}:`, err.message);
            }
        }
    }

    /**
     * Get a compact index of all loaded skills (name + description).
     */
    getIndex() {
        const index = [];
        for (const [name, skill] of this.skills) {
            index.push({
                name,
                description: skill.description,
                source: skill.source,
                plugin: skill.plugin || null
            });
        }
        return { total: index.length, skills: index };
    }

    /**
     * Get the full content of a skill by name.
     */
    getSkill(name) {
        return this.skills.get(name) || null;
    }

    /**
     * Match user text against skill descriptions and triggers.
     * Returns top N matching skills with their full content.
     */
    matchSkills(userText, maxResults = 3) {
        if (!this.loaded) this.loadAll();

        const text = userText.toLowerCase();
        const scored = [];

        for (const [name, skill] of this.skills) {
            let score = 0;

            // Check triggers (high weight)
            for (const trigger of skill.triggers) {
                if (text.includes(trigger.toLowerCase())) {
                    score += 10;
                }
            }

            // Check description words
            const descWords = (skill.description || '').toLowerCase().split(/\s+/);
            for (const word of descWords) {
                if (word.length > 3 && text.includes(word)) {
                    score += 2;
                }
            }

            // Check skill name  
            const nameWords = name.replace(/[\/-]/g, ' ').toLowerCase().split(/\s+/);
            for (const word of nameWords) {
                if (word.length > 2 && text.includes(word)) {
                    score += 5;
                }
            }

            if (score > 0) {
                scored.push({ name, score, skill });
            }
        }

        scored.sort((a, b) => b.score - a.score);
        return scored.slice(0, maxResults).map(s => ({
            name: s.name,
            score: s.score,
            description: s.skill.description,
            source: s.skill.source,
            bodyPreview: s.skill.body.substring(0, 500) + (s.skill.body.length > 500 ? '...' : '')
        }));
    }

    /**
     * Get full skill content for injection into system prompt.
     * Returns formatted markdown ready to append to prompt.
     */
    getSkillContext(skillName) {
        const skill = this.skills.get(skillName);
        if (!skill) return null;

        return `\n═══ SKILL: ${skill.name} ═══\n${skill.body}\n═══ END SKILL ═══\n`;
    }

    /**
     * Get a compact skills summary for the system prompt.
     * Lists all available skills so the model knows what expertise is available.
     */
    getSkillsSummary() {
        if (!this.loaded) this.loadAll();

        const bySource = {};
        for (const [name, skill] of this.skills) {
            const src = skill.source;
            if (!bySource[src]) bySource[src] = [];
            bySource[src].push(`${name}: ${skill.description.substring(0, 80)}`);
        }

        let summary = '\n═══ AVAILABLE SKILLS ═══\n';
        for (const [source, skills] of Object.entries(bySource)) {
            summary += `\n[${source}]\n`;
            for (const s of skills) {
                summary += `  • ${s}\n`;
            }
        }
        summary += '\nTo use a skill, the system will auto-load relevant skill context based on the conversation.\n═══ END SKILLS ═══\n';

        return summary;
    }
}

// Singleton instance
let _instance = null;

function getRegistry(basePath) {
    if (!_instance) {
        _instance = new SkillRegistry(basePath);
    }
    return _instance;
}

module.exports = { SkillRegistry, getRegistry, parseFrontmatter };
