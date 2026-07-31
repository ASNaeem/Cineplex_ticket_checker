# 🎟️ Cineplex BD Automated Ticket Checker

A fast, lightweight, automated ticket release checker for **Star Cineplex Bangladesh** (`ticket.cineplexbd.com`). Checks every 30 seconds for tickets for your desired movie(s), show date(s), and branch location(s). When tickets are released, it alerts you immediately via **Loud Audio Chime**, **Windows Desktop Toast Notification**, and optional **Discord/Telegram Webhooks**.

---

## ⚡ Quick Start Guide

### Step 1: Extract Auth Token from Chrome
Since Cineplex BD APIs require user authentication, use your active Chrome login:
1. Open Chrome and go to [https://ticket.cineplexbd.com/](https://ticket.cineplexbd.com/) (logged in).
2. Press **F12** (or Right-Click -> Inspect) and click on the **Console** tab.
3. Copy and paste the code from [extract_token.js](file:///d:/Projects/Cineplex_ticket_checker/extract_token.js) into the console and press **Enter**.
4. The Bearer token will be displayed and copied to your clipboard automatically.

### Step 2: Configure `config.json`
Open [config.json](file:///d:/Projects/Cineplex_ticket_checker/config.json) and set your target preferences:
```json
{
  "auth_token": "YOUR_COPIED_BEARER_TOKEN",
  "target_movies": ["Moana"],
  "target_dates": ["ALL"],
  "target_locations": ["ALL"],
  "check_interval_seconds": 30,
  "sound_alert": true,
  "desktop_notification": true,
  "webhook_url": ""
}
```
- `target_movies`: List of movie titles to monitor (e.g. `["Moana", "Avatar"]`). Substring match is supported.
- `target_dates`: List of dates in `YYYY-MM-DD` format (e.g. `["2026-08-05", "2026-08-06"]`) or `["ALL"]`.
- `target_locations`: Branch location names (e.g. `["Bashundhara City", "Sony Square", "SKS Tower"]`) or `["ALL"]`.
- `check_interval_seconds`: `30` seconds by default.

### Step 3: Run the Ticket Checker
Run the checker script in PowerShell or Command Prompt:
```bash
python checker.py
```

---

## 📁 Project File Structure
- [checker.py](file:///d:/Projects/Cineplex_ticket_checker/checker.py): Main application runner and 30-second loop.
- [cineplex_api.py](file:///d:/Projects/Cineplex_ticket_checker/cineplex_api.py): Handles device key calculation, authentication headers, and API endpoint communication.
- [notifier.py](file:///d:/Projects/Cineplex_ticket_checker/notifier.py): Audio chime sound, native Windows Toast notification, and Webhook triggers.
- [extract_token.js](file:///d:/Projects/Cineplex_ticket_checker/extract_token.js): Chrome DevTools helper snippet to copy token.
- [config.json](file:///d:/Projects/Cineplex_ticket_checker/config.json): Configuration file.
