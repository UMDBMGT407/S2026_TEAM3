-- Append-only April bulk data seeding for motivdata
-- Safe mode: no TRUNCATE / DELETE. Designed for MySQL 8+.
-- Requested outcomes:
--   1) Evenly spread active users across existing groups.
--   2) Add 20-30 scheduled group workouts and 20-30 challenges in April 2026.
--   3) Ensure each active app_user has about 5-6 "full" workouts in April (with workout_log rows).
--
-- How to run:
--   1) Paste into MySQL Workbench.
--   2) Execute all.
--   3) Review validation SELECTs near the end.
--   4) COMMIT if results look good, otherwise ROLLBACK.

USE motivdata;
SET NAMES utf8mb4;
START TRANSACTION;

DROP PROCEDURE IF EXISTS sp_seed_april_bulk_append;
DELIMITER $$
CREATE PROCEDURE sp_seed_april_bulk_append()
BEGIN
  DECLARE v_group_count INT DEFAULT 0;
  DECLARE v_user_count INT DEFAULT 0;
  DECLARE v_ga_count INT DEFAULT 0;
  DECLARE v_ex_count INT DEFAULT 0;

  DECLARE v_sched_target INT DEFAULT 0;
  DECLARE v_chal_target INT DEFAULT 0;
  DECLARE v_run_tag VARCHAR(32) DEFAULT '';

  DECLARE v_i INT DEFAULT 0;
  DECLARE v_j INT DEFAULT 0;
  DECLARE v_k INT DEFAULT 0;

  DECLARE v_gid INT DEFAULT NULL;
  DECLARE v_gaid INT DEFAULT NULL;
  DECLARE v_uid INT DEFAULT NULL;
  DECLARE v_user_group_id INT DEFAULT NULL;
  DECLARE v_wid INT DEFAULT NULL;
  DECLARE v_exid INT DEFAULT NULL;
  DECLARE v_chid INT DEFAULT NULL;
  DECLARE v_gwid INT DEFAULT NULL;

  DECLARE v_current_apr INT DEFAULT 0;
  DECLARE v_desired_apr INT DEFAULT 0;
  DECLARE v_to_add INT DEFAULT 0;
  DECLARE v_logs_per_workout INT DEFAULT 0;
  DECLARE v_status VARCHAR(16) DEFAULT 'pending';

  DECLARE v_workout_date DATE;
  DECLARE v_sched_date DATE;
  DECLARE v_start_date DATE;
  DECLARE v_end_date DATE;
  DECLARE v_sched_time TIME;
  DECLARE v_duration INT DEFAULT 0;
  DECLARE v_goal INT DEFAULT 0;
  DECLARE v_sets INT DEFAULT 0;
  DECLARE v_reps INT DEFAULT 0;
  DECLARE v_ex_offset INT DEFAULT 0;
  DECLARE v_weight DECIMAL(10,2) DEFAULT 0.00;

  DECLARE done_users INT DEFAULT 0;
  DECLARE cur_users CURSOR FOR
    SELECT user_id
    FROM app_user
    WHERE is_active = 1
    ORDER BY user_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done_users = 1;

  -- Preconditions
  SELECT COUNT(*) INTO v_group_count FROM motiv_group;
  SELECT COUNT(*) INTO v_user_count FROM app_user WHERE is_active = 1;
  SELECT COUNT(*) INTO v_ga_count FROM group_admin;
  SELECT COUNT(*) INTO v_ex_count FROM exercise;

  IF v_group_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: motiv_group has 0 rows.';
  END IF;
  IF v_user_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: app_user has 0 active rows.';
  END IF;
  IF v_ga_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: group_admin has 0 rows.';
  END IF;

  SET v_run_tag = DATE_FORMAT(NOW(), '%Y%m%d%H%i%s');
  SET v_sched_target = 20 + FLOOR(RAND() * 11);
  SET v_chal_target = 20 + FLOOR(RAND() * 11);

  -- Ensure baseline exercises exist for workout_log FK usage.
  INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
  SELECT 'Back Squat', 'Legs', 'intermediate'
  FROM dual
  WHERE NOT EXISTS (SELECT 1 FROM exercise WHERE exercise_name = 'Back Squat' LIMIT 1);
  INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
  SELECT 'Bench Press', 'Chest', 'intermediate'
  FROM dual
  WHERE NOT EXISTS (SELECT 1 FROM exercise WHERE exercise_name = 'Bench Press' LIMIT 1);
  INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
  SELECT 'Sit-ups', 'Abs', 'beginner'
  FROM dual
  WHERE NOT EXISTS (SELECT 1 FROM exercise WHERE exercise_name = 'Sit-ups' LIMIT 1);
  INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
  SELECT 'Deadlift', 'Back', 'advanced'
  FROM dual
  WHERE NOT EXISTS (SELECT 1 FROM exercise WHERE exercise_name = 'Deadlift' LIMIT 1);
  INSERT INTO exercise (exercise_name, exercise_muscle_group, exercise_difficulty_level)
  SELECT 'Treadmill Run', 'Cardio', 'beginner'
  FROM dual
  WHERE NOT EXISTS (SELECT 1 FROM exercise WHERE exercise_name = 'Treadmill Run' LIMIT 1);

  -- Bridge: ensure each group_admin email exists as app_user (for GA workout compatibility in app.py).
  INSERT INTO app_user (user_name, user_first_name, user_last_name, user_email, password_hash, is_active)
  SELECT
    CONCAT('ga_bridge_', ga.group_admin_id),
    ga.group_admin_first_name,
    ga.group_admin_last_name,
    ga.group_admin_email,
    ga.password_hash,
    1
  FROM group_admin ga
  LEFT JOIN app_user u
    ON u.user_email = ga.group_admin_email
  WHERE u.user_id IS NULL;

  -- Even spread: map active users across groups by row number ring.
  DROP TEMPORARY TABLE IF EXISTS tmp_seed_groups;
  CREATE TEMPORARY TABLE tmp_seed_groups (
    rn INT PRIMARY KEY,
    group_id INT NOT NULL,
    group_admin_id INT NOT NULL
  );

  INSERT INTO tmp_seed_groups (rn, group_id, group_admin_id)
  SELECT
    ROW_NUMBER() OVER (ORDER BY g.group_id) AS rn,
    g.group_id,
    g.group_admin_id
  FROM motiv_group g;

  DROP TEMPORARY TABLE IF EXISTS tmp_seed_users;
  CREATE TEMPORARY TABLE tmp_seed_users (
    rn INT PRIMARY KEY,
    user_id INT NOT NULL
  );

  INSERT INTO tmp_seed_users (rn, user_id)
  SELECT
    ROW_NUMBER() OVER (ORDER BY u.user_id) AS rn,
    u.user_id
  FROM app_user u
  WHERE u.is_active = 1;

  INSERT IGNORE INTO user_group (user_id, group_id)
  SELECT
    su.user_id,
    sg.group_id
  FROM tmp_seed_users su
  JOIN tmp_seed_groups sg
    ON sg.rn = ((su.rn - 1) MOD v_group_count) + 1;

  -- Create 20-30 scheduled group workouts in April 2026.
  SET v_i = 1;
  WHILE v_i <= v_sched_target DO
    SELECT group_id, group_admin_id
      INTO v_gid, v_gaid
    FROM tmp_seed_groups
    WHERE rn = ((v_i - 1) MOD v_group_count) + 1
    LIMIT 1;

    SET v_sched_date = DATE_ADD('2026-04-01', INTERVAL FLOOR(RAND() * 30) DAY);
    SET v_sched_time = MAKETIME(6 + FLOOR(RAND() * 13), ELT(1 + FLOOR(RAND() * 4), 0, 15, 30, 45), 0);

    INSERT INTO group_workout (
      group_workout_title,
      group_workout_description,
      group_workout_scheduled_date,
      group_workout_scheduled_time,
      group_workout_start_date,
      group_workout_end_date,
      group_workout_location,
      group_id,
      group_admin_id
    )
    VALUES (
      CONCAT('Seed ', v_run_tag, ' Scheduled Workout ', LPAD(v_i, 2, '0')),
      CONCAT('Auto-seeded scheduled workout #', v_i, ' for April 2026'),
      v_sched_date,
      v_sched_time,
      v_sched_date,
      v_sched_date,
      CONCAT('Facility ', ((v_i - 1) MOD 7) + 1),
      v_gid,
      v_gaid
    );

    SET v_i = v_i + 1;
  END WHILE;

  -- Create 20-30 challenges in April 2026.
  SET v_i = 1;
  WHILE v_i <= v_chal_target DO
    SELECT group_id, group_admin_id
      INTO v_gid, v_gaid
    FROM tmp_seed_groups
    WHERE rn = ((v_i - 1) MOD v_group_count) + 1
    LIMIT 1;

    SET v_start_date = DATE_ADD('2026-04-01', INTERVAL FLOOR(RAND() * 24) DAY);
    SET v_end_date = DATE_ADD(v_start_date, INTERVAL (3 + FLOOR(RAND() * 7)) DAY);
    IF v_end_date > '2026-04-30' THEN
      SET v_end_date = '2026-04-30';
    END IF;
    SET v_goal = 5 + FLOOR(RAND() * 16); -- 5..20

    INSERT INTO challenge (
      challenge_title,
      challenge_date,
      challenge_start_date,
      challenge_end_date,
      challenge_status,
      challenge_goal,
      group_admin_id,
      group_id
    )
    VALUES (
      CONCAT('Seed ', v_run_tag, ' Challenge ', LPAD(v_i, 2, '0')),
      v_start_date,
      v_start_date,
      v_end_date,
      CASE
        WHEN v_end_date < CURDATE() THEN 'completed'
        WHEN v_start_date > CURDATE() THEN 'upcoming'
        ELSE 'active'
      END,
      CAST(v_goal AS CHAR),
      v_gaid,
      v_gid
    );

    SET v_i = v_i + 1;
  END WHILE;

  -- Add attendance for seeded scheduled workouts (subset of users in the same group).
  INSERT IGNORE INTO group_workout_attendance (group_workout_id, user_id, attendance_status)
  SELECT
    gw.group_workout_id,
    ug.user_id,
    CASE
      WHEN MOD(gw.group_workout_id + ug.user_id, 5) = 0 THEN 'declined'
      WHEN MOD(gw.group_workout_id + ug.user_id, 3) = 0 THEN 'pending'
      ELSE 'accepted'
    END AS attendance_status
  FROM group_workout gw
  JOIN user_group ug
    ON ug.group_id = gw.group_id
  WHERE gw.group_workout_title LIKE CONCAT('Seed ', v_run_tag, ' Scheduled Workout %')
    AND MOD(gw.group_workout_id + ug.user_id, 4) <> 0;

  -- Ensure each active user has about 5-6 full workouts in April 2026.
  -- desired: odd user_id => 6, even user_id => 5.
  OPEN cur_users;
  user_loop: LOOP
    FETCH cur_users INTO v_uid;
    IF done_users = 1 THEN
      LEAVE user_loop;
    END IF;

    SELECT COUNT(*)
      INTO v_current_apr
    FROM workout w
    WHERE w.user_id = v_uid
      AND w.workout_date BETWEEN '2026-04-01' AND '2026-04-30';

    SET v_desired_apr = 5 + MOD(v_uid, 2);
    SET v_to_add = GREATEST(v_desired_apr - v_current_apr, 0);

    SET v_j = 1;
    WHILE v_j <= v_to_add DO
      SET v_workout_date = DATE_ADD('2026-04-01', INTERVAL FLOOR(RAND() * 30) DAY);
      SET v_duration = 25 + FLOOR(RAND() * 66); -- 25..90

      SELECT ug.group_id
        INTO v_user_group_id
      FROM user_group ug
      WHERE ug.user_id = v_uid
      ORDER BY ug.group_id
      LIMIT 1;

      SET v_chid = NULL;
      SET v_gwid = NULL;

      IF v_user_group_id IS NOT NULL THEN
        -- Prefer an April challenge in the user's group (if exists).
        SELECT c.challenge_id
          INTO v_chid
        FROM challenge c
        WHERE c.group_id = v_user_group_id
          AND COALESCE(c.challenge_start_date, '2026-04-01') <= '2026-04-30'
          AND COALESCE(c.challenge_end_date, '2026-04-30') >= '2026-04-01'
        ORDER BY c.challenge_id DESC
        LIMIT 1;

        -- About half of workouts linked to a group_workout.
        IF MOD(v_j + v_uid, 2) = 0 THEN
          SELECT gw.group_workout_id
            INTO v_gwid
          FROM group_workout gw
          WHERE gw.group_id = v_user_group_id
            AND gw.group_workout_scheduled_date BETWEEN '2026-04-01' AND '2026-04-30'
          ORDER BY gw.group_workout_id DESC
          LIMIT 1;
        END IF;
      END IF;

      INSERT INTO workout (
        workout_date,
        workout_duration_minutes,
        user_id,
        group_workout_id,
        challenge_id
      )
      VALUES (
        v_workout_date,
        v_duration,
        v_uid,
        v_gwid,
        v_chid
      );

      SET v_wid = LAST_INSERT_ID();
      SET v_logs_per_workout = 2 + FLOOR(RAND() * 2); -- 2..3 log rows

      SET v_k = 1;
      WHILE v_k <= v_logs_per_workout DO
        SELECT COUNT(*) INTO v_ex_count FROM exercise;
        SET v_ex_offset = FLOOR(RAND() * v_ex_count);

        SELECT e.exercise_id
          INTO v_exid
        FROM exercise e
        ORDER BY e.exercise_id
        LIMIT 1 OFFSET v_ex_offset;

        IF v_exid IS NULL THEN
          SELECT exercise_id INTO v_exid FROM exercise ORDER BY exercise_id LIMIT 1;
        END IF;

        SET v_sets = 2 + FLOOR(RAND() * 5);      -- 2..6
        SET v_reps = 6 + FLOOR(RAND() * 15);     -- 6..20
        SET v_weight = ROUND(5 + (RAND() * 195), 2);

        INSERT INTO workout_log (
          workout_num_sets,
          workout_num_reps,
          workout_num_weight,
          workout_id,
          exercise_id
        )
        VALUES (
          v_sets,
          v_reps,
          v_weight,
          v_wid,
          v_exid
        );

        SET v_k = v_k + 1;
      END WHILE;

      SET v_j = v_j + 1;
    END WHILE;
  END LOOP;
  CLOSE cur_users;

  -- Summary for this run
  SELECT
    v_run_tag AS seed_run_tag,
    v_sched_target AS scheduled_workout_target,
    v_chal_target AS challenge_target,
    (SELECT COUNT(*) FROM group_workout
     WHERE group_workout_title LIKE CONCAT('Seed ', v_run_tag, ' Scheduled Workout %')) AS scheduled_workouts_inserted,
    (SELECT COUNT(*) FROM challenge
     WHERE challenge_title LIKE CONCAT('Seed ', v_run_tag, ' Challenge %')) AS challenges_inserted;
