-- Append-only leaderboard sync seed
-- Purpose:
--   1) Ensure every active account contributes to current-week leaderboard metrics.
--   2) Top off April 2026 workouts so each active account has 5-6 workouts.
--   3) Add workout_log rows for all inserted workouts.
--
-- Safe mode:
--   - No TRUNCATE / DELETE.
--   - Appends only missing workouts/logs needed for targets.

USE motivdata;
SET NAMES utf8mb4;
START TRANSACTION;

DROP PROCEDURE IF EXISTS sp_append_leaderboard_week_and_april_sync;
DELIMITER $$
CREATE PROCEDURE sp_append_leaderboard_week_and_april_sync()
BEGIN
  DECLARE v_user_count INT DEFAULT 0;
  DECLARE v_ex_count INT DEFAULT 0;
  DECLARE v_group_count INT DEFAULT 0;
  DECLARE v_challenge_count INT DEFAULT 0;

  DECLARE v_uid INT DEFAULT NULL;
  DECLARE v_wid INT DEFAULT NULL;
  DECLARE v_gid INT DEFAULT NULL;
  DECLARE v_chid INT DEFAULT NULL;
  DECLARE v_gwid INT DEFAULT NULL;
  DECLARE v_exid INT DEFAULT NULL;

  DECLARE v_cur_week INT DEFAULT 0;
  DECLARE v_cur_apr INT DEFAULT 0;
  DECLARE v_target_week INT DEFAULT 0;
  DECLARE v_target_apr INT DEFAULT 0;
  DECLARE v_add_week INT DEFAULT 0;
  DECLARE v_add_apr INT DEFAULT 0;
  DECLARE v_logs_per_workout INT DEFAULT 0;
  DECLARE v_sets INT DEFAULT 0;
  DECLARE v_reps INT DEFAULT 0;
  DECLARE v_duration INT DEFAULT 0;
  DECLARE v_ex_offset INT DEFAULT 0;
  DECLARE v_weight DECIMAL(10,2) DEFAULT 0.00;

  DECLARE v_week_start DATE;
  DECLARE v_week_next DATE;
  DECLARE v_wdate DATE;
  DECLARE v_apr_date DATE;

  DECLARE v_i INT DEFAULT 0;
  DECLARE v_k INT DEFAULT 0;

  DECLARE done_users INT DEFAULT 0;
  DECLARE cur_users CURSOR FOR
    SELECT user_id
    FROM app_user
    WHERE is_active = 1
    ORDER BY user_id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done_users = 1;

  -- Preflight
  SELECT COUNT(*) INTO v_user_count FROM app_user WHERE is_active = 1;
  SELECT COUNT(*) INTO v_ex_count FROM exercise;
  SELECT COUNT(*) INTO v_group_count FROM motiv_group;
  SELECT COUNT(*) INTO v_challenge_count FROM challenge;
  IF v_user_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: no active app_user rows.';
  END IF;
  IF v_ex_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: no exercise rows.';
  END IF;
  IF v_group_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: no groups available.';
  END IF;
  IF v_challenge_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Preflight failed: no challenges available.';
  END IF;

  SET v_week_start = DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY);
  SET v_week_next = DATE_ADD(v_week_start, INTERVAL 7 DAY);

  OPEN cur_users;
  user_loop: LOOP
    FETCH cur_users INTO v_uid;
    IF done_users = 1 THEN
      LEAVE user_loop;
    END IF;

    -- Current week target: 2 or 3 workouts per active account.
    SET v_target_week = 2 + MOD(v_uid, 2);
    SELECT COUNT(*) INTO v_cur_week
    FROM workout w
    WHERE w.user_id = v_uid
      AND w.workout_date >= v_week_start
      AND w.workout_date < v_week_next;
    SET v_add_week = GREATEST(v_target_week - v_cur_week, 0);

    SET v_i = 1;
    WHILE v_i <= v_add_week DO
      SET v_wdate = DATE_ADD(v_week_start, INTERVAL FLOOR(RAND() * 7) DAY);
      SET v_duration = 25 + FLOOR(RAND() * 41); -- 25..65

      SET v_gid = NULL;
      SET v_chid = NULL;
      SET v_gwid = NULL;

      SELECT ug.group_id INTO v_gid
      FROM user_group ug
      WHERE ug.user_id = v_uid
      ORDER BY ug.group_id
      LIMIT 1;

      IF v_gid IS NOT NULL THEN
        SELECT c.challenge_id INTO v_chid
        FROM challenge c
        WHERE c.group_id = v_gid
          AND COALESCE(c.challenge_start_date, '1900-01-01') <= v_wdate
          AND COALESCE(c.challenge_end_date, '2999-12-31') >= v_wdate
        ORDER BY c.challenge_id DESC
        LIMIT 1;

        SELECT gw.group_workout_id INTO v_gwid
        FROM group_workout gw
        WHERE gw.group_id = v_gid
          AND gw.group_workout_scheduled_date = v_wdate
        ORDER BY gw.group_workout_id DESC
        LIMIT 1;
      END IF;

      INSERT INTO workout (
        workout_date, workout_duration_minutes, user_id, group_workout_id, challenge_id
      ) VALUES (
        v_wdate, v_duration, v_uid, v_gwid, v_chid
      );
      SET v_wid = LAST_INSERT_ID();

      SET v_logs_per_workout = 2 + FLOOR(RAND() * 2); -- 2..3 logs
      SET v_k = 1;
      WHILE v_k <= v_logs_per_workout DO
        SET v_ex_offset = FLOOR(RAND() * v_ex_count);
        SELECT e.exercise_id INTO v_exid
        FROM exercise e
        ORDER BY e.exercise_id
        LIMIT 1 OFFSET v_ex_offset;
        IF v_exid IS NULL THEN
          SELECT exercise_id INTO v_exid FROM exercise ORDER BY exercise_id LIMIT 1;
        END IF;

        SET v_sets = 2 + FLOOR(RAND() * 4); -- 2..5
        SET v_reps = 6 + FLOOR(RAND() * 13); -- 6..18
        SET v_weight = ROUND(5 + RAND() * 145, 2);
        INSERT INTO workout_log (
          workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id
        ) VALUES (
          v_sets, v_reps, v_weight, v_wid, v_exid
        );
        SET v_k = v_k + 1;
      END WHILE;

      SET v_i = v_i + 1;
    END WHILE;

    -- April 2026 target: 5 or 6 workouts per active account.
    SET v_target_apr = 5 + MOD(v_uid, 2);
    SELECT COUNT(*) INTO v_cur_apr
    FROM workout w
    WHERE w.user_id = v_uid
      AND w.workout_date BETWEEN '2026-04-01' AND '2026-04-30';
    SET v_add_apr = GREATEST(v_target_apr - v_cur_apr, 0);

    SET v_i = 1;
    WHILE v_i <= v_add_apr DO
      SET v_apr_date = DATE_ADD('2026-04-01', INTERVAL FLOOR(RAND() * 30) DAY);
      SET v_duration = 30 + FLOOR(RAND() * 51); -- 30..80

      SET v_gid = NULL;
      SET v_chid = NULL;
      SET v_gwid = NULL;

      SELECT ug.group_id INTO v_gid
      FROM user_group ug
      WHERE ug.user_id = v_uid
      ORDER BY ug.group_id
      LIMIT 1;

      IF v_gid IS NOT NULL THEN
        SELECT c.challenge_id INTO v_chid
        FROM challenge c
        WHERE c.group_id = v_gid
          AND COALESCE(c.challenge_start_date, '1900-01-01') <= v_apr_date
          AND COALESCE(c.challenge_end_date, '2999-12-31') >= v_apr_date
        ORDER BY c.challenge_id DESC
        LIMIT 1;

        SELECT gw.group_workout_id INTO v_gwid
        FROM group_workout gw
        WHERE gw.group_id = v_gid
          AND gw.group_workout_scheduled_date = v_apr_date
        ORDER BY gw.group_workout_id DESC
        LIMIT 1;
      END IF;

      INSERT INTO workout (
        workout_date, workout_duration_minutes, user_id, group_workout_id, challenge_id
      ) VALUES (
        v_apr_date, v_duration, v_uid, v_gwid, v_chid
      );
      SET v_wid = LAST_INSERT_ID();

      SET v_logs_per_workout = 2 + FLOOR(RAND() * 2); -- 2..3 logs
      SET v_k = 1;
      WHILE v_k <= v_logs_per_workout DO
        SET v_ex_offset = FLOOR(RAND() * v_ex_count);
        SELECT e.exercise_id INTO v_exid
        FROM exercise e
        ORDER BY e.exercise_id
        LIMIT 1 OFFSET v_ex_offset;
        IF v_exid IS NULL THEN
          SELECT exercise_id INTO v_exid FROM exercise ORDER BY exercise_id LIMIT 1;
        END IF;

        SET v_sets = 2 + FLOOR(RAND() * 4); -- 2..5
        SET v_reps = 6 + FLOOR(RAND() * 13); -- 6..18
        SET v_weight = ROUND(5 + RAND() * 145, 2);
        INSERT INTO workout_log (
          workout_num_sets, workout_num_reps, workout_num_weight, workout_id, exercise_id
        ) VALUES (
          v_sets, v_reps, v_weight, v_wid, v_exid
        );
        SET v_k = v_k + 1;
      END WHILE;

      SET v_i = v_i + 1;
    END WHILE;
  END LOOP;
  CLOSE cur_users;

  -- Quick summary counts
  SELECT
    (SELECT COUNT(*) FROM app_user WHERE is_active = 1) AS active_users,
    (SELECT COUNT(*) FROM workout
      WHERE workout_date >= v_week_start AND workout_date < v_week_next) AS workouts_current_week_total,
    (SELECT COUNT(*) FROM workout
      WHERE workout_date BETWEEN '2026-04-01' AND '2026-04-30') AS workouts_april_2026_total;
