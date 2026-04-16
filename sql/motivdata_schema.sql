-- Motiv ERD schema for MySQL Workbench
-- Paste into a new query tab, then execute.
-- Re-runs: uses CREATE TABLE IF NOT EXISTS. For a full reset: DROP DATABASE motivdata; then run again.

CREATE DATABASE IF NOT EXISTS motivdata
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE motivdata;

SET NAMES utf8mb4;
SET SESSION default_storage_engine = 'InnoDB';

-- Platform admin (monitors posts, directs groups)
CREATE TABLE IF NOT EXISTS admin (
  admin_id INT AUTO_INCREMENT PRIMARY KEY,
  admin_name VARCHAR(255),
  admin_first_name VARCHAR(255) NOT NULL,
  admin_last_name VARCHAR(255) NOT NULL,
  admin_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL
);

-- Group admin (administers groups, manages challenges, supervises group workouts)
CREATE TABLE IF NOT EXISTS group_admin (
  group_admin_id INT AUTO_INCREMENT PRIMARY KEY,
  group_admin_name VARCHAR(255),
  group_admin_first_name VARCHAR(255) NOT NULL,
  group_admin_last_name VARCHAR(255) NOT NULL,
  group_admin_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL
);

-- End users
CREATE TABLE IF NOT EXISTS app_user (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  user_name VARCHAR(255),
  user_first_name VARCHAR(255) NOT NULL,
  user_last_name VARCHAR(255) NOT NULL,
  user_email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(512) NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS motiv_group (
  group_id INT AUTO_INCREMENT PRIMARY KEY,
  group_name VARCHAR(255) NOT NULL,
  group_description TEXT,
  group_date_created DATE NOT NULL,
  admin_id INT NOT NULL,
  group_admin_id INT NOT NULL,
  CONSTRAINT fk_group_admin FOREIGN KEY (admin_id) REFERENCES admin (admin_id),
  CONSTRAINT fk_group_group_admin FOREIGN KEY (group_admin_id) REFERENCES group_admin (group_admin_id)
);

CREATE TABLE IF NOT EXISTS user_group (
  user_id INT NOT NULL,
  group_id INT NOT NULL,
  PRIMARY KEY (user_id, group_id),
  CONSTRAINT fk_ug_user FOREIGN KEY (user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_ug_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id) ON DELETE CASCADE
);

-- Group admins invite app users (see sql/migration_group_invite.sql; included here for fresh installs)
CREATE TABLE IF NOT EXISTS group_invite (
  invite_id INT AUTO_INCREMENT PRIMARY KEY,
  group_id INT NOT NULL,
  invited_user_id INT NOT NULL,
  invited_by_group_admin_id INT NOT NULL,
  invite_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  invite_status VARCHAR(32) NOT NULL DEFAULT 'pending',
  CONSTRAINT fk_gi_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id) ON DELETE CASCADE,
  CONSTRAINT fk_gi_user FOREIGN KEY (invited_user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_gi_ga FOREIGN KEY (invited_by_group_admin_id) REFERENCES group_admin (group_admin_id),
  UNIQUE KEY uq_group_invite_user (group_id, invited_user_id)
);

CREATE TABLE IF NOT EXISTS group_workout (
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

CREATE TABLE IF NOT EXISTS group_workout_attendance (
  attendance_id INT AUTO_INCREMENT PRIMARY KEY,
  group_workout_id INT NOT NULL,
  user_id INT NOT NULL,
  attendance_status VARCHAR(16) NOT NULL DEFAULT 'pending',
  attendance_updated DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_gwa_workout FOREIGN KEY (group_workout_id)
    REFERENCES group_workout (group_workout_id) ON DELETE CASCADE,
  CONSTRAINT fk_gwa_user FOREIGN KEY (user_id)
    REFERENCES app_user (user_id) ON DELETE CASCADE,
  UNIQUE KEY uq_gwa_workout_user (group_workout_id, user_id)
);

CREATE TABLE IF NOT EXISTS post (
  post_id INT AUTO_INCREMENT PRIMARY KEY,
  post_content TEXT,
  post_photo_path VARCHAR(255) NULL,
  post_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  post_time TIME NULL,
  post_date DATE NULL,
  admin_id INT NULL,
  user_id INT NOT NULL,
  CONSTRAINT fk_post_admin FOREIGN KEY (admin_id) REFERENCES admin (admin_id),
  CONSTRAINT fk_post_user FOREIGN KEY (user_id) REFERENCES app_user (user_id)
);

CREATE TABLE IF NOT EXISTS challenge (
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

CREATE TABLE IF NOT EXISTS challenge_participant_exclusion (
  exclusion_id INT AUTO_INCREMENT PRIMARY KEY,
  challenge_id INT NOT NULL,
  user_id INT NOT NULL,
  removed_by_admin_id INT NOT NULL,
  removed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cpe_challenge FOREIGN KEY (challenge_id) REFERENCES challenge (challenge_id) ON DELETE CASCADE,
  CONSTRAINT fk_cpe_user FOREIGN KEY (user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_cpe_admin FOREIGN KEY (removed_by_admin_id) REFERENCES admin (admin_id),
  UNIQUE KEY uq_cpe_challenge_user (challenge_id, user_id)
);

CREATE TABLE IF NOT EXISTS user_challenge_leave (
  leave_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  challenge_id INT NOT NULL,
  left_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ucl_user FOREIGN KEY (user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_ucl_challenge FOREIGN KEY (challenge_id) REFERENCES challenge (challenge_id) ON DELETE CASCADE,
  UNIQUE KEY uq_ucl_user_challenge (user_id, challenge_id)
);

CREATE TABLE IF NOT EXISTS exercise (
  exercise_id INT AUTO_INCREMENT PRIMARY KEY,
  exercise_name VARCHAR(255) NOT NULL,
  exercise_muscle_group VARCHAR(128) NULL,
  exercise_difficulty_level VARCHAR(64) NULL
);

CREATE TABLE IF NOT EXISTS workout (
  workout_id INT AUTO_INCREMENT PRIMARY KEY,
  workout_date DATE NOT NULL,
  workout_duration_minutes INT NULL COMMENT 'Duration stored in minutes',
  user_id INT NOT NULL,
  group_workout_id INT NULL,
  CONSTRAINT fk_workout_user FOREIGN KEY (user_id) REFERENCES app_user (user_id),
  CONSTRAINT fk_workout_gw FOREIGN KEY (group_workout_id) REFERENCES group_workout (group_workout_id)
);

CREATE TABLE IF NOT EXISTS workout_log (
  workout_log_id INT AUTO_INCREMENT PRIMARY KEY,
  workout_num_sets INT NULL,
  workout_num_reps INT NULL,
  workout_num_weight DECIMAL(10, 2) NULL,
  workout_id INT NOT NULL,
  exercise_id INT NOT NULL,
  CONSTRAINT fk_wl_workout FOREIGN KEY (workout_id) REFERENCES workout (workout_id) ON DELETE CASCADE,
  CONSTRAINT fk_wl_exercise FOREIGN KEY (exercise_id) REFERENCES exercise (exercise_id)
);
