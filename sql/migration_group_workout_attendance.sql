-- Run once on existing motivdata databases to support RSVP attendance statuses.

USE motivdata;

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
