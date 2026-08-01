import os
import sys
import json
import time
import re

# Fix Windows console encoding for emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def perform_login_on_page(page, email: str, password: str) -> str:
    """Performs login using an existing Playwright Page object and returns extracted Bearer token."""
    print(f"[*] Navigating to https://ticket.cineplexbd.com/login ...")
    try:
        page.goto("https://ticket.cineplexbd.com/login", wait_until="domcontentloaded", timeout=35000)
        page.wait_for_selector("#email", timeout=15000)

        print("[*] Filling login credentials...")
        page.locator("#email").click()
        page.locator("#email").press_sequentially(email, delay=30)
        page.locator("#email").dispatch_event("change")

        page.locator("#password").click()
        page.locator("#password").press_sequentially(password, delay=30)
        page.locator("#password").dispatch_event("change")

        print("[*] Submitting login form...")
        page.click("button.green-bg")

        for _ in range(12):
            time.sleep(1)
            user_info_raw = page.evaluate("() => localStorage.getItem('userInfo')")
            if user_info_raw:
                try:
                    user_info = json.loads(user_info_raw)
                    token = user_info.get("token")
                    if token:
                        print("[+] AUTOMATED LOGIN SUCCESSFUL!")
                        print(f"[+] Auth Token extracted: {token[:25]}...{token[-10:]}")
                        return token
                except Exception:
                    pass
        print("[!] Failed to extract token from localStorage.")
    except Exception as e:
        print(f"[!] Login execution error on page: {e}")
    return None

def auto_login_and_get_token(email: str, password: str) -> str:
    """Automates login on ticket.cineplexbd.com to fetch Bearer Auth Token."""
    print(f"[*] Attempting automated login for user '{email}'...")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright module not found. Please run: pip install playwright")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            try:
                token = perform_login_on_page(page, email, password)
                if token:
                    update_env_auth_token(token)
                return token
            finally:
                browser.close()
    except Exception as e:
        print(f"[!] Automated login error: {e}")
        return None

def update_env_auth_token(token: str):
    """Update AUTH_TOKEN in .env file."""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        if re.search(r"^AUTH_TOKEN=.*$", content, flags=re.MULTILINE):
            new_content = re.sub(r"^AUTH_TOKEN=.*$", f"AUTH_TOKEN={token}", content, flags=re.MULTILINE)
        else:
            new_content = content + f"\nAUTH_TOKEN={token}\n"

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("[+] Saved fresh AUTH_TOKEN to '.env' file!")

if __name__ == "__main__":
    from checker import load_config
    cfg = load_config()
    email = cfg.get("CINEPLEX_EMAIL") or "01766202327"
    password = cfg.get("CINEPLEX_PASSWORD") or "movie@7l33Pl377"
    auto_login_and_get_token(email, password)
