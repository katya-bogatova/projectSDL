import os
import psycopg2
from psycopg2 import sql
import re
from getpass import getpass

DB_HOST = os.getenv("DB_HOST", "db3")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "db3")
LOG_FILE = os.getenv("LOG_FILE")

if not DB_NAME:
    raise Exception("DB_NAME is not set in environment")

def log_message(message, error=False):
    """Вывод в stdout и дублирование в LOG_FILE"""
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

def safe_name(name: str):
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError("Bad identifier")
    return name

def connect_db():
    while True:
        try:
            user = input("Логин: ").strip()
            password = getpass("Пароль: ")
            conninfo = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={user} password={password}"
            conn = psycopg2.connect(conninfo)
            log_message("Подключение к БД успешно")
            return conn
        except Exception:
            log_message("Ошибка подключения к базе данных", error=True)
            print("Попробуйте снова\n")

def get_tables(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        return [r[0] for r in cur.fetchall()]

def show_tables(conn):
    tables = get_tables(conn)
    log_message("\nТаблицы БД:")
    for table in tables:
        log_message(f"- {table}")

def select_all(conn):
    try:
        table = safe_name(input("Таблица: "))
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))
            rows = cur.fetchall()
            for r in rows:
                log_message(" | ".join(map(str, r)))
    except Exception:
        log_message("Ошибка выполнения SELECT", error=True)
        conn.rollback()

def select_where(conn):
    try:
        table = safe_name(input("Таблица: "))
        column = safe_name(input("Колонка: "))
        value = input("Значение: ")
        query = sql.SQL("SELECT * FROM {} WHERE {}=%s").format(sql.Identifier(table), sql.Identifier(column))
        with conn.cursor() as cur:
            cur.execute(query, (value,))
            rows = cur.fetchall()
            for r in rows:
                log_message(" | ".join(map(str, r)))
    except Exception:
        log_message("Ошибка выполнения SELECT WHERE", error=True)
        conn.rollback()

def insert_user(conn):
    try:
        name = input("Имя пользователя: ")
        email = input("Email: ")
        age = input("Возраст: ")
        city = input("Город: ")

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users(name, email, age, city)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (name, email or None, age or None, city or None))
            user_id = cur.fetchone()[0]

        conn.commit()
        log_message(f"Пользователь добавлен, id={user_id}")
        return user_id
    except Exception:
        log_message("Ошибка вставки пользователя", error=True)
        conn.rollback()
        return None

def insert_product(conn):
    try:
        name = input("Название: ")
        price = int(input("Цена: "))
        category = input("Категория: ")
        stock = int(input("Остаток: "))

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO products(name, price, category, stock)
                VALUES (%s,%s,%s,%s)
                RETURNING id
            """, (name, price, category, stock))
            product_id = cur.fetchone()[0]

        conn.commit()
        log_message(f"Товар добавлен, id={product_id}")
    except Exception:
        log_message("Ошибка вставки товара", error=True)
        conn.rollback()

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
                log_message(f"\nТовар #{i+1}")
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

def update_record(conn):
    try:
        table = safe_name(input("Таблица: "))
        column = safe_name(input("Колонка для обновления: "))
        value = input("Новое значение: ")
        where_col = safe_name(input("Колонка фильтра (WHERE): "))
        where_val = input("Значение фильтра: ")
        with conn.cursor() as cur:
            cur.execute(sql.SQL("UPDATE {} SET {}=%s WHERE {}=%s").format(
                sql.Identifier(table),
                sql.Identifier(column),
                sql.Identifier(where_col)
            ), (value, where_val))

            if cur.rowcount:
                log_message(f"Обновлено строк: {cur.rowcount}")
            else:
                log_message("Подходящие записи не найдены")

        conn.commit()
    except Exception:
        log_message("Ошибка обновления", error=True)
        conn.rollback()

def interactive_menu(conn):
    while True:
        tables = get_tables(conn)
        log_message("\nДоступные таблицы: " + ", ".join(tables))
        log_message("""
1. SELECT ALL
2. SELECT WHERE
3. Вставка пользователя
4. Вставка продукта
5. Вставка заказа
6. UPDATE записи
7. Показать таблицы
0. Выход
""")
        choice = input("> ").strip()
        if choice == "0":
            break
        elif choice == "1":
            select_all(conn)
        elif choice == "2":
            select_where(conn)
        elif choice == "3":
            insert_user(conn)
        elif choice == "4":
            insert_product(conn)
        elif choice == "5":
            insert_order(conn)
        elif choice == "6":
            update_record(conn)
        elif choice == "7":
            show_tables(conn)
        else:
            log_message("Неверный выбор", error=True)

if __name__ == "__main__":
    import sys
    conn = connect_db()
    interactive_menu(conn)
    conn.close()