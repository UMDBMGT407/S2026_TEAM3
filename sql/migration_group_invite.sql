-- Run once on existing motivdata databases (after motivdata_schema.sql) to enable group invites.
-- Group admins invite app users; invites appear on User/NU.html until accepted or rejected.

USE motivdata;

CREATE TABLE IF NOT EXISTS group_invite (
  invite_id INT AUTO_INCREMENT PRIMARY KEY,
  group_id INT NOT NULL,
  invited_user_id INT NOT NULL,
  invited_by_group_admin_id INT NOT NULL,
  invite_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  invite_status VARCHAR(32) NOT NULL DEFAULT 'pending',
  CONSTRAINT fk_gi_group FOREIGN KEY (group_id) REFERENCES motiv_group (group_id) ON DELETE CASCADE,
  CONSTRAINT fk_gi_user FOREIGN KEY (invited_user_id) REFERENCES app_user (user_id) ON DELETE CASCADE,
  CONSTRAINT fk_gi_ga FOREIGN KEY (invited_by_group_admin_id) REFERENCES group_admin (group_admin_id),
  UNIQUE KEY uq_group_invite_user (group_id, invited_user_id)
);
