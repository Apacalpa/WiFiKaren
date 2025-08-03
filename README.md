# KarenWiFi

**The Wi-Fi system that judges you. Out loud.**

KarenWiFi is a passive-aggressive network snitch built from a TP-Link Archer C7 router, OpenWRT and a Raspberry Pi Zero. It monitors your network activity and loudly complains about it using AI-generated insults and custom audio.

Yes, your router now criticizes you. You're welcome.

---

## What It Does

- Monitors new device connections, bandwidth usage, and DNS traffic
- Sends logs to OpenAI to generate sarcastic responses
- Converts those responses to audio using Google Cloud Text-to-Speech
- Plays them through the default out from the PI
- Absolutely does *not* help your network speed. It makes it worse on an emotional level.

---

## Hardware

- **Router**: something running OpenWRT
- **Brains**: Raspberry Pi Zero or Zero 2W
- **Sound**: some speaker (just make sure the Pi can play sound and configure the script correctly)
- **Power**: Via USB from the router itself (if possible)

---

## Current Status

- [x] Logs are monitored
- [x] AI sass is generated
- [x] Voice responses are played
- [ ] Web UI (coming... eventually... maybe... if Karen lets me)

---

## Tech Stack

- Python (main logic)
- OpenAI Assistant API (custom sarcastic prompt)
- Google Cloud Text-to-Speech
- netcat + tcpdump for log streaming
- `pygame` for audio playback

---

## Why?

Because I was tired of routers being silent.  
Silence is complicity.  
Now mine screams when someone watches Netflix in 4K.

---

## 👀 Demo

https://www.youtube.com/watch?v=HrNU0ghqL3U
