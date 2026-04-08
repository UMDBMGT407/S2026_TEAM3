-- Run once in MySQL Workbench when you want to undo "create group → become group admin"
-- for accounts that were promoted from app_user.
--
-- Affected rows: group_admin rows whose email matches an app_user with is_active = 0
-- (the promotion flow deactivates the user row and creates a GA with the same email).
-- Seed/demo group admins (e.g. ga@motiv.test) are NOT matched and are left as-is.
--
-- This deletes groups owned by those GAs (and related challenges, group workouts, user_group
-- via CASCADE on motiv_group delete for user_group). Workouts linked to those group_workouts
-- get group_workout_id set to NULL first.

USE motivdata;

CREATE TEMPORARY TABLE tmp_revert_ga (
  group_admin_id INT NOT NULL PRIMARY KEY,
  user_email VARCHAR(255) NOT NULL
);

INSERT INTO tmp_revert_ga (group_admin_id, user_email)
SELECT ga.group_admin_id, ga.group_admin_email
FROM group_admin ga
INNER JOIN app_user u ON u.user_email = ga.group_admin_email AND u.is_active = 0;

-- Detach user workouts from group sessions we are about to remove
UPDATE workout w
INNER JOIN group_workout gw ON w.group_workout_id = gw.group_workout_id
LEFT JOIN motiv_group g ON gw.group_id = g.group_id
INNER JOIN tmp_revert_ga t ON (
  (g.group_admin_id IS NOT NULL AND g.group_admin_id = t.group_admin_id)
  OR gw.group_admin_id = t.group_admin_id
)
SET w.group_workout_id = NULL;

DELETE gw FROM group_workout gw
LEFT JOIN motiv_group g ON gw.group_id = g.group_id
INNER JOIN tmp_revert_ga t ON (
  (g.group_admin_id IS NOT NULL AND g.group_admin_id = t.group_admin_id)
  OR gw.group_admin_id = t.group_admin_id
);

DELETE c FROM challenge c
INNER JOIN motiv_group g ON c.group_id = g.group_id
INNER JOIN tmp_revert_ga t ON g.group_admin_id = t.group_admin_id;

DELETE c FROM challenge c
INNER JOIN tmp_revert_ga t ON c.group_admin_id = t.group_admin_id;

DELETE g FROM motiv_group g
INNER JOIN tmp_revert_ga t ON g.group_admin_id = t.group_admin_id;

DELETE ga FROM group_admin ga
INNER JOIN tmp_revert_ga t ON ga.group_admin_id = t.group_admin_id;

UPDATE app_user u
INNER JOIN tmp_revert_ga t ON u.user_email = t.user_email
SET u.is_active = 1;

DROP TEMPORARY TABLE tmp_revert_ga;
