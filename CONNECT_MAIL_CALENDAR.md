# Connecting your Gmail accounts & calendars — the 15-minute path

You were on the Google **Branding** page trying to publish, and hit a wall.
Here is the honest situation, then the path that actually works.

---

## Why you got stuck

Google now requires three things before an **External** app can be published:

1. an **Application home page** URL
2. a **Privacy policy** URL
3. at least one **Authorized domain** — one you have *proven you own* via Google Search Console

You have none of these, so the Publish button stays greyed out. That is exactly
where you are.

### And it gets worse from there

Reading a Gmail inbox requires the scope `gmail.readonly`. Google classifies that
as a **restricted** scope. If your app uses a restricted scope and you publish it,
Google requires:

| Requirement | Reality |
|---|---|
| Third-party security assessment (CASA) | **~$540–$1,800 per year** |
| Annual re-certification | every 12 months, forever |
| Review timeline | 4–8 weeks |
| Privacy policy, homepage, verified domain | mandatory |

For an app that exactly **one person** is going to use, that is not a reasonable
trade. You would be spending real money every year, and weeks of waiting, to let
Jarvis read your own mail.

> **If you stay in Testing mode**, everything works today — but Google expires the
> refresh token **every 7 days**, so you would have to re-connect all three accounts
> every single week. That is why "just publish it" felt like the answer.

---

## The path that actually works

Two connections, neither of which needs Google Cloud at all.

### Part 1 — Mail, via a Gmail App Password (no OAuth)

```text
myaccount.google.com/security   →  turn ON 2-Step Verification
myaccount.google.com/apppasswords →  create one, named "Jarvis"
```

You get 16 characters. Paste that into Jarvis instead of your password.

| | |
|---|---|
| Cost | **free, forever** |
| Google Cloud project | **not needed** |
| Consent screen / verification | **not needed** |
| Token expiry | **never** |
| Access | read-only (`EXAMINE` + `BODY.PEEK` — Jarvis literally cannot mark your mail as read) |

Works for both personal accounts:

- `immanuellourdu@gmail.com`
- `lmariaimmanuel@gmail.com`

> ⚠️ **`vtu24334@veltech.edu.in` is a Workspace account.** Google stopped accepting
> App Passwords for Workspace domains on **1 May 2025** — and your college admin may
> additionally block third-party access. That one may only work via OAuth. Try it;
> if it refuses, either skip it or use the OAuth route in Part 3. The app works fine
> with any subset of accounts.

### Part 2 — Calendar, via the private iCal address (no OAuth)

```text
calendar.google.com → ⚙️ Settings
  → Settings for my calendars → pick the calendar
  → Integrate calendar → "Secret address in iCal format"
```

Copy that URL — it looks like
`https://calendar.google.com/calendar/ical/you%40gmail.com/private-abc123/basic.ics`

| | |
|---|---|
| Cost | **free, forever** |
| OAuth | **none at all** |
| Expiry | **none** |
| Access | inherently read-only |

Repeat once per Google account (switch Google account first). That is **3 URLs** for
all three of your calendars.

> That URL is a password. Jarvis encrypts it and only ever fetches it server-side.

### Part 3 (optional) — Google OAuth, only if you need the college account

This is already built and tested (see `GOOGLE_SETUP.md`). It works perfectly in
**Testing** mode for yourself — you would just reconnect that one account weekly.
That is a fair trade for a single account you rarely change. Do **not** chase
publication for it.

---

## Doing it in the app

```powershell
cd "I:\Major projects\Second Brain"
git pull origin main
.\verify-jarvis.ps1
.\start-jarvis.ps1
```

Then open **Integrations**:

**Mail**
1. Click the `immanuellourdu@gmail.com` button (it fills the address for you)
2. Paste the 16-character App Password
3. Click **Connect**

Jarvis logs in immediately and refuses to save anything unless the login
succeeds. You should see *"4210 messages, 37 unread"* — real numbers from your
real inbox.

4. Repeat for `lmariaimmanuel@gmail.com`

**Calendar**
1. Paste the first iCal URL into the *Add a calendar by private iCal address* box
2. Give it a label ("Personal", "College")
3. Click **Add**

Jarvis fetches it once to prove it is a real calendar, then tells you how many
events it found.

4. Repeat for the other two accounts

Then open **Gmail** and **Calendar** — both now show real data, with a switcher at
the top listing every account and which method it uses (`IMAP` / `OAUTH` / `ICS`).

---

## What Jarvis can and cannot do

| Allowed | Not allowed |
|---|---|
| Read your inbox and message bodies | Send email |
| Detect unread, important, senders | Delete, archive, or label anything |
| Search with `from:` / `subject:` | Mark messages as read |
| Read your calendars and events | Create, edit, or cancel events |

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| *"Gmail rejected that app password"* | You used your normal Google password. Generate one at `myaccount.google.com/apppasswords` — it is only offered once 2-Step Verification is on. |
| *"authentication failed… Workspace account"* | Expected for `veltech.edu.in`. Use Part 3 (OAuth) for that one. |
| App Passwords page says *"not available for your account"* | 2-Step Verification is off, or you are on a Workspace domain. |
| *"Google returned 404 for that calendar address"* | The secret URL was reset. Copy a fresh one from Calendar settings. |
| *"That URL returned a web page, not a calendar"* | You copied the calendar's public web link instead of the *Secret address in iCal format*. |
| Calendar shows fewer events than expected | Recurring events are expanded (daily/weekly/monthly). Rare rules — `BYSETPOS`, `BYYEARDAY` — are intentionally not expanded rather than expanded wrongly. |
| Wrong time on events | Times are read as UTC unless the feed says otherwise. Tell me and I will add full timezone handling. |

---

## Where your credentials live

- `backend/data/integrations/imap_accounts.enc` — app passwords
- `backend/data/integrations/calendar_feeds.enc` — iCal secret URLs
- `backend/data/integrations/google_accounts.enc` — OAuth refresh tokens

All three are **Fernet-encrypted** (AES-128 + HMAC) with a key beside them, under
`backend/data/`, which is `.gitignore`d and **never** part of the `memory_vault/`
sync that pushes to GitHub every 60 seconds. The backend actively **refuses to
store credentials** if that directory is ever pointed inside `memory_vault/`.

To revoke: the trash icon in **Integrations**, or
<https://myaccount.google.com/permissions> for OAuth, or
<https://myaccount.google.com/apppasswords> to kill an app password.
