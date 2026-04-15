CREATE TABLE IF NOT EXISTS challenge_participant_exclusion (
  exclusion_id INT AUTO_INCREMENT PRIMARY KEY,
  challenge_id INT NOT NULL,
  user_id INT NOT NULL,
  removed_by_admin_id INT NOT NULL,
  removed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cpe_challenge FOREIGN KEY (challenge_id)
    REFERENCES challenge (challenge_id) ON DELETE CASCADE,
  CONSTRAINT fk_cpe_user FOREIGN KEY (user_id)
    REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_cpe_admin FOREIGN KEY (removed_by_admin_id)
    REFERENCES admin (admin_id),
  UNIQUE KEY uq_cpe_challenge_user (challenge_id, user_id)
);
