# Mail → Brain: your inbox becomes askable memory

Once a mailbox is connected (see `CONNECT_MAIL_CALENDAR.md`), Jarvis can read it
on a timer, turn each new email into a permanent memory, and let you ask
questions about it.

---

## What happens to each new email

```text
Gmail (read-only IMAP)
      │
      ├─► SQLite memory + search index   ← makes it ANSWERABLE in AI Agent
      ├─► memory_vault/cards/*.json      ← vault + knowledge graph
      │      └─► self-improving wiki compiler
      ├─► deadline detection             ← tasks + notifications
      └─► GitHub sync (existing 60s loop)
```

It is written to **two** stores on purpose. The vault gives you the permanent,
GitHub-backed record and feeds the wiki and graph. The SQLite memory is what the
answering pipeline actually searches — a card alone would have been unanswerable.

---

## What gets skipped (and why)

| Mail | Behaviour |
|---|---|
| Normal mail | Fully ingested |
| Newsletters / marketing (`List-Unsubscribe`) | Never stored — would pollute the wiki and graph |
| Transactional bulk (invoices, bills, `Precedence: bulk`) | Stored **only if** it contains a real action/deadline — a bill's due date matters |
| Anything you already read | Still ingested the first time; its read/unread state is recorded |

---

## Deadlines become tasks

Jarvis scans each email for deadline and action wording and extracts a date from
phrases like:

- `submit by Friday 5 PM` → the coming Friday
- `deadline 25/12/2026` → 25 Dec 2026
- `due on 30 September` → 30 Sep (this year, or next if already past)
- `today` / `tomorrow`

When found, it creates a **task** (`Email Follow-ups` project) and a
**notification**. A task is high priority when the mail says urgent, or when an
explicit deadline is present. If no date can be found, none is invented — the task
gets created without a due date rather than a wrong one.

---

## Being notified

- **Notifications page** — real alerts only, auto-refreshing
- **Windows notification** — raised from the app shell when a sync ingests mail
- **Agent Activity** — every sync recorded in the audit log

---

## Asking questions

Open **AI Agent** and ask naturally:

- "What is the IEEE conference draft deadline?"
- "What did Prof. Sharma say about the dataset?"
- "Any invoice I still need to pay?"

Retrieval matches on the meaningful words in your question and ranks by how many
matched, so you do not need to remember exact phrasing.

> **Note:** semantic (embedding) search adds a second layer when the optional
> `sentence-transformers` pack is installed (`backend/requirements-optional.txt`).
> Without it, the keyword layer now works properly for full questions — see below.

---

## Configuration

In `backend/.env`:

```env
MAIL_SYNC_ENABLED=true
MAIL_SYNC_INTERVAL_MINUTES=10
MAIL_SYNC_FOLDERS=inbox          # add "sent" to also learn from what you write
MAIL_SYNC_LIMIT=25               # new messages per folder per run
MAIL_SYNC_SKIP_BULK=true
MAIL_STORE_IN_VAULT=true
```

Manual sync any time: **Integrations → Mail → Brain → Sync mail now**.

---

## Guarantees

| Guarantee | How |
|---|---|
| Mail is never marked as read | Every mailbox opened with `EXAMINE`; every body pulled with `BODY.PEEK` |
| No duplicates | IMAP `UIDVALIDITY` + last-UID cursor, plus a content-hash unique constraint |
| Resumable | A changed `UIDVALIDITY` triggers a clean resync instead of silent gaps |
| No re-push storms | Bulk ingestion writes cards without firing a GitHub push per email |
| Credentials stay private | App passwords encrypted; never in the vault, never synced |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Sync reports 0 ingested | Nothing new since the last cursor. Send yourself a test email, then sync. |
| "Server did not report UIDVALIDITY" | Unusual IMAP server; try again, and send me the server name. |
| Wiki filling with junk | Set `MAIL_SYNC_SKIP_BULK=true` and add noisy senders — tell me and I'll add a sender blocklist. |
| Deadlines not detected | Send me the exact wording; the phrase list is easy to extend. |
