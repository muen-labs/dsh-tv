# Pairing design: TV → DSH

**Goal:** a user installs one APK, opens one screen, scans a QR with their phone,
and the TV is paired — no IP address, port or token typed with a remote.

## Why the QR is on the TV, not the Mac

The TV has no camera; the phone does, and the phone is the device the user
already holds. The Mac is the trusted service both sides talk to. So the QR is
rendered **on the TV** and scanned by the **phone**, which opens a short approval
page served by the Mac. This is the same shape as TV sign-in flows (device code /
"link with code") and YouTube's TV code.

## Flow

```
 TV (PairingActivity)              Mac (host/whale_voice.py :8766)          Phone
─────────────────────              ─────────────────────────────────        ─────
 GET /pair/new ───────────────────▶ creates {id, code}  (5 min TTL)
 ◀────── {id, code, qr(png), url}
 show QR + "Code: XXXX"
        │                                │
        │                                │        scan QR ──▶ GET /pair?id
        │                                │ ◀────────────────────────────────
        │                                │  approval page (shows code)
        │                                │ ◀── POST /pair/approve  ◀── tap Approve
        │ GET /pair/status?id (1.5 s poll)
        │ ───────────────────────────────▶ now approved
        │ ◀──── {approved:true, config:{host,port,token}}
 save host/port/token ──▶ open Whale-chan
```

- The TV learns the Mac's address before showing the QR. Today that is prefilled
  from the build config / last pairing and editable; mDNS discovery is the next
  step so only the QR is needed.
- The QR content is `http://<mac>:8766/pair?id=<id>`; the id is 16 hex chars.
- The page asks the user to confirm the code shown on the TV, then approves.

## Security properties

| Property | How |
| --- | --- |
| No secret in the QR | id only; the token is returned after approval |
| Short-lived | pairing sessions expire after 300 s |
| One-time | an approved id is consumed |
| LAN-only | endpoints bound to the LAN daemon; keep 8766 off the internet |
| Confirm-on-TV | approval page shows the code the TV displays |
| No token typing on TV | token is delivered over the LAN after approval |

A LAN attacker who can read the QR (or guess a 16-hex id within 5 minutes) could
approve a device; this is the usual device-code tradeoff on a trusted home
network. Rate limiting, per-device tokens and revocation are roadmap items.

## Fallbacks

- No phone camera: the pairing screen shows the URL and the 6-character code;
  approve it from a browser on any device on the LAN (`GET /pair?id=…`).
- No QR support on the host (the `qrcode` package itself is missing): the
  daemon returns `qr: null` and the TV shows the URL + code instead. The PNG
  encoder is stdlib-only, so Pillow is not required.
- Manual override: the TV screen always includes the host field for a fixed IP,
  and the daemon's `/ask` endpoint accepts the token directly for scripts.

## Endpoints (host)

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/pair/new` | none | create pairing session + QR PNG (base64; stdlib PNG, no Pillow) |
| GET | `/pair?id=` | none | approval page (phone) |
| POST | `/pair/approve` | none, needs id | approve a session (form field `id`, or JSON `{id}` with `Accept: application/json`) |
| POST | `/pair/deny` | none, needs id | cancel a pending session (JSON `{id}`) |
| GET | `/pair/status?id=` | none | pending / approved + config (TV poll) |
| GET | `/pair/pending` | token | unapproved, unexpired sessions for the DSH GUI (`[{id,code,createdAt,ageSeconds,host}]`) |
| GET | `/health` | token | daemon status |
| POST | `/stt` | token | audio → transcript |
| POST | `/ask` | token | text → DSH reply |
| POST | `/voice` | token | audio → transcript + reply |

The DSH settings pane (`plugin/ui`) proxies the token-authenticated pair routes
from its host half, so a TV-initiated request can be approved inside DSH.

## Future

1. mDNS (`_whale-voice._tcp`) so the TV finds the Mac automatically.
2. Per-TV tokens (`devices.json`-style) + revoke in the plugin.
3. QR that deep-links into the DSH mobile client instead of a browser page.

Pairing confirmation in the DSH GUI is implemented in `plugin/ui` (Settings →
Whale-chan TV → Pairing requests).