END $$
DELIMITER ;

CALL sp_append_leaderboard_week_and_april_sync();
DROP PROCEDURE IF EXISTS sp_append_leaderboard_week_and_april_sync;

-- Validation 1: Current-week workouts per active user (leaderboard-critical)
SELECT
  u.user_id,
  u.user_email,
  COUNT(w.workout_id) AS workouts_this_week
FROM app_user u
LEFT JOIN workout w
  ON w.user_id = u.user_id
 AND w.workout_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
 AND w.workout_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY)
WHERE u.is_active = 1
GROUP BY u.user_id, u.user_email
ORDER BY workouts_this_week ASC, u.user_id;

-- Validation 2: April 2026 workouts per active user (target 5-6)
SELECT
  u.user_id,
  u.user_email,
  COUNT(w.workout_id) AS workouts_april_2026
FROM app_user u
LEFT JOIN workout w
  ON w.user_id = u.user_id
 AND w.workout_date BETWEEN '2026-04-01' AND '2026-04-30'
WHERE u.is_active = 1
GROUP BY u.user_id, u.user_email
ORDER BY workouts_april_2026 ASC, u.user_id;

-- Validation 3: Distinct users represented in current-week leaderboard source
SELECT
  COUNT(DISTINCT w.user_id) AS distinct_users_with_current_week_workouts
FROM workout w
JOIN app_user u ON u.user_id = w.user_id
WHERE u.is_active = 1
  AND w.workout_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)
  AND w.workout_date < DATE_ADD(DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), INTERVAL 7 DAY);

-- If results look correct:
-- COMMIT;
-- Otherwise:
-- ROLLBACK;

