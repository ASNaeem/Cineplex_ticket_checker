import os
import sys
import json
import time
import re

# Fix Windows console encoding for emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def _generate_device_key():
    """Generates SHA-256 device-key matching the Cineplex web app."""
    import hashlib
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    raw_str = f"{ua}###en-US###Win32###1920x1080###Asia/Dhaka###"
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()


def _attempt_single_login(page, email: str, password: str) -> str:
    """Single login attempt combining UI interactions and direct API call."""
    page.goto("https://ticket.cineplexbd.com/login", wait_until="domcontentloaded", timeout=35000)
    page.wait_for_selector("#email", timeout=15000)
    time.sleep(2)

    # Fill UI form to trigger DOM/React state changes
    page.locator("#email").click()
    page.locator("#email").press_sequentially(email, delay=30)
    page.locator("#password").click()
    page.locator("#password").press_sequentially(password, delay=30)

    # Simulate subtle mouse movement to raise ReCAPTCHA v3 trust score
    page.mouse.move(200, 200)
    time.sleep(0.5)
    page.mouse.move(400, 500)
    time.sleep(0.5)

    device_key = _generate_device_key()

    result = page.evaluate('''async (args) => {
        const siteKey = '6LcnBEcsAAAAAC_qfyMoEJgKLbRDZViNc3Yv79_6';
        const recaptchaToken = await new Promise((resolve) => {
            if (window.grecaptcha) {
                window.grecaptcha.ready(() => {
                    window.grecaptcha.execute(siteKey, {action: 'login'})
                        .then(resolve).catch(() => resolve(null));
                });
            } else { resolve(null); }
        });
        if (!recaptchaToken) return {error: true, message: 'ReCAPTCHA not available'};

        try {
            const resp = await fetch('https://cineplex-ticket-api.cineplexbd.com/api/v1/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'appsource': 'web',
                    'device-key': args.deviceKey,
                },
                body: JSON.stringify({
                    email: args.email,
                    password: args.password,
                    recaptcha_token: recaptchaToken,
                }),
            });
            return await resp.json();
        } catch (e) {
            return {error: true, message: e.toString()};
        }
    }''', {'email': email, 'password': password, 'deviceKey': device_key})

    if result and result.get('code') == 200 and result.get('data'):
        token = result['data'].get('token')
        if token:
            page.evaluate(f"token => localStorage.setItem('userInfo', JSON.stringify({{token: token}}))", token)
            return token

    msg = result.get('message', 'Unknown error')
    print(f"    API response: {msg}")
    return None


def perform_login_on_page(page, email: str, password: str, max_attempts: int = 3) -> str:
    """Performs login with multiple retry attempts (full page reload between each).
    
    ReCAPTCHA v3 often flags the first headless attempt as suspicious.
    Like a real user, we dismiss the error, wait, and try again from scratch.
    """
    for attempt in range(1, max_attempts + 1):
        print(f"[*] Login attempt {attempt}/{max_attempts} — Navigating to login page...")
        try:
            token = _attempt_single_login(page, email, password)
            if token:
                print("[+] AUTOMATED LOGIN SUCCESSFUL!")
                print(f"[+] Auth Token extracted: {token[:25]}...{token[-10:]}")
                return token
            else:
                if attempt < max_attempts:
                    wait_secs = 5 * attempt  # 5s, 10s backoff
                    print(f"⚠️ Login attempt {attempt} failed. Waiting {wait_secs}s before retry...")
                    time.sleep(wait_secs)
        except Exception as e:
            print(f"[!] Login attempt {attempt} error: {e}")
            if attempt < max_attempts:
                time.sleep(5)

    print("[!] All login attempts failed. Could not retrieve auth token.")
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
