DROP DATABASE general_attendance;
CREATE DATABASE general_attendance;
USE general_attendance;


CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    special_id VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    password VARBINARY(255) NULL,
    role ENUM('admin', 'employee') DEFAULT 'employee'
    

);

CREATE TABLE admin_logs (
    Admin_id INT AUTO_INCREMENT PRIMARY KEY,
	user_id INT NOT NULL,
	action_taken VARCHAR(255) NOT NULL,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE

);



CREATE TABLE employee_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
	log_date DATE NOT NULL,
    time_in DATETIME NOT NULL,
	time_out DATETIME,
    
	category ENUM('Part-Time', 'Full-Time') DEFAULT 'Full-Time',
	status ENUM('on_time', 'late', 'absent')  DEFAULT 'on_time',
	department VARCHAR(100),
    
	hours_worked INT GENERATED ALWAYS AS (TIMESTAMPDIFF(HOUR, time_in, time_out)) VIRTUAL,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_log_date (log_date)

);

CREATE TABLE employee_info (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
	first_name VARCHAR(50) NOT NULL,
	last_name VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL,
	category ENUM('Part-Time', 'Full-Time') DEFAULT 'Full-Time',
	department VARCHAR(100),
    

	FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE


);

INSERT INTO users (special_id, first_name, role, password)
VALUES
('EMP-100', 'Jordan', 'employee', 'jordandagoat'),
('EMP-110', 'Gefferson', 'employee', 'bagsakonnamisacscc12'),
('EMP-121', 'Joie Ann', 'employee', 'maamsacc13ogcscc35'),
('ADM-464', 'Serge Jossiah', 'admin', 'sergecalasara');


INSERT INTO employee_logs (user_id, first_name, last_name, department, log_date, time_in, status, category)
VALUES
(1, 'Jordan', 'Cantete', 'BSCS', '2026-05-28', '2026-05-28 08:00:00', 'on_time', 'Full-Time'),
(2, 'Gefferson', 'Balase', 'BSCS', '2026-05-28', '2026-05-28 08:00:26', 'on_time', 'Part-Time'),
(3, 'Joie Ann', 'Mac', 'BSEMC', '2026-05-28', '2026-05-28 08:01:28', 'on_time', 'Full-Time');


INSERT INTO admin_logs (user_id, action_taken)
VALUES
(4, 'Manually corrected Gefferson Balase attendance record');

SHOW TABLES;
SELECT * FROM employee_logs;
SELECT * FROM users;
SELECT * FROM admin_logs;

INSERT INTO employee_info (user_id, first_name, last_name, email, category, department)
VALUES
(1, 'Jordan', 'Cantete', 'jordan@test.com', 'Full-Time', 'BSCS'),
(2, 'Gefferson', 'Balase', 'gefferson@test.com', 'Part-Time', 'BSCS'),
(3, 'Joie Ann', 'Mac', 'joie@test.com', 'Full-Time', 'BSEMC');

