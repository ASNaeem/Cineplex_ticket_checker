import sys
import hashlib
import json
import requests
from typing import Dict, List, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class CineplexAPI:
    BASE_URL = "https://cineplex-ticket-api.cineplexbd.com/api/v1"

    def __init__(self, auth_token: str, page=None):
        self.auth_token = auth_token.strip()
        self.page = page
        self.headers = self._build_headers()

    def set_page(self, page):
        self.page = page

    def _generate_device_key(self) -> str:
        """Generates SHA-256 device-key used by Cineplex web application."""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        lang = "en-US"
        platform = "Win32"
        screen_res = "1920x1080"
        time_zone = "Asia/Dhaka"
        plugins = ""
        raw_str = f"{ua}###{lang}###{platform}###{screen_res}###{time_zone}###{plugins}"
        return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

    def _build_headers(self) -> Dict[str, str]:
        device_key = self._generate_device_key()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://ticket.cineplexbd.com',
            'Referer': 'https://ticket.cineplexbd.com/',
            'appsource': 'web',
            'device-key': device_key,
        }
        if self.auth_token and self.auth_token != "PASTE_YOUR_BEARER_TOKEN_HERE":
            token = self.auth_token if not self.auth_token.startswith("Bearer ") else self.auth_token.replace("Bearer ", "")
            headers['Authorization'] = f"Bearer {token}"
        return headers

    def update_token(self, new_token: str):
        self.auth_token = new_token.strip()
        self.headers = self._build_headers()

    def _post(self, endpoint: str, payload: dict = {}) -> Optional[dict]:
        url = f"{self.BASE_URL}/{endpoint}"

        # If Playwright browser page is active, execute fetch directly inside window to pass Cloudflare WAF
        if self.page:
            try:
                result = self.page.evaluate('''async ({url, payload, headers}) => {
                    try {
                        const res = await fetch(url, {
                            method: "POST",
                            headers: headers,
                            body: JSON.stringify(payload)
                        });
                        return await res.json();
                    } catch (e) {
                        return { fetch_error: true, message: e.toString() };
                    }
                }''', {"url": url, "payload": payload, "headers": self.headers})

                if result and isinstance(result, dict):
                    if result.get('code') == 401 or 'Unauthenticated' in str(result.get('message', '')):
                        print("❌ Error 401: Authentication Token is invalid or expired!")
                        return {"error": "unauthenticated", "message": result.get('message')}
                    if not result.get('fetch_error'):
                        return result
                    else:
                        print(f"⚠️ Playwright in-page fetch error: {result.get('message')}")
            except Exception as e:
                print(f"⚠️ Playwright evaluate error for {endpoint}: {e}")

        # Fallback to requests.post
        try:
            resp = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 401 or 'Unauthenticated' in str(data.get('message', '')):
                    print("❌ Error 401: Authentication Token is invalid or expired!")
                    return {"error": "unauthenticated", "message": data.get('message')}
                return data
            else:
                print(f"⚠️ HTTP Error {resp.status_code} for {endpoint}: {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"⚠️ Request failed for {endpoint}: {e}")
            return None

    def get_locations(self) -> List[dict]:
        """Fetch list of Cineplex cinema locations."""
        res = self._post("get-location", {})
        if res and res.get('code') == 200 and isinstance(res.get('data'), list):
            return res['data']
        return []

    def get_showdates(self, location_id: int) -> List[dict]:
        """Fetch available show dates for a specific location."""
        res = self._post("get-showdate", {"location": location_id})
        if res and res.get('code') == 200 and isinstance(res.get('data'), list):
            return res['data']
        return []

    def get_shows(self, location_id: int, show_date: str, movie_id: Optional[int] = None) -> List[dict]:
        """Fetch shows for a given location and showDate (YYYY-MM-DD)."""
        # Default to 1688 (Spider-Man: Brand New Day) if movie_id is not specified
        target_id = movie_id if movie_id is not None else 1688
        payload = {
            "location": location_id,
            "showDate": show_date,
            "movieId": target_id
        }

        res = self._post("get-shows", payload)
        if res and res.get('code') == 200 and isinstance(res.get('data'), list):
            return res['data']
        return []
