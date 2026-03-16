---
name: mail-automation
description: "Use this skill when the user wants to work with Apple Mail on macOS. Covers sending emails, reading inbox, replying, forwarding, searching messages, checking unread count, marking read/unread, and deleting messages."
triggers: mail, apple mail, inbox, send email, read email, unread, reply, forward, compose, check mail, message, outlook
platform: darwin
---

# Apple Mail Automation Skill

Full Apple Mail automation on macOS via **native AppleScript** — direct Mail API access, no keyboard simulation. 12 actions for composing, reading, replying, forwarding, searching, and managing emails.

---

## Examples — What the User Says → What You Call

### Example 1: Check Inbox
**User says:** "Check my email" or "What's in my inbox?"

**You call:**
```json
desktop_automation("mail_list_inbox", {"count": 10})
```
Then tell the user a summary of their messages.

---

### Example 2: Read Unread Only
**User says:** "Do I have any unread emails?"

**You call:**
```json
desktop_automation("mail_unread_count")
```
Then if they want to see them:
```json
desktop_automation("mail_list_inbox", {"count": 10, "unread_only": true})
```

---

### Example 3: Read a Specific Message
**User says:** "Read the first email" or "What does that email say?"

**You call:**
```json
desktop_automation("mail_read_message", {"index": 1})
```
Index 1 = most recent. Then summarize the content to the user.

---

### Example 4: Reply to an Email
**User says:** "Reply to that email saying thank you"

**You call:**
```json
desktop_automation("mail_reply", {"index": 1, "body": "Thank you for reaching out! I appreciate your message.", "send": true})
```
Use `send: false` to let user review before sending.

---

### Example 5: Send a New Email
**User says:** "Send an email to john@example.com about the meeting tomorrow"

**You call:**
```json
desktop_automation("mail_compose", {"to": "john@example.com", "subject": "Meeting Tomorrow", "body": "Hi John,\n\nJust a reminder about our meeting tomorrow.\n\nBest regards", "send": true})
```

---

### Example 6: Forward an Email
**User says:** "Forward that email to my boss at boss@company.com"

**You call:**
```json
desktop_automation("mail_forward", {"index": 1, "to": "boss@company.com", "body": "FYI - please see below.", "send": true})
```

---

### Example 7: Search Emails
**User says:** "Find emails about invoice" or "Search for emails from Apple"

**You call:**
```json
desktop_automation("mail_search", {"query": "invoice", "count": 10})
```

---

## Workflow Patterns

### Reading and Responding
1. `mail_list_inbox({count: 5})` → see recent messages
2. `mail_read_message({index: 1})` → read full content of message #1
3. `mail_reply({index: 1, body: "response text", send: true})` → reply

### Morning Email Check
1. `mail_check()` → fetch new mail
2. `mail_unread_count()` → see how many unread
3. `mail_list_inbox({unread_only: true})` → list unread messages
4. `mail_read_message({index: 1})` → read the first unread

### Compose and Send
1. `mail_compose({to: "email", subject: "sub", body: "text", send: false})` → draft
2. Or `send: true` to send immediately

---

## All Actions Reference (12 total)

All actions use `desktop_automation("mail_action_name", {args})`.

### App Control (2)
| Action | Args | Description |
|--------|------|-------------|
| `mail_open` | — | Open Apple Mail |
| `mail_check` | — | Check for new mail (fetch) |

### Reading (4)
| Action | Args | Description |
|--------|------|-------------|
| `mail_unread_count` | — | Get number of unread inbox messages |
| `mail_list_inbox` | `count` (10), `unread_only` (false) | List recent inbox messages |
| `mail_read_message` | `index` (1 = newest) | Read full message content |
| `mail_search` | `query`, `count` (10) | Search by subject or sender |

### Composing (3)
| Action | Args | Description |
|--------|------|-------------|
| `mail_compose` | `to`, `subject`, `body`, `cc`, `send` | Compose and optionally send new email |
| `mail_reply` | `index`, `body`, `send` | Reply to a message |
| `mail_forward` | `index`, `to`, `body`, `send` | Forward a message |

### Managing (3)
| Action | Args | Description |
|--------|------|-------------|
| `mail_mark_read` | `index` | Mark message as read |
| `mail_mark_unread` | `index` | Mark message as unread |
| `mail_delete` | `index` | Move message to trash |

---

## Important Notes

- **Index 1 = most recent message** — messages are ordered newest first
- **send: true** sends immediately, **send: false** opens compose window for review
- **mail_read_message** returns first 2000 characters of body text
- **mail_search** searches both subject and sender fields
- **mail_list_inbox** with `unread_only: true` only returns unread messages
- Always summarize email content to the user rather than reading the raw text

---

## Dependencies

- Apple Mail (pre-installed on macOS)
- At least one email account configured in Mail
