# Security policy

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private reporting: on this repository, **Security → Report a vulnerability**. Include what you found, how to reproduce it, and the commit you tested.

You should get a first reply within a week.

## Scope

In scope: the TV bridge APK (`android/tv-assistant`), the Mac daemon and tools (`host/`), the DSH plugin (`plugin/`), and anything that could expose a pairing token, let another device on the network control the TV, or leak audio.

Out of scope: DeepSeek Harness itself, model providers, Android, and third-party TV apps.

## Good to know

- The bridge and daemon are meant for a home LAN. Never forward ports 8765/8766 to the internet.
- Every TV → daemon call needs the pairing token; pairing codes expire after 5 minutes.
- Tokens live in `.auth/` (gitignored) and in the TV app's private storage. If you find one committed anywhere in this repository or its history, report it privately as above.
