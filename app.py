import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
INTERVAL = int(os.getenv("PING_INTERVAL", 10))
LOG_FILE = os.getenv("LOG_FILE")

def write_log(message: str, is_error: bool = False):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{current_time}] {message}"

    log_output = sys.stderr if is_error else sys.stdout
    print(formatted_message, file=log_output, flush=True)

    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(f"{formatted_message}\n")
        except Exception as e:
            print(f"[ERROR] Failed to write log to file: {e}", file=sys.stderr)

def main():
    conn_params = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASS,
        "connect_timeout": 10,
    }

    while True:
        try:
            conn = psycopg2.connect(**conn_params)
            cur = conn.cursor()

            cur.execute("SELECT version();")
            version = cur.fetchone()[0]

            if version.lower().startswith("postgresql"):
                write_log(f"[OK] PostgreSQL version: {version}")
            else:
                write_log(f"[WARN] Unexpected response: {version}")

            cur.close()
            conn.close()

        except (OperationalError, Exception) as e:
            write_log(f"[ERROR] {str(e)}", is_error=True)
            write_log("[INFO] Retrying...")


        time.sleep(INTERVAL)

if __name__ == "__main__":
    if not DB_USER or not DB_PASS:
        write_log("DB_USER и DB_PASS не заданы", is_error=True)
        sys.exit(1)

    main()

