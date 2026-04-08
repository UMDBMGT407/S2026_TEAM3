-- Run once in MySQL Workbench after motivdata_schema.sql (existing databases).
-- Promoted users are marked inactive so they log in as group_admin only.

USE motivdata;

ALTER TABLE app_user
  ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1
  COMMENT '0 = promoted to group_admin; row kept for FK to posts/workouts/user_group';
