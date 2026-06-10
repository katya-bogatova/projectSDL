import os
import sys
import psycopg2
from psycopg2 import sql
import re
from getpass import getpass

# ---------------- ENV CONFIG ----------------
DB_HOST = os.getenv("DB_HOST", "db3")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "db3")
LOG_FILE = os.getenv("LOG_FILE")

if not DB_NAME:
    raise Exception("DB_NAME is not set in environment")

# ---------------- LOGGING ----------------
def log_message(message, error=False):
    """Вывод в stdout/stderr и дублирование в LOG_FILE"""
    if error:
        print(message, file=sys.stderr)
    else:
        print(message)
    if LOG_FILE:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception:
            pass

# ---------------- SECURITY ----------------
def safe_name(name: str):
    """Проверка названия таблицы или колонки"""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError("Bad identifier")
    return name

# ---------------- CONNECT ----------------
def connect_db():
    try:
        user = input("Логин: ").strip()
        password = getpass("Пароль: ")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=user,
            password=password
        )
        log_message("Подключение к БД успешно")
        return conn
    except psycopg2.OperationalError:
        log_message(
            "Неверный логин или пароль",
            error=True
        )
        sys.exit(1)
    except EOFError:
        log_message(
            "Приложение запущено без интерактивной консоли",
            error=True
        )
        sys.exit(1)
    except Exception:
        log_message(
            "Ошибка подключения к базе данных",
            error=True
        )
        sys.exit(1)

# ---------------- TABLES ----------------
def get_tables(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        return [r[0] for r in cur.fetchall()]

# ---------------- SELECT ----------------
def select_records(conn):
    try:
        table = safe_name(input("Таблица: "))
        count = int(
            input(
                "Сколько условий фильтрации (0 для всех записей): "
            )
        )
        with conn.cursor() as cur:
            if count == 0:
                query = sql.SQL(
                    "SELECT * FROM {}"
                ).format(
                    sql.Identifier(table)
                )
                cur.execute(query)
            else:
                conditions = []
                params = []
                for i in range(count):
                    column = safe_name(
                        input(f"Колонка #{i+1}: ")
                    )
                    value = input(
                        f"Значение #{i+1}: "
                    )
                    conditions.append(
                        sql.SQL("{} = %s").format(
                            sql.Identifier(column)
                        )
                    )
                    params.append(value)
                query = sql.SQL(
                    "SELECT * FROM {} WHERE "
                ).format(
                    sql.Identifier(table)
                ) + sql.SQL(" AND ").join(conditions)
                cur.execute(
                    query,
                    params
                )
            rows = cur.fetchall()
            for row in rows:
                log_message(
                    " | ".join(map(str, row))
                )
    except Exception:
        log_message(
            "Ошибка выполнения SELECT",
            error=True
        )
        conn.rollback()

# ---------------- UNIVERSAL INSERT ----------------
def insert_into_table(conn):
    try:
        table_name = safe_name(input("Таблица: "))
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = [row[0] for row in cur.fetchall()]
        count = int(input("Сколько строк добавить: "))
        rows = []
        for i in range(count):
            print(f"\nСтрока {i + 1}")
            values = []
            for col in columns:
                if col == "id":  # пропускаем SERIAL
                    continue
                val = input(f"{col}: ")
                values.append(val if val != "" else None)
            rows.append(values)
        insert_columns = [c for c in columns if c != "id"]
        placeholders = ", ".join(["%s"] * len(insert_columns))
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(", ").join(map(sql.Identifier, insert_columns)),
            sql.SQL(placeholders)
        )
        with conn.cursor() as cur:
            cur.executemany(query, rows)
        conn.commit()
        log_message(f"Добавлено строк: {len(rows)}")
    except Exception:
        log_message("Ошибка вставки данных", error=True)
        conn.rollback()

