-- Optional link from a personal workout log to one challenge (counts toward that challenge when dates align).
-- Safe to re-run: skips steps that already exist (avoids Error 1060 / duplicate FK).

USE motivdata;

SET @col_exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'workout'
    AND COLUMN_NAME = 'challenge_id'
);

SET @sql_add_col := IF(
  @col_exists = 0,
  'ALTER TABLE workout ADD COLUMN challenge_id INT NULL AFTER group_workout_id',
  'SELECT 1 AS workout_challenge_id_column_already_present'
);
PREPARE stmt_col FROM @sql_add_col;
EXECUTE stmt_col;
DEALLOCATE PREPARE stmt_col;

SET @fk_exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE CONSTRAINT_SCHEMA = DATABASE()
    AND TABLE_NAME = 'workout'
    AND CONSTRAINT_NAME = 'fk_workout_challenge'
    AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);

SET @sql_add_fk := IF(
  @fk_exists = 0,
  'ALTER TABLE workout ADD CONSTRAINT fk_workout_challenge FOREIGN KEY (challenge_id) REFERENCES challenge (challenge_id) ON DELETE SET NULL',
  'SELECT 1 AS workout_challenge_fk_already_present'
);
PREPARE stmt_fk FROM @sql_add_fk;
EXECUTE stmt_fk;
DEALLOCATE PREPARE stmt_fk;
