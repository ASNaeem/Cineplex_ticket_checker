import os
import sys
import json
import time
import re

# Fix Windows console encoding for emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def auto_login_and_get_token(email: str, password: str) -> str:
    """Automates login on ticket.cineplexbd.com to fetch Bearer Auth Token and updates .env."""
    print(f"[*] Attempting automated login for user '{email}'...")
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[!] Playwright module not found. Please run: pip install playwright")
        return None

    token = None
    with sync_playwright() as p:
        # Launch chromium browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        try:
            print("[*] Navigating to https://ticket.cineplexbd.com/login ...")
            page.goto("https://ticket.cineplexbd.com/login", wait_until="networkidle", timeout=35000)

            print("[*] Filling login credentials...")
            page.wait_for_selector("input", timeout=15000)

            # Target input fields
            inputs = page.query_selector_all("input")
            if len(inputs) >= 2:
                inputs[0].fill(email)
                inputs[1].fill(password)
            else:
                print("[!] Login input fields not matched.")

            print("[*] Submitting login form...")
            # Click submit button
            submit_btn = page.query_selector("button[type='submit']") or page.query_selector("button")
            if submit_btn:
                submit_btn.click()

            time.sleep(6)

            # Extract userInfo from localStorage
            user_info_raw = page.evaluate("() => localStorage.getItem('userInfo')")
            if user_info_raw:
                user_info = json.loads(user_info_raw)
                token = user_info.get("token")
                if token:
                    print("[+] AUTOMATED LOGIN SUCCESSFUL!")
                    print(f"[+] Auth Token extracted: {token[:25]}...{token[-10:]}")
                else:
                    print("[!] 'userInfo' found in localStorage, but missing token.")
            else:
                print("[-] 'userInfo' not found in localStorage after login.")

        except Exception as e:
            print(f"[!] Automated login error: {e}")
        finally:
            browser.close()

    if token:
        update_env_auth_token(token)
    return token

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
