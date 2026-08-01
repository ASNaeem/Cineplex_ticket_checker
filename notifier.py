import sys
import os
import time
import subprocess
import json
import urllib.request

try:
    import winsound
except ImportError:
    winsound = None

# Fix console encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class Notifier:
    def __init__(self, sound_alert=True, desktop_notification=True, webhook_url="", telegram_bot_token="", telegram_chat_id=""):
        self.sound_alert = sound_alert
        self.desktop_notification = desktop_notification
        self.webhook_url = webhook_url
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def trigger_audio_chime(self):
        """Play a loud, distinctive victory chime when tickets are found."""
        if not winsound:
            return
        try:
            tones = [(523, 150), (659, 150), (784, 150), (1046, 400)]
            for freq, duration in tones:
                winsound.Beep(freq, duration)
        except Exception as e:
            print(f"⚠️ Could not play audio alert: {e}")

    def show_desktop_toast(self, title, message):
        """Display a Windows desktop toast balloon notification."""
        if not self.desktop_notification or os.name != 'nt':
            return
        
        try:
            clean_title = title.replace("'", "''")
            clean_msg = message.replace("'", "''")
            
            ps_script = f"""
            [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms')
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.Visible = $true
            $notify.ShowBalloonTip(10000, '{clean_title}', '{clean_msg}', [System.Windows.Forms.ToolTipIcon]::Info)
            """
            subprocess.Popen(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script],
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception as e:
            print(f"⚠️ Could not trigger desktop notification: {e}")

    def send_webhook(self, title, message, link="https://ticket.cineplexbd.com/home"):
        """Send optional Discord or generic Webhook notification."""
        if not self.webhook_url or not self.webhook_url.strip():
            return
            
        try:
            payload = {
                "content": f"🚨 **{title}** 🚨\n{message}\n🔗 Buy tickets: {link}"
            }
            req = urllib.request.Request(
                self.webhook_url.strip(),
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'CineplexTicketChecker/1.0'}
            )
            urllib.request.urlopen(req, timeout=5)
            print("📱 Webhook alert sent successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send webhook alert: {e}")

    def send_telegram(self, title, message, link="https://ticket.cineplexbd.com/home"):
        """Send instant alert to your phone via Telegram Bot API."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return
            
        bot_token = self.telegram_bot_token.strip()
        chat_id = self.telegram_chat_id.strip()
        
        if not bot_token or not chat_id or bot_token == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
            return

        try:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            text_msg = f"{message}\n\n🎟️ [Book Tickets Now]({link})"
            payload = {
                "chat_id": chat_id,
                "text": text_msg,
                "parse_mode": "Markdown"
            }
            req = urllib.request.Request(
                tg_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=5)
            print("📱 Telegram phone alert sent successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send Telegram alert: {e}")

    def send_auth_token_alert(self):
        """Send Telegram notification alerting user to update their AUTH_TOKEN."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return

        bot_token = self.telegram_bot_token.strip()
        chat_id = self.telegram_chat_id.strip()

        if not bot_token or not chat_id or bot_token == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
            return

        try:
            tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            text_msg = (
                "⚠️ *Cineplex Ticket Checker Alert* ⚠️\n\n"
                "🔑 *AUTH_TOKEN Expired or Invalid!*\n\n"
                "Automated login was blocked by ReCAPTCHA bot protection.\n"
                "Please copy a fresh Bearer `token` from browser DevTools and update your `AUTH_TOKEN` in GitHub Secrets / `.env` to keep receiving ticket notifications.\n\n"
                "🎟️ [Open Cineplex Login](https://ticket.cineplexbd.com/login)"
            )
            payload = {
                "chat_id": chat_id,
                "text": text_msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            req = urllib.request.Request(
                tg_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(req, timeout=5)
            print("📲 Telegram AUTH_TOKEN refresh alert sent successfully!")
        except Exception as e:
            print(f"⚠️ Failed to send Telegram AUTH_TOKEN alert: {e}")

    def notify_release(self, movie_name, location_name, show_date, booking_link="https://ticket.cineplexbd.com/home"):
        """Trigger all enabled notifications for a ticket release match."""
        title = "🎉 CINEPLEX TICKET RELEASED!"
        msg = f"🎉 *CINEPLEX TICKET RELEASED!*\n\n🎬 *Movie*: {movie_name}\n📍 *Location*: {location_name}\n📅 *Date*: {show_date}"
        
        print("\n" + "="*60)
        print(f"🚨 ALERT! MATCH FOUND FOR '{movie_name}' 🚨")
        print(f"📍 Location: {location_name}")
        print(f"📅 Date: {show_date}")
        print(f"🔗 Link: {booking_link}")
        print("="*60 + "\n")

        if self.sound_alert:
            self.trigger_audio_chime()
            
        self.show_desktop_toast(title, f"Movie: {movie_name}\nLocation: {location_name}\nDate: {show_date}")
        self.send_webhook(title, msg, booking_link)
        self.send_telegram(title, msg, booking_link)
