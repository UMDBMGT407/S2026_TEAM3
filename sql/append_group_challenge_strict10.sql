-- Append-only strict-10 membership extension
-- Run after: sql/append_april_bulk_seed.sql
-- Purpose:
--   1) Ensure each group has at least 10 active app_user members.
--   2) Ensure each challenge has at least 10 eligible participants derived from its group.
--      (Eligibility = active group members excluding challenge_participant_exclusion and user_challenge_leave)
--   3) Provide validation queries including deterministic top-10 eligible lists per challenge.

USE motivdata;
SET NAMES utf8mb4;
START TRANSACTION;

DROP PROCEDURE IF EXISTS sp_append_group_challenge_strict10;
DELIMITER $$
CREATE PROCEDURE sp_append_group_challenge_strict10()
BEGIN
  DECLARE v_group_count INT DEFAULT 0;
  DECLARE v_challenge_count INT DEFAULT 0;
  DECLARE v_gid INT DEFAULT NULL;
  DECLARE v_cid INT DEFAULT NULL;
  DECLARE v_need INT DEFAULT 0;
  DECLARE v_eligible_count INT DEFAULT 0;
  DECLARE v_created_uid INT DEFAULT NULL;
  DECLARE v_fill_idx INT DEFAULT 0;
  DECLARE v_loop_guard INT DEFAULT 0;
  DECLARE v_pw VARCHAR(512);
  DECLARE v_run_tag VARCHAR(32);

  DECLARE done_groups INT DEFAULT 0;
  DECLARE done_challenges INT DEFAULT 0;

  DECLARE cur_groups CURSOR FOR
    SELECT g.group_id
    FROM motiv_group g
    ORDER BY g.group_id;

  DECLARE cur_challenges CURSOR FOR
    SELECT c.challenge_id
    FROM challenge c
    ORDER BY c.challenge_id;

  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done_groups = 1;

  SET v_run_tag = DATE_FORMAT(NOW(), '%Y%m%d%H%i%s');
  SET v_pw = (
    SELECT password_hash
    FROM app_user
    ORDER BY user_id
    LIMIT 1
  );
  IF v_pw IS NULL OR v_pw = '' THEN
    SET v_pw = 'scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70';
  END IF;

  SELECT COUNT(*) INTO v_group_count FROM motiv_group;
  SELECT COUNT(*) INTO v_challenge_count FROM challenge;
  IF v_group_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No groups found; cannot apply strict-10 membership.';
  END IF;
  IF v_challenge_count = 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No challenges found; cannot apply strict-10 challenge eligibility.';
  END IF;

  -- Step 1: ensure each group has at least 10 active users.
  OPEN cur_groups;
  group_loop: LOOP
    FETCH cur_groups INTO v_gid;
    IF done_groups = 1 THEN
      LEAVE group_loop;
    END IF;

    SELECT GREATEST(10 - COUNT(DISTINCT ug.user_id), 0)
      INTO v_need
    FROM user_group ug
    JOIN app_user u ON u.user_id = ug.user_id
    WHERE ug.group_id = v_gid
      AND u.is_active = 1;

    SET v_fill_idx = 1;
    WHILE v_fill_idx <= v_need DO
      INSERT INTO app_user (user_name, user_first_name, user_last_name, user_email, password_hash, is_active)
      VALUES (
        CONCAT('grpfill_', v_gid, '_', v_run_tag, '_', LPAD(v_fill_idx, 2, '0')),
        'Group',
        CONCAT('Fill', v_gid),
        CONCAT('grpfill+', v_gid, '_', v_run_tag, '_', LPAD(v_fill_idx, 2, '0'), '@motiv.test'),
        v_pw,
        1
      );
      SET v_created_uid = LAST_INSERT_ID();
      INSERT IGNORE INTO user_group (user_id, group_id) VALUES (v_created_uid, v_gid);
      SET v_fill_idx = v_fill_idx + 1;
    END WHILE;
  END LOOP;
  CLOSE cur_groups;

  -- Step 2: ensure each challenge has at least 10 eligible users.
  -- Reuse NOT FOUND handler by resetting and toggling done flag manually.
  SET done_groups = 0;
  SET done_challenges = 0;

  OPEN cur_challenges;
  challenge_loop: LOOP
    FETCH cur_challenges INTO v_cid;
    IF done_groups = 1 THEN
      LEAVE challenge_loop;
    END IF;

    SELECT c.group_id INTO v_gid
    FROM challenge c
    WHERE c.challenge_id = v_cid
    LIMIT 1;

    SELECT COUNT(DISTINCT ug.user_id)
      INTO v_eligible_count
    FROM user_group ug
    JOIN app_user u ON u.user_id = ug.user_id AND u.is_active = 1
    LEFT JOIN challenge_participant_exclusion cpe
      ON cpe.challenge_id = v_cid AND cpe.user_id = ug.user_id
    LEFT JOIN user_challenge_leave ucl
      ON ucl.challenge_id = v_cid AND ucl.user_id = ug.user_id
    WHERE ug.group_id = v_gid
      AND cpe.user_id IS NULL
      AND ucl.user_id IS NULL;

    SET v_loop_guard = 0;
    WHILE v_eligible_count < 10 AND v_loop_guard < 20 DO
      SET v_loop_guard = v_loop_guard + 1;

      INSERT INTO app_user (user_name, user_first_name, user_last_name, user_email, password_hash, is_active)
      VALUES (
        CONCAT('chfill_', v_cid, '_', v_run_tag, '_', LPAD(v_loop_guard, 2, '0')),
        'Challenge',
        CONCAT('Fill', v_cid),
        CONCAT('chfill+', v_cid, '_', v_run_tag, '_', LPAD(v_loop_guard, 2, '0'), '@motiv.test'),
        v_pw,
        1
      );
      SET v_created_uid = LAST_INSERT_ID();
      INSERT IGNORE INTO user_group (user_id, group_id) VALUES (v_created_uid, v_gid);

      SELECT COUNT(DISTINCT ug.user_id)
        INTO v_eligible_count
      FROM user_group ug
      JOIN app_user u ON u.user_id = ug.user_id AND u.is_active = 1
      LEFT JOIN challenge_participant_exclusion cpe
        ON cpe.challenge_id = v_cid AND cpe.user_id = ug.user_id
      LEFT JOIN user_challenge_leave ucl
        ON ucl.challenge_id = v_cid AND ucl.user_id = ug.user_id
      WHERE ug.group_id = v_gid
        AND cpe.user_id IS NULL
        AND ucl.user_id IS NULL;
    END WHILE;
  END LOOP;
  CLOSE cur_challenges;

  -- Deterministic top-10 eligible per challenge for reporting.
  DROP TEMPORARY TABLE IF EXISTS tmp_challenge_top10;
  CREATE TEMPORARY TABLE tmp_challenge_top10 AS
  SELECT x.challenge_id, x.user_id
  FROM (
    SELECT
      c.challenge_id,
      ug.user_id,
      ROW_NUMBER() OVER (PARTITION BY c.challenge_id ORDER BY ug.user_id) AS rn
    FROM challenge c
    JOIN user_group ug ON ug.group_id = c.group_id
    JOIN app_user u ON u.user_id = ug.user_id AND u.is_active = 1
    LEFT JOIN challenge_participant_exclusion cpe
      ON cpe.challenge_id = c.challenge_id AND cpe.user_id = ug.user_id
    LEFT JOIN user_challenge_leave ucl
      ON ucl.challenge_id = c.challenge_id AND ucl.user_id = ug.user_id
    WHERE cpe.user_id IS NULL
      AND ucl.user_id IS NULL
  ) x
  WHERE x.rn <= 10;
