CREATE DATABASE IF NOT EXISTS event_management;
USE event_management;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    venue VARCHAR(150) NOT NULL,
    category_id INT,
    capacity INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('confirmed', 'cancelled') DEFAULT 'confirmed',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE KEY unique_booking (user_id, event_id)
);

INSERT IGNORE INTO categories (name) VALUES
('Technology'), ('Music'), ('Sports'), ('Art'), ('Business');

INSERT IGNORE INTO events (title, description, event_date, event_time, venue, category_id, capacity) VALUES
('Tech Expo 2026', 'The latest gadgets and AI breakthroughs on display.', '2026-11-15', '10:00:00', 'Convention Center, Lahore', 1, 200),
('Rock Night Live', 'An electrifying night with the best local bands.', '2026-11-20', '19:00:00', 'Alhamra Hall, Lahore', 2, 150),
('City Marathon', '5K and 10K runs for all fitness levels.', '2026-12-05', '06:30:00', 'Gulberg Grounds', 3, 500),
('Modern Art Showcase', 'Paintings and sculptures by emerging artists.', '2026-12-10', '15:00:00', 'National Gallery', 4, 100),
('Startup Pitch Day', 'Watch 10 startups pitch to real investors.', '2026-12-18', '11:00:00', 'NUST Auditorium', 5, 300);
