-- User opted out of a challenge (stays in group; does not use admin exclusion table).
CREATE TABLE IF NOT EXISTS user_challenge_leave (
  leave_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  challenge_id INT NOT NULL,
  left_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_ucl_user FOREIGN KEY (user_id)
    REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_ucl_challenge FOREIGN KEY (challenge_id)
    REFERENCES challenge (challenge_id) ON DELETE CASCADE,
  UNIQUE KEY uq_ucl_user_challenge (user_id, challenge_id)
);
