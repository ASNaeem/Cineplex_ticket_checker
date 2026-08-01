import os
import sys
import time
import json
import re
from datetime import datetime
from cineplex_api import CineplexAPI
from notifier import Notifier

ENV_FILE = ".env"
CONFIG_FILE = "config.json"

def load_env_file(filepath: str) -> dict:
    env_vars = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

def load_config() -> dict:
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config.update(json.load(f))
            except Exception:
                pass

    env_vars = load_env_file(ENV_FILE)

    def get_var(key, default=""):
        val = os.environ.get(key)
        if val is not None and val.strip():
            return val.strip()
        val = env_vars.get(key)
        if val is not None and val.strip():
            return val.strip()
        return default

    auth_token = get_var("AUTH_TOKEN")
    if auth_token:
        config["auth_token"] = auth_token

    email = get_var("CINEPLEX_EMAIL")
    if email:
        config["CINEPLEX_EMAIL"] = email

    password = get_var("CINEPLEX_PASSWORD")
    if password:
        config["CINEPLEX_PASSWORD"] = password

    movies = get_var("TARGET_MOVIES")
    if movies:
        config["target_movies"] = [m.strip() for m in movies.split(",") if m.strip()]

    dates = get_var("TARGET_DATES")
    if dates:
        config["target_dates"] = [d.strip() for d in dates.split(",") if d.strip()]

    locations = get_var("TARGET_LOCATIONS")
    if locations:
        config["target_locations"] = [l.strip() for l in locations.split(",") if l.strip()]

    interval = get_var("CHECK_INTERVAL_SECONDS")
    if interval:
        try:
            config["check_interval_seconds"] = int(interval)
        except ValueError:
            pass

    sound = get_var("SOUND_ALERT")
    if sound:
        config["sound_alert"] = str(sound).lower() in ("true", "1", "yes")

    desktop = get_var("DESKTOP_NOTIFICATION")
    if desktop:
        config["desktop_notification"] = str(desktop).lower() in ("true", "1", "yes")

    webhook = get_var("WEBHOOK_URL")
    if webhook:
        config["webhook_url"] = webhook

    tg_token = get_var("TELEGRAM_BOT_TOKEN")
    if tg_token:
        config["telegram_bot_token"] = tg_token

    tg_chat = get_var("TELEGRAM_CHAT_ID")
    if tg_chat:
        config["telegram_chat_id"] = tg_chat

    return config

def normalize_title(t: str) -> str:
    """Removes spaces and punctuation for robust movie title matching."""
    return re.sub(r'[^a-zA-Z0-9]', '', str(t)).lower()

def is_movie_match(movie_title: str, target_movies: list) -> bool:
    if not target_movies or "ALL" in [m.upper() for m in target_movies]:
        return True
    norm_title = normalize_title(movie_title)
    for target in target_movies:
        norm_target = normalize_title(target)
        if norm_target in norm_title or norm_title in norm_target:
            return True
    return False

def is_date_match(show_date_str: str, target_dates: list) -> bool:
    if not target_dates or "ALL" in [d.upper() for d in target_dates]:
        return True
    
    # Direct match or YYYY-MM-DD match
    for d in target_dates:
        d_clean = d.strip()
        if d_clean == show_date_str:
            return True
        # Handle '4th aug' or 'aug 4' conversion to 2026-08-04
        if "4" in d_clean and ("aug" in d_clean.lower() or "08" in d_clean):
            if show_date_str.endswith("08-04") or show_date_str.endswith("8-4"):
                return True
    return False

def is_location_match(loc_name: str, loc_id: int, target_locations: list) -> bool:
    if not target_locations or "ALL" in [str(l).upper() for l in target_locations]:
        return True
    loc_name_lower = loc_name.lower()
    for target in target_locations:
        target_str = str(target).lower()
        if target_str in loc_name_lower or target_str == str(loc_id):
            return True
    return False

