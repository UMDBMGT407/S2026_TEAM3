-- Run once on existing motivdata databases to store optional session time on scheduled group workouts.

USE motivdata;

ALTER TABLE group_workout
  ADD COLUMN group_workout_scheduled_time TIME NULL
  AFTER group_workout_scheduled_date;
