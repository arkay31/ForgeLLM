-- HR Analytics SQLite Database Schema and Seed Data
DROP TABLE IF EXISTS performance_reviews;
DROP TABLE IF EXISTS salaries;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name TEXT NOT NULL,
    location TEXT NOT NULL,
    budget DECIMAL(12, 2) NOT NULL
);

CREATE TABLE employees (
    emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    dept_id INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE salaries (
    salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER NOT NULL,
    base_salary DECIMAL(10, 2) NOT NULL,
    bonus DECIMAL(10, 2) DEFAULT 0.00,
    effective_date DATE NOT NULL,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

CREATE TABLE performance_reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id INTEGER NOT NULL,
    review_year INTEGER NOT NULL,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    notes TEXT,
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

-- Seed Data
INSERT INTO departments (dept_name, location, budget) VALUES
('AI Research', 'San Francisco', 5000000.00),
('Backend Engineering', 'Seattle', 3500000.00),
('Product Design', 'New York', 2000000.00),
('Data Science', 'Austin', 2800000.00);

INSERT INTO employees (first_name, last_name, email, role, dept_id, hire_date) VALUES
('Elena', 'Rostova', 'elena@company.ai', 'Principal AI Engineer', 1, '2024-01-15'),
('Marcus', 'Vance', 'marcus@company.ai', 'Senior Backend Architect', 2, '2024-03-01'),
('Sophia', 'Chen', 'sophia@company.ai', 'Lead UI/UX Designer', 3, '2024-06-10'),
('David', 'Kim', 'david@company.ai', 'Staff Data Scientist', 4, '2024-09-01'),
('Hannah', 'Abbott', 'hannah@company.ai', 'MLOps Engineer', 1, '2025-02-15'),
('Liam', 'Miller', 'liam@company.ai', 'Senior Systems Engineer', 2, '2025-04-01');

INSERT INTO salaries (emp_id, base_salary, bonus, effective_date) VALUES
(1, 210000.00, 45000.00, '2026-01-01'),
(2, 185000.00, 30000.00, '2026-01-01'),
(3, 160000.00, 20000.00, '2026-01-01'),
(4, 175000.00, 25000.00, '2026-01-01'),
(5, 155000.00, 18000.00, '2026-01-01'),
(6, 165000.00, 22000.00, '2026-01-01');

INSERT INTO performance_reviews (emp_id, review_year, rating, notes) VALUES
(1, 2025, 5, 'Exceeded expectations. Published key LLM quantization paper.'),
(2, 2025, 5, 'Architected sub-10ms distributed microservices.'),
(3, 2025, 4, 'Redesigned core platform UI with high user satisfaction.'),
(4, 2025, 5, 'Built production SQL evaluation pipeline.'),
(5, 2025, 4, 'Implemented robust GPU cluster monitoring.');
