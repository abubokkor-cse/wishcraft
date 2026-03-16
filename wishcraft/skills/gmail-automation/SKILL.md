---
name: gmail-automation
description: "Use this skill when the user wants to interact with Gmail in Chrome — check inbox, read emails, compose, reply, forward, search, archive, delete, star, unread count, or organize Gmail messages."
triggers: gmail, google mail, web mail, check gmail, gmail inbox, gmail compose, gmail search, gmail reply, gmail forward, gmail archive, unread count, how many unread, read my emails, send email
platform: all
---

# Web Gmail Automation (Chrome)

Gmail automation via keyboard shortcuts + clipboard paste in Chrome. Requires Gmail keyboard shortcuts enabled in Settings > General > "Keyboard shortcuts on".

## Quick Examples

### Check Unread Count
```json
{"action": "gmail_unread_count"}
```
Returns: `{"success": true, "unread_count": 5}`

### Auto-Reset to List View (CALL THIS BEFORE NEW TASKS)
```json
{"action": "gmail_ensure_list_view"}
```
Automatically: closes compose/reply if open, goes back to list from email. Safe to call anytime.

### Read an Email (MUST open first)
```json
{"action": "gmail_open_email"}
{"action": "gmail_read_email"}
```
Returns From, Subject, Date, Body (up to 3000 chars) of the open email.

### Reply to Email (MUST be open first)
```json
{"action": "gmail_reply", "args": {"body": "Thank you for your message!", "send": true}}
```
Opens reply box, types body, sends. Use `send: false` to let user review.

### Compose New Email
```json
{"action": "gmail_compose", "args": {"to": "someone@gmail.com", "subject": "Meeting Tomorrow", "body": "Hi, can we meet at 3pm?", "send": true}}
```
Fields: `to`, `subject`, `body`, `cc`, `bcc`, `send`. Uses clipboard paste to fill fields.

### Forward Email (MUST be open first)
```json
{"action": "gmail_forward", "args": {"to": "colleague@email.com", "body": "FYI - see below", "send": true}}
```

### Search Emails
```json
{"action": "gmail_search", "args": {"query": "invoice from:amazon"}}
```

## Step-by-Step Workflow Patterns

### WORKFLOW: "Send email to X"
1. `gmail_compose({to, subject, body, send: true})` — ONE call does everything
2. Confirm `send_confirmed: true` → tell user "Email sent!"

### WORKFLOW: "Reply to the Nth email"
1. `gmail_ensure_list_view` — reset to inbox list
2. `gmail_next` — repeat N-1 times to reach Nth email (skip for 1st/latest)
3. `gmail_open_email` — **MUST open before reply**
4. `gmail_read_email` — read to verify it's the right email
5. `gmail_reply({body, send: true})` — reply to the OPEN email
6. Confirm `send_confirmed: true` → tell user "Reply sent!"
7. `gmail_ensure_list_view` — reset for next action

### WORKFLOW: "Read my emails" / "What's in my inbox?"
1. `gmail_ensure_list_view` — reset to list
2. `gmail_unread_count` — tell user the count
3. `gmail_open_email` — open first email
4. `gmail_read_email` — read it, tell user subject + summary
5. `gmail_ensure_list_view` — go back for next email
6. Repeat for more emails if user wants

### WORKFLOW: "Open/read the Nth email"
1. `gmail_ensure_list_view` — reset to list
2. `gmail_next` — repeat N-1 times
3. `gmail_open_email` — **MUST open the email**
4. `gmail_read_email` — read content, tell user subject + summary

### WORKFLOW: "Forward this email to X"
1. `gmail_ensure_list_view` — if not already on an email
2. `gmail_next` — if needed
3. `gmail_open_email` — **MUST open first**
4. `gmail_forward({to, body, send: true})`

### WORKFLOW: "Morning Email Check"
1. `gmail_unread_count` — quick count
2. `gmail_ensure_list_view` — reset
3. `gmail_open_email` — open first email
4. `gmail_read_email` — read it, summarize for user
5. Take action: reply/archive/star/delete
6. `gmail_ensure_list_view` — reset before next
7. `gmail_next` — move to next
8. Repeat

## All Actions Reference

| Action | Args | What It Does |
|--------|------|-------------|
| `gmail_open` | — | Open Gmail in Chrome |
| `gmail_get_state` | — | Detect current view (list/email/compose/reply) |
| `gmail_ensure_list_view` | — | Auto-close compose/reply/email, return to list |
| `gmail_unread_count` | — | Get count of unread emails |
| `gmail_compose` | `{to, subject, body, cc, bcc, send}` | Compose new email |
| `gmail_search` | `{query}` | Search emails |
| `gmail_reply` | `{body, send}` | Reply to **open** email |
| `gmail_reply_all` | `{body, send}` | Reply all to **open** email |
| `gmail_forward` | `{to, body, send}` | Forward **open** email |
| `gmail_send` | — | Send (Ctrl/Cmd+Return) |
| `gmail_go_inbox` | — | Go to Inbox |
| `gmail_go_sent` | — | Go to Sent |
| `gmail_go_drafts` | — | Go to Drafts |
| `gmail_go_starred` | — | Go to Starred |
| `gmail_go_all_mail` | — | Go to All Mail |
| `gmail_open_email` | — | Open selected email |
| `gmail_back_to_list` | — | Back to email list |
| `gmail_next` | — | Next/older conversation |
| `gmail_prev` | — | Previous/newer conversation |
| `gmail_newer` | — | Next message in thread |
| `gmail_older` | — | Previous message in thread |
| `gmail_archive` | — | Archive conversation |
| `gmail_delete` | — | Delete conversation |
| `gmail_spam` | — | Report as spam |
| `gmail_star` | — | Toggle star |
| `gmail_mark_read` | — | Mark as read |
| `gmail_mark_unread` | — | Mark as unread |
| `gmail_mark_important` | — | Mark as important |
| `gmail_select` | — | Select conversation |
| `gmail_select_all` | — | Select all conversations |
| `gmail_mute` | — | Mute conversation |
| `gmail_label` | — | Open label menu |
| `gmail_move_to` | — | Open move-to menu |
| `gmail_snooze` | — | Snooze conversation |
| `gmail_undo` | — | Undo last action |
| `gmail_refresh` | — | Refresh inbox |
| `gmail_read_email` | — | Read open email content (subject, from, body via clipboard) |

## Gmail Search Operators
- `from:user@email.com` — from specific sender
- `to:user@email.com` — to specific recipient
- `subject:meeting` — subject contains
- `has:attachment` — has attachments
- `is:unread` — unread emails
- `is:starred` — starred emails
- `after:2024/01/01` — after date
- `before:2024/12/31` — before date
- `label:work` — has specific label

## CRITICAL RULES
- **ALWAYS call `gmail_open_email` BEFORE** `gmail_reply`, `gmail_reply_all`, `gmail_forward`, or `gmail_read_email`. These ONLY work on an OPEN email.
- **ALWAYS call `gmail_ensure_list_view`** before starting a NEW Gmail task.
- Execute ONE action at a time, check result, tell user what happened, then proceed.
- If `gmail_reply` returns `send_confirmed: true` → "Reply sent." If false/missing → "Reply may not have sent" and retry.
- `gmail_compose` is the ONLY action that works without opening an email first.
- Do NOT use `mail_*` functions for Gmail — those are Apple Mail only.
- For Apple Mail, use `mail_*` functions instead.
