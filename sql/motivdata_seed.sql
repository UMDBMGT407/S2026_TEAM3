-- Motiv fake data for MySQL Workbench
-- Run motivdata_schema.sql first (all tables, including app_user.is_active and post.post_photo_path).
-- Password for all seeded accounts: password123 (werkzeug scrypt hash below).
-- Safe to re-run: truncates seeded tables first (requires tables to exist).

USE motivdata;

SET NAMES utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE workout_log;
TRUNCATE TABLE workout;
TRUNCATE TABLE group_workout_attendance;
TRUNCATE TABLE post;
TRUNCATE TABLE challenge_participant_exclusion;
TRUNCATE TABLE user_challenge_leave;
TRUNCATE TABLE challenge;
TRUNCATE TABLE group_workout;
TRUNCATE TABLE group_invite;
TRUNCATE TABLE user_group;
TRUNCATE TABLE motiv_group;
TRUNCATE TABLE exercise;
TRUNCATE TABLE app_user;
TRUNCATE TABLE group_admin;
TRUNCATE TABLE admin;
SET FOREIGN_KEY_CHECKS = 1;

SET @pw := 'scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70';

START TRANSACTION;

INSERT INTO admin (admin_name, admin_first_name, admin_last_name, admin_email, password_hash) VALUES
('Admin One', 'Alex', 'Rivera', 'admin@motiv.test', @pw),
('Admin Two', 'Sam', 'Chen', 'admin2@motiv.test', @pw);

INSERT INTO group_admin (group_admin_name, group_admin_first_name, group_admin_last_name, group_admin_email, password_hash) VALUES
('GA Jordan', 'Jordan', 'Lee', 'ga@motiv.test', @pw),
('GA Morgan', 'Morgan', 'Patel', 'ga2@motiv.test', @pw);

INSERT INTO app_user (user_name, user_first_name, user_last_name, user_email, password_hash, is_active) VALUES
('jdoe', 'John', 'Doe', 'john@motiv.test', @pw, 1),
('jsmith', 'Jane', 'Smith', 'jane@motiv.test', @pw, 1),
('bobk', 'Bob', 'Kim', 'bob@motiv.test', @pw, 1);

INSERT INTO motiv_group (group_name, group_description, group_date_created, admin_id, group_admin_id) VALUES
('Morning Lifters', 'Early gym crew', '2026-01-15', 1, 1),
('Campus Runners', 'Track and trail runs', '2026-02-01', 1, 1),
('Yoga Circle', 'Relaxation and mobility', '2026-02-10', 2, 2);

INSERT INTO user_group (user_id, group_id) VALUES
(1, 1), (1, 2), (2, 1), (3, 2), (3, 3);

INSERT INTO challenge (challenge_title, challenge_date, challenge_start_date, challenge_end_date, challenge_status, challenge_goal, group_admin_id, group_id) VALUES
('Spring Step Count', '2026-03-01', '2026-03-01', '2026-03-31', 'active', 'Walk 10k steps daily', 1, 1),
('April Strength', '2026-04-01', '2026-04-01', '2026-04-30', 'active', '12 workouts this month', 1, 2);

INSERT INTO group_workout (group_workout_title, group_workout_description, group_workout_scheduled_date, group_workout_start_date, group_workout_end_date, group_workout_location, group_id, group_admin_id) VALUES
('Leg Day', 'Squats and accessories', '2026-04-07', '2026-04-07', '2026-04-07', 'Eppley Rec Center', 1, 1),
('Group Run', '5K easy pace', '2026-04-08', '2026-04-08', '2026-04-08', 'Campus loop', 2, 1),
('Morning Yoga', 'Vinyasa flow', '2026-04-09', '2026-04-09', '2026-04-09', 'Studio B', 3, 2);

INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level) VALUES
('Back Squat', 'Legs', 'intermediate'),
('Bench Press', 'Chest', 'intermediate'),
('Sit-ups', 'Abs', 'beginner'),
('Deadlift', 'Back', 'advanced'),
('Treadmill Run', 'Cardio', 'beginner');

INSERT INTO workout (workout_date, workout_duration_minutes, user_id, group_workout_id) VALUES
('2026-03-27', 40, 1, 1),
('2026-03-27', 36, 1, NULL),
('2026-03-26', 25, 2, NULL),
('2026-03-25', 15, 3, 2);

INSERT INTO workout_log (workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id) VALUES
(3, 10, 135.00, 1, 1),
(4, 8, 185.00, 1, 2),
(3, 20, 0.00, 2, 3),
(5, 5, 225.00, 3, 4);

INSERT INTO post (post_content, post_photo_path, post_date, post_time, admin_id, user_id) VALUES
('Great session today everyone!', NULL, '2026-04-01', '09:30:00', 1, 1),
('Hit a new PR on squat', NULL, '2026-04-02', '18:00:00', NULL, 2),
('Who is joining the weekend run?', NULL, '2026-04-03', '12:15:00', NULL, 3);

COMMIT;
