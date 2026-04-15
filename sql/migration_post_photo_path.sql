-- Run once on existing motivdata databases to support uploaded post photos.

USE motivdata;

ALTER TABLE post
  ADD COLUMN post_photo_path VARCHAR(255) NULL
  AFTER post_content;
