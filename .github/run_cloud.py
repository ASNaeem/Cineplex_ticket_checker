import sys
import os
import time
import json

# Fix UTF-8 encoding for Linux console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure workspace root is in sys.path
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)

from checker import run_checker_once, load_config

def main():
    print("🚀 Starting Cloud Check Block with Playwright In-Browser Fetch (Cloudflare Bypass)...")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not found in cloud environment.")
        return

    cfg = load_config()
    email = cfg.get("CINEPLEX_EMAIL", "")
    password = cfg.get("CINEPLEX_PASSWORD", "")

    with sync_playwright() as p:
        print("[*] Launching Playwright browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            print("[*] Navigating to https://ticket.cineplexbd.com/login ...")
            page.goto("https://ticket.cineplexbd.com/login", wait_until="networkidle", timeout=35000)

            if email and password:
                print(f"[*] Logging in user '{email}'...")
                try:
                    page.wait_for_selector("input", timeout=15000)
                    inputs = page.query_selector_all("input")
                    if len(inputs) >= 2:
                        inputs[0].fill(email)
                        inputs[1].fill(password)
                        submit_btn = page.query_selector("button[type='submit']") or page.query_selector("button")
                        if submit_btn:
                            submit_btn.click()
                        time.sleep(6)
                except Exception as login_err:
                    print(f"⚠️ Initial browser form fill error: {login_err}")

                user_info_raw = page.evaluate("() => localStorage.getItem('userInfo')")
                if user_info_raw:
                    try:
                        user_info = json.loads(user_info_raw)
                        token = user_info.get("token") if isinstance(user_info, dict) else None
                        if token:
                            os.environ["AUTH_TOKEN"] = token
                            print(f"✅ Token retrieved & stored for block reuse: {token[:20]}...")
                        else:
                            print("⚠️ 'userInfo' found in localStorage, but missing token.")
                    except Exception as parse_err:
                        print(f"⚠️ Failed to parse userInfo JSON: {parse_err}")
                else:
                    print("⚠️ localStorage 'userInfo' not found after initial login attempt.")

            notified_releases = set()
            for i in range(10):
                print(f"\n--- ⏱️ Cloud Iteration {i+1}/10 ---")
                try:
                    found = run_checker_once(notified_releases, page=page)
                    if found:
                        print("🎉 Match detected and notified!")
                except Exception as e:
                    print(f"⚠️ Iteration {i+1} error: {e}")
                
                if i < 9:
                    time.sleep(30)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