def run_checker_once(notified_releases=None, page=None) -> bool:
    if notified_releases is None:
        notified_releases = set()

    config = load_config()
    auth_token = config.get("auth_token", "")
    email = config.get("CINEPLEX_EMAIL", "")
    password = config.get("CINEPLEX_PASSWORD", "")

    if (not auth_token or auth_token == "PASTE_YOUR_BEARER_TOKEN_HERE") and email and password:
        try:
            from auto_login import auto_login_and_get_token
            auth_token = auto_login_and_get_token(email, password)
        except Exception:
            pass

    if not auth_token:
        print("❌ Auth token missing.")
        return False

    target_movies = config.get("target_movies", ["Spider-Man: Brand New Day"])
    target_dates = config.get("target_dates", ["ALL"])
    target_locations = config.get("target_locations", ["ALL"])

    notifier = Notifier(
        sound_alert=config.get("sound_alert", True),
        desktop_notification=config.get("desktop_notification", True),
        webhook_url=config.get("webhook_url", ""),
        telegram_bot_token=config.get("telegram_bot_token", ""),
        telegram_chat_id=config.get("telegram_chat_id", "")
    )

    api = CineplexAPI(auth_token, page=page)
    locations = api.get_locations()

    if not locations and email and password:
        try:
            from auto_login import perform_login_on_page, auto_login_and_get_token
            if page:
                new_token = perform_login_on_page(page, email, password)
            else:
                new_token = auto_login_and_get_token(email, password)

            if new_token:
                os.environ["AUTH_TOKEN"] = new_token
                api.update_token(new_token)
                locations = api.get_locations()
        except Exception as e:
            print(f"⚠️ Automatic token refresh failed: {e}")

    if not locations:
        print("⚠️ No locations returned.")
        try:
            notifier.send_auth_token_alert()
        except Exception:
            pass
        return False

    match_found = False
    for loc in locations:
        loc_id = loc.get("id") or loc.get("locationId") or loc.get("location_id")
        loc_name = loc.get("locationTitle") or loc.get("location_title") or loc.get("name") or loc.get("locationName") or loc.get("location_name") or f"Location #{loc_id}"

        if not is_location_match(loc_name, loc_id, target_locations):
            continue

        showdates = api.get_showdates(loc_id)
        for sd in showdates:
            show_date = sd.get("showDate") or sd.get("date") or sd.get("show_date")
            if not show_date:
                continue

            if is_date_match(show_date, target_dates):
                shows = api.get_shows(loc_id, show_date)
                for show in shows:
                    movie_title = show.get("movieName") or show.get("title") or show.get("name") or ""
                    if is_movie_match(movie_title, target_movies):
                        match_key = f"{loc_id}_{show_date}_{movie_title}"
                        match_found = True
                        print(f"  🎉 FOUND! Movie: '{movie_title}' | Location: '{loc_name}' | Date: '{show_date}'")

                        if match_key not in notified_releases:
                            notified_releases.add(match_key)
                            booking_url = f"https://ticket.cineplexbd.com/home?location_id={loc_id}&date={show_date}"
                            notifier.notify_release(movie_title, loc_name, show_date, booking_url)

    if not match_found:
        print("  ℹ️ No tickets released yet for target criteria.")

    return match_found

def run_checker():
    config = load_config()
    check_interval = config.get("check_interval_seconds", 30)

    print("\n🎬 =====================================================")
    print("🎟️ CINEPLEX BD AUTOMATED TICKET CHECKER INITIALIZED")
    print("=====================================================")
    print(f"🎯 Target Movie(s)   : {', '.join(config.get('target_movies', []))}")
    print(f"📅 Target Date(s)    : {', '.join(config.get('target_dates', []))}")
    print(f"📍 Target Location(s): {', '.join(map(str, config.get('target_locations', [])))}")
    print(f"⏱️ Check Interval   : Every {check_interval} seconds")
    print("=====================================================\n")

    notified_releases = set()
    check_count = 0

    page = None
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        print("[*] Launching Playwright browser instance...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        print("[*] Navigating to https://ticket.cineplexbd.com/ ...")
        page.goto("https://ticket.cineplexbd.com/", wait_until="networkidle", timeout=35000)
    except Exception as e:
        print(f"ℹ️ Playwright browser not initialized ({e}). Using direct HTTP mode.")

    while True:
        check_count += 1
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{current_time}] 🔍 Check #{check_count}: Querying Cineplex API...")

        try:
            run_checker_once(notified_releases, page=page)
        except Exception as e:
            print(f"⚠️ Check #{check_count} error: {e}")

        print(f"⏳ Waiting {check_interval} seconds until next check...")
        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        run_checker()
    except KeyboardInterrupt:
        print("\n👋 Ticket checker stopped by user.")
