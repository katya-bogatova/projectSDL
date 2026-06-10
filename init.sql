DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    age INT,
    city TEXT
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    price INT NOT NULL,
    category TEXT,
    stock INT
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    order_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT,
    unit_price INT
);

-- Тесты
INSERT INTO users (name, email, age, city) VALUES
('Katya', 'katya@example.com', 25, 'Amsterdam'),
('Anna', 'anna@example.com', 22, 'Rotterdam'),
('Maria', 'maria@example.com', 30, 'Utrecht'),
('Ivan', 'ivan@example.com', 28, 'Haarlem'),
('Olga', 'olga@example.com', 35, 'Groningen'),
('Peter', 'peter@example.com', 27, 'Eindhoven'),
('Lena', 'lena@example.com', 24, 'Leiden'),
('John', 'john@example.com', 32, 'Maastricht');

SELECT setval(
    'users_id_seq',
    (SELECT MAX(id) FROM users)
);

INSERT INTO products (name, price, category, stock) VALUES
('Phone', 500, 'Electronics', 50),
('Laptop', 1500, 'Electronics', 20),
('Tablet', 800, 'Electronics', 30),
('Headphones', 150, 'Electronics', 100),
('Smartwatch', 250, 'Electronics', 75),
('Backpack', 80, 'Accessories', 200),
('Shoes', 120, 'Clothing', 150),
('T-shirt', 25, 'Clothing', 300);

SELECT setval(
    'products_id_seq',
    (SELECT MAX(id) FROM products)
);

INSERT INTO orders (user_id, order_date) VALUES
(1, '2026-06-01'),
(2, '2026-06-02'),
(3, '2026-06-03'),
(4, '2026-06-04'),
(5, '2026-06-05'),
(6, '2026-06-06'),
(7, '2026-06-07'),
(8, '2026-06-08');

SELECT setval(
    'orders_id_seq',
    (SELECT MAX(id) FROM orders)
);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1,1,2,500),(1,4,1,150),(2,2,1,1500),(2,5,2,250),
(3,3,1,800),(3,1,1,500),(4,4,3,150),(5,2,2,1500),
(5,5,1,250),(6,6,2,80),(6,7,1,120),(7,8,3,25),
(8,1,1,500),(8,3,2,800);

SELECT setval(
    'order_items_id_seq',
    (SELECT MAX(id) FROM order_items)
);

CREATE USER app_user WITH PASSWORD '1234';
GRANT CONNECT ON DATABASE db3 TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;0
