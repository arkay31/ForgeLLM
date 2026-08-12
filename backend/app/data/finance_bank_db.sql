-- Finance Bank SQLite Database Schema and Seed Data
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    account_type TEXT CHECK(account_type IN ('Checking', 'Savings', 'Investment')),
    balance DECIMAL(12, 2) NOT NULL
);

CREATE TABLE transactions (
    tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    tx_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    tx_type TEXT CHECK(tx_type IN ('Deposit', 'Withdrawal', 'Transfer')),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Seed Data
INSERT INTO accounts (customer_id, account_type, balance) VALUES
(101, 'Checking', 15400.50),
(102, 'Savings', 45000.00),
(103, 'Investment', 120000.75),
(104, 'Checking', 8900.25);

INSERT INTO transactions (account_id, tx_date, amount, tx_type) VALUES
(1, '2026-08-01', 2500.00, 'Deposit'),
(1, '2026-08-03', 150.00, 'Withdrawal'),
(2, '2026-08-05', 5000.00, 'Deposit'),
(3, '2026-08-08', 12000.00, 'Deposit'),
(4, '2026-08-09', 1200.00, 'Deposit');
