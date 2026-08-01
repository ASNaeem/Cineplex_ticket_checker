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
        page.wait_for_selector("input", timeout=15000)

        inputs = page.query_selector_all("input")
        if len(inputs) >= 2:
            print("[*] Filling login credentials...")
            inputs[0].fill(email)
            inputs[1].fill(password)

        print("[*] Submitting login form...")
        submit_btn = page.query_selector("button[type='submit']") or page.query_selector("button")
        if submit_btn:
            submit_btn.click()

        time.sleep(5)
        try:
            page.goto("https://ticket.cineplexbd.com/home", wait_until="domcontentloaded", timeout=15000)
            time.sleep(1)
        except Exception:
            pass

        user_info_raw = page.evaluate("() => localStorage.getItem('userInfo')")
        if user_info_raw:
            user_info = json.loads(user_info_raw)
            token = user_info.get("token")
            if token:
                print("[+] AUTOMATED LOGIN SUCCESSFUL!")
                print(f"[+] Auth Token extracted: {token[:25]}...{token[-10:]}")
                return token
            else:
                print("[!] 'userInfo' found in localStorage, but missing token.")
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