# ---------------- INSERT ORDER ----------------
def insert_order(conn):
    try:
        user_id = int(input("ID пользователя: "))
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if not cur.fetchone():
                raise Exception(f"Пользователь {user_id} не найден")
            cur.execute("INSERT INTO orders(user_id) VALUES (%s) RETURNING id", (user_id,))
            order_id = cur.fetchone()[0]
            count = int(input("Сколько товаров в заказе: "))
            items = []
            for i in range(count):
                log_message(f"\nТовар #{i + 1}")
                product_id = int(input("ID товара: "))
                quantity = int(input("Количество: "))
                cur.execute("SELECT price FROM products WHERE id=%s", (product_id,))
                row = cur.fetchone()
                if not row:
                    raise Exception(f"Товар {product_id} не найден")
                price = row[0]
                items.append((order_id, product_id, quantity, price))
            cur.executemany("""
                INSERT INTO order_items(order_id, product_id, quantity, unit_price)
                VALUES (%s,%s,%s,%s)
            """, items)
        conn.commit()
        log_message(f"Заказ создан, id={order_id}")
    except Exception:
        log_message("Ошибка создания заказа", error=True)
        conn.rollback()

# ---------------- UPDATE ----------------
def update_records(conn):
    try:
        table = safe_name(
            input("Таблица: ")
        )
        update_column = safe_name(
            input("Обновляемая колонка: ")
        )
        update_value = input(
            "Новое значение: "
        )
        where_column = safe_name(
            input("Колонка фильтра: ")
        )
        values = input(
            "Значения через запятую: "
        )
        values_list = [
            v.strip()
            for v in values.split(",")
        ]
        placeholders = sql.SQL(", ").join(
            [sql.Placeholder()] * len(values_list)
        )
        query = sql.SQL("""
            UPDATE {}
            SET {} = %s
            WHERE {} IN ({})
        """).format(
            sql.Identifier(table),
            sql.Identifier(update_column),
            sql.Identifier(where_column),
            placeholders
        )
        with conn.cursor() as cur:
            cur.execute(
                query,
                [update_value] + values_list
            )
            if cur.rowcount:
                log_message(
                    f"Обновлено строк: {cur.rowcount}"
                )
            else:
                log_message(
                    "Подходящие записи не найдены"
                )
        conn.commit()
    except Exception:
        log_message(
            "Ошибка обновления",
            error=True
        )
        conn.rollback()
        
def update_multiple_records(conn):
    try:
        table = safe_name(input("Таблица: "))
        update_column = safe_name(input("Обновляемая колонка: "))
        update_value = input("Новое значение: ")
        where_column = safe_name(input("Колонка фильтра: "))
        values = input(
            "Значения через запятую: "
        )
        values_list = [
            v.strip()
            for v in values.split(",")
        ]
        placeholders = sql.SQL(", ").join(
            [sql.Placeholder()] * len(values_list)
        )
        query = sql.SQL("""
            UPDATE {}
            SET {} = %s
            WHERE {} IN ({})
        """).format(
            sql.Identifier(table),
            sql.Identifier(update_column),
            sql.Identifier(where_column),
            placeholders
        )
        with conn.cursor() as cur:
            cur.execute(
                query,
                [update_value] + values_list
            )
            log_message(
                f"Обновлено строк: {cur.rowcount}"
            )
        conn.commit()
    except Exception:
        log_message(
            "Ошибка обновления",
            error=True
        )
        conn.rollback()

# ---------------- MENU ----------------
def interactive_menu(conn):
    while True:
        tables = get_tables(conn)
        log_message("\nДоступные таблицы: " + ", ".join(tables))
        log_message("""
1. SELECT
2. INSERT в таблицу
3. INSERT заказ
4. UPDATE
0. Выход
""")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "1":
            select_records(conn)
        elif choice == "2":
            insert_into_table(conn)
        elif choice == "3":
            insert_order(conn)
        elif choice == "4":
            update_records(conn)
        else:
            log_message(
                "Неверный выбор",
                error=True
            )

# ---------------- MAIN ----------------
if __name__ == "__main__":
    conn = connect_db()
    interactive_menu(conn)
    conn.close()