END $$
DELIMITER ;

CALL sp_seed_april_bulk_append();
DROP PROCEDURE IF EXISTS sp_seed_april_bulk_append;

-- =========================
-- Validation checks
-- =========================

-- 1) Membership spread by group
SELECT
  g.group_id,
  g.group_name,
  COUNT(ug.user_id) AS members
FROM motiv_group g
LEFT JOIN user_group ug ON ug.group_id = g.group_id
GROUP BY g.group_id, g.group_name
ORDER BY g.group_id;

-- 2) April 2026 workload per active user (should be around 5-6)
SELECT
  u.user_id,
  u.user_email,
  COUNT(w.workout_id) AS april_workouts
FROM app_user u
LEFT JOIN workout w
  ON w.user_id = u.user_id
 AND w.workout_date BETWEEN '2026-04-01' AND '2026-04-30'
WHERE u.is_active = 1
GROUP BY u.user_id, u.user_email
ORDER BY u.user_id;

-- 3) Group admin bridge accounts April workout counts
SELECT
  ga.group_admin_id,
  ga.group_admin_email,
  COALESCE(u.user_id, 0) AS bridged_user_id,
  COUNT(w.workout_id) AS april_workouts
FROM group_admin ga
LEFT JOIN app_user u ON u.user_email = ga.group_admin_email
LEFT JOIN workout w
  ON w.user_id = u.user_id
 AND w.workout_date BETWEEN '2026-04-01' AND '2026-04-30'
GROUP BY ga.group_admin_id, ga.group_admin_email, u.user_id
ORDER BY ga.group_admin_id;

-- 4) Quick totals for April schedule/challenge objects
SELECT
  COUNT(*) AS april_group_workouts
FROM group_workout
WHERE group_workout_scheduled_date BETWEEN '2026-04-01' AND '2026-04-30';

SELECT
  COUNT(*) AS april_challenges
FROM challenge
WHERE COALESCE(challenge_start_date, challenge_date) <= '2026-04-30'
  AND COALESCE(challenge_end_date, challenge_date) >= '2026-04-01';

-- If validation looks good:
-- COMMIT;
-- If anything looks off:
-- ROLLBACK;
