-- Motiv ERD schema for MySQL Workbench
-- Paste into a new query tab, then execute.

CREATE DATABASE IF NOT EXISTS motivdata
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE motivdata;

-- Platform admin (monitors posts, directs groups)
CREATE TABLE admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  admin_name VARCHAR(255),
  admin_first_name VARCHAR(255) NOT NULL,
  admin_last_name VARCHAR(255) NOT NULL,
  admin_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL
);

-- Group admin (administers groups, manages challenges, supervises group workouts)
CREATE TABLE group_admin (
  group_admin_id INT AUTO_INCREMENT PRIMARY KEY,
  group_admin_name VARCHAR(255),
  group_admin_first_name VARCHAR(255) NOT NULL,
  group_admin_last_name VARCHAR(255) NOT NULL,
  group_admin_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL
);

-- End users
CREATE TABLE app_user (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  user_name VARCHAR(255),
  user_first_name VARCHAR(255) NOT NULL,
  user_last_name VARCHAR(255) NOT NULL,
  user_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE motiv_group (
  group_id INT AUTO_INCREMENT PRIMARY KEY,
  group_name VARCHAR(255) NOT NULL,
  group_description TEXT,
  group_date_created DATE NOT NULL,
  admin_id INT NOT NULL,
  group_admin_id INT NOT NULL,
  CONSTRAINT fk_group_admin FOREIGN KEY (admin_id) REFERENCES admin (admin_id),
  CONSTRAINT fk_group_group_admin FOREIGN KEY (group_admin_id) REFERENCES group_admin (group_admin_id)
);

CREATE TABLE user_group (
  user_id INT NOT NULL,
  group_id INT NOT NULL,
  PRIMARY KEY (user_id, group_id),
  CONSTRAINT fk_ug_user FOREIGN KEY (user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_ug_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id) ON DELETE CASCADE
);

CREATE TABLE post (
  post_id INT AUTO_INCREMENT PRIMARY KEY,
  post_content TEXT,
  post_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  post_time TIME NULL,
  post_date DATE NULL,
  admin_id INT NULL,
  user_id INT NOT NULL,
  CONSTRAINT fk_post_admin FOREIGN KEY (admin_id) REFERENCES admin (admin_id),
  CONSTRAINT fk_post_user FOREIGN KEY (user_id) REFERENCES app_user (user_id)
);

CREATE TABLE challenge (
  challenge_id INT AUTO_INCREMENT PRIMARY KEY,
  challenge_title VARCHAR(255) NOT NULL,
  challenge_date DATE NULL,
  challenge_start_date DATE NULL,
  challenge_end_date DATE NULL,
  challenge_status VARCHAR(64) NULL,
  challenge_goal TEXT NULL,
  group_admin_id INT NOT NULL,
  group_id INT NOT NULL,
  CONSTRAINT fk_challenge_ga FOREIGN KEY (group_admin_id) REFERENCES group_admin (group_admin_id),
  CONSTRAINT fk_challenge_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id)
);

CREATE TABLE group_workout (
  group_workout_id INT AUTO_INCREMENT PRIMARY KEY,
  group_workout_title VARCHAR(255) NOT NULL,
  group_workout_description TEXT NULL,
  group_workout_scheduled_date DATE NULL,
  group_workout_scheduled_time TIME NULL,
  group_workout_start_date DATE NULL,
  group_workout_end_date DATE NULL,
  group_workout_location VARCHAR(255) NULL,
  group_id INT NOT NULL,
  group_admin_id INT NOT NULL,
  CONSTRAINT fk_gw_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id),
  CONSTRAINT fk_gw_ga FOREIGN KEY (group_admin_id) REFERENCES group_admin (group_admin_id)
);

CREATE TABLE exercise (
  exercise_id INT AUTO_INCREMENT PRIMARY KEY,
  exercise_name VARCHAR(255) NOT NULL,
  exercise_muscle_group VARCHAR(128) NULL,
  exercise_difficulty_level VARCHAR(64) NULL
);

CREATE TABLE workout (
  workout_id INT AUTO_INCREMENT PRIMARY KEY,
  workout_date DATE NOT NULL,
  workout_duration_minutes INT NULL COMMENT 'Duration stored in minutes',
  user_id INT NOT NULL,
  group_workout_id INT NULL,
  CONSTRAINT fk_workout_user FOREIGN KEY (user_id) REFERENCES app_user (user_id),
  CONSTRAINT fk_workout_gw FOREIGN KEY (group_workout_id) REFERENCES group_workout (group_workout_id)
);

CREATE TABLE workout_log (
  workout_log_id INT AUTO_INCREMENT PRIMARY KEY,
  workout_num_sets INT NULL,
  workout_num_reps INT NULL,
  workout_num_weight DECIMAL(10, 2) NULL,
  workout_id INT NOT NULL,
  exercise_id INT NOT NULL,
  CONSTRAINT fk_wl_workout FOREIGN KEY (workout_id) REFERENCES workout (workout_id) ON DELETE CASCADE,
  CONSTRAINT fk_wl_exercise FOREIGN KEY (exercise_id) REFERENCES exercise (exercise_id)
);
