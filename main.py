import time
from datetime import datetime

def log_every_minute():
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open("log.txt", "a") as f:
            f.write(f"[{now}] Hello from GitHub Actions!\n")
        print(f"[{now}] Logged.")
        time.sleep(60)

if __name__ == "__main__":
    log_every_minute()
