-- E-Commerce SQLite Database Schema and Seed Data
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status TEXT CHECK(status IN ('Pending', 'Completed', 'Shipped', 'Cancelled')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    review_date DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Seed Data
INSERT INTO customers (first_name, last_name, email, country) VALUES
('Alice', 'Smith', 'alice@example.com', 'USA'),
('Bob', 'Jones', 'bob@example.com', 'Canada'),
('Charlie', 'Brown', 'charlie@example.com', 'UK'),
('Diana', 'Prince', 'diana@example.com', 'Germany'),
('Evan', 'Wright', 'evan@example.com', 'USA'),
('Fiona', 'Gallagher', 'fiona@example.com', 'Canada');

INSERT INTO products (name, category, price, stock_quantity) VALUES
('MacBook Pro M3', 'Electronics', 1999.99, 45),
('Wireless Noise-Canceling Headphones', 'Electronics', 299.99, 120),
('Ergonomic Mesh Chair', 'Furniture', 349.50, 30),
('Mechanical RGB Keyboard', 'Electronics', 129.00, 85),
('Ultra-Wide 34 Monitor', 'Electronics', 699.99, 20),
('Organic Fair-Trade Coffee 1lb', 'Grocery', 18.99, 300);

INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, '2026-07-01', 2299.98, 'Completed'),
(2, '2026-07-05', 349.50, 'Completed'),
(1, '2026-07-15', 129.00, 'Shipped'),
(3, '2026-07-20', 699.99, 'Completed'),
(4, '2026-08-01', 1999.99, 'Completed'),
(5, '2026-08-05', 318.98, 'Completed'),
(6, '2026-08-08', 299.99, 'Pending');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1999.99),
(1, 2, 1, 299.99),
(2, 3, 1, 349.50),
(3, 4, 1, 129.00),
(4, 5, 1, 699.99),
(5, 1, 1, 1999.99),
(6, 2, 1, 299.99),
(6, 6, 1, 18.99),
(7, 2, 1, 299.99);

INSERT INTO reviews (product_id, customer_id, rating, comment, review_date) VALUES
(1, 1, 5, 'Absolute beast of a machine for machine learning!', '2026-07-03'),
(2, 1, 4, 'Great noise cancellation for office coding.', '2026-07-03'),
(3, 2, 5, 'Cured my lower back pain.', '2026-07-07'),
(5, 3, 4, 'Immersive screen real estate.', '2026-07-22');
