# Hands-Free: "Hey Jarvis" + Jarvis speaks first

The two traits that make the difference between *an app you check* and
*something that is there*. Both run **100% locally** — no cloud, no account,
no per-request cost, and no audio ever leaves your machine.

---

## 1. Wake word — say "Hey Jarvis"

Runs **offline** on the CPU using [openWakeWord](https://github.com/dscripka/openWakeWord),
which ships a pretrained `hey_jarvis` model.

### Enable it (one command)

```powershell
cd "I:\Major projects\Second Brain"
backend\.venv\Scripts\python.exe -m pip install openwakeword sounddevice
```

Restart the app. You should see:

```
[Wake] Listening for 'hey_jarvis' (threshold 0.5). Say it to summon Jarvis.
```

Now say **"Hey Jarvis"** and the orb appears and starts listening.

**Alt+J keeps working exactly as before** — the two are independent. Without the
packages, the app runs normally and the Integrations page tells you what to install.

### Verified accuracy

Measured against the real model on real recorded speech:

| Input | `hey_jarvis` score | Result |
|---|---|---|
| Spoken "Hey Jarvis" | **0.9968** | ✅ fires |
| Silence | 0.0000 | no fire |
| White noise | 0.0007 | no fire |
| 440 Hz tone | 0.0018 | no fire |

Threshold `0.5` sits comfortably in that gap. Tune with `WAKE_WORD_THRESHOLD` if
your microphone is quiet or your room is noisy.

### Tuning

| Setting | Default | Meaning |
|---|---|---|
| `WAKE_WORD_ENABLED` | `true` | Turn the listener on/off |
| `WAKE_WORD_MODEL` | `hey_jarvis` | Which phrase to listen for |
| `WAKE_WORD_THRESHOLD` | `0.5` | Lower = easier to trigger, more false positives |
| `WAKE_WORD_DEBOUNCE_SECONDS` | `2.5` | One utterance fires once, not five times |

Other pretrained phrases already present: `alexa`, `hey_mycroft`, `timer`, `weather`.

---

## 2. Jarvis speaks first

Until now, agents **detected** things and filed a card. Now a deadline found in
your mail is **said aloud**, and the orb comes up so there is a face on the voice.

> *"Sir, IEEE conference draft deadline — from sharma@university.edu, due 2026-09-25."*

That is the mail ingestion agent's own output, spoken.

### The controls that keep it civil

A talking assistant that never shuts up is worse than one that never speaks:

| Control | Default | Why |
|---|---|---|
| `VOICE_ANNOUNCE_MIN_PRIORITY` | `high` | Only things that matter. `low`/`normal` are filed silently. |
| `VOICE_QUIET_HOURS` | `23:00-07:00` | Silent at night. Handles windows that wrap midnight. |
| `VOICE_ANNOUNCE_COOLDOWN_SECONDS` | `90` | One chatty source cannot dominate. |
| `VOICE_ANNOUNCE_DEDUPE_MINUTES` | `30` | The same sentence is never repeated. |

**`critical` breaks through quiet hours.** A security or final-deadline alert at
2am is allowed to wake you.

Every decision is explainable — `/api/proactive/history` records what it said
**and what it refused to say, with the reason**.

### Pause it instantly

```powershell
curl -X POST http://127.0.0.1:8000/api/proactive/pause -H "Authorization: Bearer <token>"
```

Or use **Integrations → Hands-Free → Pause speaking**.

---

## Try it without saying a word

**Integrations → Hands-Free:**

- **Test wake** — fires the wake event exactly as a real detection does, so you
  can confirm the whole chain (detector → UI → orb) without shouting at your laptop
- **Test voice** — makes Jarvis say a line immediately

Or from the API:

```powershell
curl -X POST http://127.0.0.1:8000/api/proactive/wake/test -H "Authorization: Bearer <token>"
curl -X POST http://127.0.0.1:8000/api/proactive/announce -H "Authorization: Bearer <token>" `
     -H "Content-Type: application/json" `
     -d '{"text":"Sir, all systems nominal.","priority":"high","force":true}'
```

---

## How it flows

```text
microphone
   │  openWakeWord scores 80ms frames on a worker thread
   ▼
"Hey Jarvis" detected
   │  run_coroutine_threadsafe onto the API event loop
   ▼
backend broadcasts {type:"wake"} over /ws/live
   ▼
the running window calls revealOrb()
   ▼
orb appears and starts listening
```

For announcements the same path carries `{type:"speak", text, show_orb}`, and the
window speaks it. **The renderer holds no policy** — priority gating, quiet hours,
cooldown and dedupe all live in one place on the backend, so the rules cannot
drift apart between windows.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Status says *"dependencies missing"* | Run the `pip install` above, then restart the app. |
| Status says *"Could not open the microphone"* | No default input device. Check Windows → Privacy → Microphone, and that a mic is plugged in. |
| Nothing happens when you say it | Lower `WAKE_WORD_THRESHOLD` to `0.3`. Check the *recent scores* on the Hands-Free panel — if they stay near zero, the mic is not reaching the app. |
| It triggers on other speech | Raise the threshold to `0.7`. |
| It fires repeatedly for one phrase | Raise `WAKE_WORD_DEBOUNCE_SECONDS`. |
| It never speaks | Check the volume, and that `VOICE_ANNOUNCE_MIN_PRIORITY` is not `critical`. Look at `/api/proactive/history` — it will show the refusal reason. |
| It talks too much | Raise `VOICE_ANNOUNCE_MIN_PRIORITY` to `critical`, or press **Pause speaking**. |

---

## Why local

openWakeWord is a small ONNX network scoring sound on your CPU. That means:

- **no audio upload** — your conversations are not sent anywhere
- **no wake-word service bill**, ever
- **works with WiFi off**
- the phrase is a **model name**, so changing it is a config edit

The trade-off: it is a keyword spotter, not full speech recognition. It only
listens for the phrase; the actual question is still transcribed by the app's
existing speech pipeline.
