# ☁️ 100% Free 24/7 Cloud Hosting (No PC Required!)

Here is how to ensure your ticket checker **NEVER goes to sleep** on free cloud platforms:

---

## 🌟 Solution 1: GitHub Actions (NEVER Sleeps - Recommended)

### Why it doesn't sleep:
GitHub Actions is **NOT a web app**, so it has **no sleep timeout**. GitHub's cloud servers wake up automatically on a 5-minute schedule, execute the Python ticket check, send Telegram alerts if found, and finish.

### Setup (2 Minutes):
1. Push your project to a **Private GitHub Repository**.
2. Go to your repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
3. Add your secrets matching [.env](file:///d:/Projects/Cineplex_ticket_checker/.env):
   - `AUTH_TOKEN`
   - `CINEPLEX_EMAIL`
   - `CINEPLEX_PASSWORD`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `TARGET_MOVIES`: `Spider-Man: Brand New Day`
   - `TARGET_DATES`: `2026-08-04`
4. **Done!** It runs in GitHub's cloud 24/7 automatically.

---

## 🚀 Solution 2: Render.com + UptimeRobot (Keeps Awake 24/7)

### How to bypass Render's 15-minute free sleep timeout:
Render free web services sleep after 15 minutes of no web traffic. We created [server.py](file:///d:/Projects/Cineplex_ticket_checker/server.py) which adds a `/ping` endpoint. By setting up a free ping service (like UptimeRobot), Render **STAYS AWAKE 24/7 FOREVER**!

### Setup Steps:
1. Push project to GitHub.
2. Sign up at [https://render.com/](https://render.com/) (Free) -> **New Web Service**.
3. Set Start Command: `python server.py`
4. Add your `.env` secrets under **Environment**.
5. Once deployed, copy your Render URL (e.g. `https://my-checker.onrender.com`).
6. Sign up at [https://uptimerobot.com/](https://uptimerobot.com/) (100% Free).
7. Create a **HTTP Monitor** pointing to your Render URL every 5 minutes.
8. Render will now **NEVER sleep**!