END $$
DELIMITER ;

CALL sp_append_group_challenge_strict10();
DROP PROCEDURE IF EXISTS sp_append_group_challenge_strict10;

-- Validation 1: active group members (target >= 10 per group)
SELECT
  g.group_id,
  g.group_name,
  COUNT(DISTINCT ug.user_id) AS active_members
FROM motiv_group g
LEFT JOIN user_group ug ON ug.group_id = g.group_id
LEFT JOIN app_user u ON u.user_id = ug.user_id AND u.is_active = 1
WHERE u.user_id IS NOT NULL
GROUP BY g.group_id, g.group_name
ORDER BY g.group_id;

-- Validation 2: eligible challenge participants and deterministic top-10 count
SELECT
  c.challenge_id,
  c.challenge_title,
  c.group_id,
  (
    SELECT COUNT(DISTINCT ug.user_id)
    FROM user_group ug
    JOIN app_user u ON u.user_id = ug.user_id AND u.is_active = 1
    LEFT JOIN challenge_participant_exclusion cpe
      ON cpe.challenge_id = c.challenge_id AND cpe.user_id = ug.user_id
    LEFT JOIN user_challenge_leave ucl
      ON ucl.challenge_id = c.challenge_id AND ucl.user_id = ug.user_id
    WHERE ug.group_id = c.group_id
      AND cpe.user_id IS NULL
      AND ucl.user_id IS NULL
  ) AS eligible_count,
  (
    SELECT COUNT(*)
    FROM tmp_challenge_top10 t
    WHERE t.challenge_id = c.challenge_id
  ) AS deterministic_top10_count
FROM challenge c
ORDER BY c.challenge_id;

-- Validation 3: synthetic users added by this extension
SELECT
  u.user_id,
  u.user_email,
  u.user_first_name,
  u.user_last_name
FROM app_user u
WHERE u.user_email LIKE 'grpfill+%@motiv.test'
   OR u.user_email LIKE 'chfill+%@motiv.test'
ORDER BY u.user_id DESC;

-- If validation looks correct:
-- COMMIT;
-- Otherwise:
-- ROLLBACK;

