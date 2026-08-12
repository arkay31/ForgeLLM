-- Concert Singer SQLite Database Schema and Seed Data
DROP TABLE IF EXISTS singer_in_concert;
DROP TABLE IF EXISTS concert;
DROP TABLE IF EXISTS singer;

CREATE TABLE singer (
    singer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    song_name TEXT,
    song_release_year TEXT,
    age INTEGER,
    is_male BOOLEAN
);

CREATE TABLE concert (
    concert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    concert_name TEXT NOT NULL,
    theme TEXT,
    stadium_id INTEGER,
    year INTEGER NOT NULL
);

CREATE TABLE singer_in_concert (
    concert_id INTEGER NOT NULL,
    singer_id INTEGER NOT NULL,
    FOREIGN KEY (concert_id) REFERENCES concert(concert_id),
    FOREIGN KEY (singer_id) REFERENCES singer(singer_id)
);

-- Seed Data
INSERT INTO singer (name, country, song_name, song_release_year, age, is_male) VALUES
('Adele', 'UK', 'Hello', '2015', 35, 0),
('Taylor Swift', 'USA', 'Anti-Hero', '2022', 34, 0),
('Ed Sheeran', 'UK', 'Shape of You', '2017', 33, 1),
('Bruno Mars', 'USA', 'Uptown Funk', '2014', 38, 1),
('Dua Lipa', 'UK', 'Levitating', '2020', 28, 0);

INSERT INTO concert (concert_name, theme, stadium_id, year) VALUES
('The Eras Tour', 'Pop & Country', 101, 2023),
('Mathematics Tour', 'Acoustic Pop', 102, 2022),
('Future Nostalgia Tour', 'Disco Pop', 103, 2021),
('World Stadium Tour', 'Classic R&B', 104, 2019);

INSERT INTO singer_in_concert (concert_id, singer_id) VALUES
(1, 2), -- Taylor Swift in The Eras Tour (2023)
(2, 3), -- Ed Sheeran in Mathematics Tour (2022)
(3, 5), -- Dua Lipa in Future Nostalgia Tour (2021)
(4, 4); -- Bruno Mars in World Stadium Tour (2019)
