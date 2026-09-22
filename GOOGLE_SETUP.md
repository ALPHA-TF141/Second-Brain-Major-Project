# Connecting Gmail & Calendar to Jarvis

**Why you have to do this part yourself:** Google requires that the *account owner*
approve access through their own browser. That is a good thing — it means nobody,
including me, ever sees or handles your password. You are creating your own private
OAuth application, so only you hold the keys.

**Time:** about 5 minutes, one time.

---

## Before you start

You will connect three accounts:

| Account | Notes |
|---|---|
| `immanuellourdu@gmail.com` | personal |
| `lmariaimmanuel@gmail.com` | personal |
| `vtu24334@veltech.edu.in` | **college (Workspace) account** — see the note at the end |

---

## Step 1 — Create a Google Cloud project

1. Go to <https://console.cloud.google.com/>
2. Sign in with **any one** of your Google accounts (this is just the *owner* of the
   project — it does not limit which accounts you can later connect).
3. Top bar → project dropdown → **New Project**
4. Name: `Jarvis Second Brain` → **Create**
5. Make sure the new project is selected in the top bar.

---

## Step 2 — Enable the two APIs

For each of these, click the link → **Enable**:

- **Gmail API** → <https://console.cloud.google.com/apis/library/gmail.googleapis.com>
- **Google Calendar API** → <https://console.cloud.google.com/apis/library/calendar-json.googleapis.com>

Both must say **Enabled**. If you skip this, connecting succeeds but every read fails.

---

## Step 3 — Configure the consent screen

1. Go to <https://console.cloud.google.com/apis/credentials/consent>
2. User type: **External** → **Create**
3. Fill in:
   - **App name:** `Jarvis Second Brain`
   - **User support email:** your email
   - **Developer contact email:** your email
4. **Save and continue**
5. **Scopes** page → **Save and continue** (leave empty — Jarvis requests its scopes
   at connect time)
6. **Test users** page → **Add users** → add **all three**:

   ```
   immanuellourdu@gmail.com
   lmariaimmanuel@gmail.com
   vtu24334@veltech.edu.in
   ```

   > ⚠️ Skip this and Google will refuse with *"Access blocked: this app has not been
   > verified"* when you try to connect. This is the #1 mistake.

7. **Save and continue** → **Back to dashboard**

---

## Step 4 — Create the OAuth credentials

1. Go to <https://console.cloud.google.com/apis/credentials>
2. **+ Create credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `Jarvis Desktop`
5. **Authorized redirect URIs** → **Add URI** → paste this **exactly**:

   ```
   http://127.0.0.1:8000/api/google/callback
   ```

   > It must match character for character. `localhost` instead of `127.0.0.1` will be
   > rejected. No trailing slash. Wrong port breaks it.

6. **Create**
7. Copy the **Client ID** and **Client secret** from the popup.

---

## Step 5 — Put the credentials into the app

Create (or edit) `backend\.env` in your project folder:

```powershell
cd "I:\Major projects\Second Brain"
notepad backend\.env
```

Add these two lines (paste your own values):

```env
GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret-here
```

Save and close.

> **Never commit this file or share the secret.** It is already in `.gitignore`
> (`backend/.env`), so it will not be pushed to GitHub.

---

## Step 6 — Publish the app (IMPORTANT — do not skip)

While the app is in **Testing** mode, Google **expires refresh tokens after 7 days**.
Jarvis would silently stop reading your mail every week.

1. Go to <https://console.cloud.google.com/apis/credentials/consent>
2. Under **Publishing status**, click **Publish app** → **Confirm**

You will see *"unverified app"* when connecting. That warning is expected — it is your
own app, only you use it, and this is what stops the 7-day expiry. Click
**Advanced → Go to Jarvis Second Brain (unsafe)** to continue.

> Publishing does **not** make your app public or let anyone else in. Nobody can use it
> without your Client Secret.

---

## Step 7 — Restart and connect

```powershell
cd "I:\Major projects\Second Brain"
.\start-jarvis.ps1
```

Then in the app:

1. Open **Integrations**
2. You should see three buttons, one per account
3. Click **`immanuellourdu@gmail.com`** → your browser opens Google's consent screen
4. Pick that account → **Continue** → approve the read-only permissions
5. You will land on a *"Connected Successfully"* page — close the tab
6. Jarvis updates by itself within ~2 seconds
7. Repeat for the other two addresses

Then open **Gmail** and **Calendar** — both now show real data with an account switcher
at the top.

---

## What Jarvis can and cannot do

| Allowed (read-only) | Not allowed |
|---|---|
| Read your inbox and messages | Send email |
| Detect deadlines, senders, unread state | Delete or archive anything |
| Read your calendars and events | Create, edit, or cancel events |

Scopes requested: `gmail.readonly`, `calendar.readonly`, `userinfo.email`.
You can verify this yourself in the consent screen — it will say *"View your email
messages"* and *"See your calendars"*, never "send".

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Access blocked: this app has not been verified` | You did not add that email under **Test users** (Step 3) |
| `Error 400: redirect_uri_mismatch` | The URI in Google Cloud must be exactly `http://127.0.0.1:8000/api/google/callback` |
| `Gmail API has not been used in project … or it is disabled` | Step 2 was skipped — enable the Gmail API |
| *"Google is not configured yet"* in the app | `backend/.env` is missing or the backend was not restarted after editing it |
| Worked, then stopped after ~7 days | App still in **Testing** mode — do Step 6 |
| Connect worked but Gmail shows *"Token problem"* | Access was revoked. Disconnect and reconnect that account |
| `vtu24334@veltech.edu.in` refuses to connect | See below |

### About the college account

`veltech.edu.in` is a **Google Workspace** domain. Workspace admins can block third-party
apps for their users. If the college account will not connect, one of these will apply:

- It needs to be added as a **Test user** (Step 3) — try this first
- The college admin must allow it, or
- You simply connect the two personal Gmail accounts instead; the app works fine with
  any subset of accounts

The app supports as many accounts as you want, so connect whichever ones Google allows.

---

## Where your tokens live

- File: `backend/data/integrations/google_accounts.enc`
- **Encrypted** with Fernet (AES-128 + HMAC); the key sits beside it as `.token_key`
- `backend/data/` is in `.gitignore` and is **never** part of the `memory_vault/` sync
  that pushes to GitHub every 60 seconds
- The backend actively **refuses to start token storage** if that directory is ever
  pointed inside `memory_vault/`

To revoke access entirely: use the trash icon in **Integrations**, or visit
<https://myaccount.google.com/permissions> and remove *Jarvis Second Brain*.
