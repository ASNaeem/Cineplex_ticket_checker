// Run this in Chrome DevTools Console (F12 -> Console) while on https://ticket.cineplexbd.com/
(function() {
    try {
        const userInfo = localStorage.getItem("userInfo");
        if (!userInfo) {
            console.error("❌ No userInfo found in localStorage! Make sure you are logged in at https://ticket.cineplexbd.com/login");
            return;
        }
        const parsed = JSON.parse(userInfo);
        const token = parsed.token;
        if (token) {
            console.log("%c✅ CINEPLEX AUTH TOKEN FOUND:", "color: #00ff00; font-size: 14px; font-weight: bold;");
            console.log(token);
            navigator.clipboard.writeText(token).then(() => {
                console.log("%c📋 Token copied to clipboard automatically!", "color: #00bfff; font-size: 12px;");
            }).catch(() => {
                console.log("👉 Please copy the token printed above manually into config.json");
            });
        } else {
            console.error("❌ Token not found inside userInfo object.");
        }
    } catch(e) {
        console.error("❌ Error reading token:", e);
    }
})();
