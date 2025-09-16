import json
import getpass
import psycopg2
from psycopg2 import OperationalError

def load_config(path="dbconfig.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    config = load_config("dbconfig.json")

    username = input("Введите логин: ").strip()
    password = getpass.getpass("Введите пароль: ")

    conn_params = {
        "host": config.get("host", "localhost"),
        "port": config.get("port", 5432),
        "dbname": config.get("dbname"),
        "user": username,
        "password": password,
    }

    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print("PostgreSQL version:", version)
        cur.close()
        conn.close()
    except OperationalError as e:
        print("Ошибка подключения:", e)

if __name__ == "__main__":
    main()
