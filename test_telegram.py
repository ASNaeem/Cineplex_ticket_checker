import sys
sys.path.append(r"d:\Projects\Cineplex_ticket_checker")

import json
from checker import load_config
from notifier import Notifier

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

cfg = load_config()
bot_token = cfg.get("telegram_bot_token", "")
chat_id = cfg.get("telegram_chat_id", "")

print("=== TELEGRAM BOT TEST ===")
print("Bot Token:", bot_token[:15] + "..." if bot_token else "NOT CONFIGURED")
print("Chat ID  :", chat_id if chat_id else "NOT CONFIGURED")

if not bot_token or not chat_id or bot_token == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("\n⚠️ Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your '.env' file first!")
else:
    notifier = Notifier(telegram_bot_token=bot_token, telegram_chat_id=chat_id)
    notifier.send_telegram(
        title="🔔 TEST NOTIFICATION",
        message="Your Telegram Bot is configured successfully! You will receive instant phone notifications when August 4th tickets release for Spider-Man: Brand New Day.",
        link="https://ticket.cineplexbd.com/home"
    )
