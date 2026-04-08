CREATE DATABASE  IF NOT EXISTS `motivdata` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `motivdata`;
-- MySQL dump 10.13  Distrib 8.0.45, for macos15 (arm64)
--
-- Host: localhost    Database: motivdata
-- ------------------------------------------------------
-- Server version	9.6.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '021e6b4c-296b-11f1-b5e2-fdd32a594137:1-95';

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `admin_id` int NOT NULL AUTO_INCREMENT,
  `admin_name` varchar(255) DEFAULT NULL,
  `admin_first_name` varchar(255) NOT NULL,
  `admin_last_name` varchar(255) NOT NULL,
  `admin_email` varchar(255) NOT NULL,
  `password_hash` varchar(512) NOT NULL,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `admin_email` (`admin_email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1,'Alex Rivera','Alex','Rivera','admin@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(2,'Admin Two','Sam','Chen','admin2@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70');
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `app_user`
--

DROP TABLE IF EXISTS `app_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `app_user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `user_name` varchar(255) DEFAULT NULL,
  `user_first_name` varchar(255) NOT NULL,
  `user_last_name` varchar(255) NOT NULL,
  `user_email` varchar(255) NOT NULL,
  `password_hash` varchar(512) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '0 = promoted to group_admin; row kept for FK to posts/workouts/user_group',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `user_email` (`user_email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `app_user`
--

LOCK TABLES `app_user` WRITE;
/*!40000 ALTER TABLE `app_user` DISABLE KEYS */;
INSERT INTO `app_user` VALUES (1,'jdoe','John','Doe','john@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',0),(2,'jsmith','Jane','Smith','jane@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(3,'Bob Kim','Bob','Kim','bob@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',0),(4,'Tyler Deitzel','Tyler','Deitzel','tdeitzel4@icloud.com','scrypt:32768:8:1$BZ4rnGl3ubRx8e8N$89cccc66b017c1309cfd97973979ee7b601537779271a977daed4122427f8e105a1cc89811d83c7cf63a01220dd89d6d6180e9a24fa77291f938c4406f3ad179',1),(5,'Jordan Lee','Jordan','Lee','ga@motiv.test','scrypt:32768:8:1$8YRzlyheAGjsKxeM$bc133cdb153f2c447fc7900ebc7a381fee477f4c4416e1777791eb3f69d31702fbe90fb9f752e4200cd05b63ab2ed91c0b67be6da68729e0d81e84cb6b0093e3',1);
/*!40000 ALTER TABLE `app_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `challenge`
--

DROP TABLE IF EXISTS `challenge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challenge` (
  `challenge_id` int NOT NULL AUTO_INCREMENT,
  `challenge_title` varchar(255) NOT NULL,
  `challenge_date` date DEFAULT NULL,
  `challenge_start_date` date DEFAULT NULL,
  `challenge_end_date` date DEFAULT NULL,
  `challenge_status` varchar(64) DEFAULT NULL,
  `challenge_goal` text,
  `group_admin_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`challenge_id`),
  KEY `fk_challenge_ga` (`group_admin_id`),
  KEY `fk_challenge_group` (`group_id`),
  CONSTRAINT `fk_challenge_ga` FOREIGN KEY (`group_admin_id`) REFERENCES `group_admin` (`group_admin_id`),
  CONSTRAINT `fk_challenge_group` FOREIGN KEY (`group_id`) REFERENCES `motiv_group` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `challenge`
--

LOCK TABLES `challenge` WRITE;
/*!40000 ALTER TABLE `challenge` DISABLE KEYS */;
INSERT INTO `challenge` VALUES (1,'Summer Prep','2026-03-01','2026-05-01','2026-05-31','active','10 workouts',1,2),(2,'April Strength','2026-04-01','2026-04-01','2026-04-30','active','12 workouts this month',1,2),(3,'Test','2026-04-08','2026-04-16','2026-04-23','active','5 workouts',1,1);
/*!40000 ALTER TABLE `challenge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exercise`
--

DROP TABLE IF EXISTS `exercise`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exercise` (
  `exercise_id` int NOT NULL AUTO_INCREMENT,
  `exercise_name` varchar(255) NOT NULL,
  `exercise_muscle_group` varchar(128) DEFAULT NULL,
  `exercise_difficulty_level` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`exercise_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exercise`
--

LOCK TABLES `exercise` WRITE;
/*!40000 ALTER TABLE `exercise` DISABLE KEYS */;
INSERT INTO `exercise` VALUES (1,'Back Squat','Legs','intermediate'),(2,'Bench Press','Chest','intermediate'),(3,'Sit-ups','Abs','beginner'),(4,'Deadlift','Back','advanced'),(5,'Treadmill Run','Cardio','beginner');
/*!40000 ALTER TABLE `exercise` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_admin`
--

DROP TABLE IF EXISTS `group_admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_admin` (
  `group_admin_id` int NOT NULL AUTO_INCREMENT,
  `group_admin_name` varchar(255) DEFAULT NULL,
  `group_admin_first_name` varchar(255) NOT NULL,
  `group_admin_last_name` varchar(255) NOT NULL,
  `group_admin_email` varchar(255) NOT NULL,
  `password_hash` varchar(512) NOT NULL,
  PRIMARY KEY (`group_admin_id`),
  UNIQUE KEY `group_admin_email` (`group_admin_email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_admin`
--

LOCK TABLES `group_admin` WRITE;
/*!40000 ALTER TABLE `group_admin` DISABLE KEYS */;
INSERT INTO `group_admin` VALUES (1,'GA Jordan','Jordan','Lee','ga@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(2,'GA Morgan','Morgan','Patel','ga2@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(3,'John Doe','John','Doe','john@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(4,'Bob Kim','Bob','Kim','bob@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70');
/*!40000 ALTER TABLE `group_admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_workout`
--

DROP TABLE IF EXISTS `group_workout`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_workout` (
  `group_workout_id` int NOT NULL AUTO_INCREMENT,
  `group_workout_title` varchar(255) NOT NULL,
  `group_workout_description` text,
  `group_workout_scheduled_date` date DEFAULT NULL,
  `group_workout_start_date` date DEFAULT NULL,
  `group_workout_end_date` date DEFAULT NULL,
  `group_workout_location` varchar(255) DEFAULT NULL,
  `group_id` int NOT NULL,
  `group_admin_id` int NOT NULL,
  PRIMARY KEY (`group_workout_id`),
  KEY `fk_gw_group` (`group_id`),
  KEY `fk_gw_ga` (`group_admin_id`),
  CONSTRAINT `fk_gw_ga` FOREIGN KEY (`group_admin_id`) REFERENCES `group_admin` (`group_admin_id`),
  CONSTRAINT `fk_gw_group` FOREIGN KEY (`group_id`) REFERENCES `motiv_group` (`group_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_workout`
--

LOCK TABLES `group_workout` WRITE;
/*!40000 ALTER TABLE `group_workout` DISABLE KEYS */;
INSERT INTO `group_workout` VALUES (1,'Leg Day','Squats and accessories','2026-04-07','2026-04-07','2026-04-07','Eppley Rec Center',1,1),(2,'School Run','5K easy pace','2026-04-09','2026-04-09','2026-04-09','South Campus',2,1),(3,'Morning run','Vinyasa flow','2026-04-09','2026-04-09','2026-04-09','Studio a',3,2),(4,'Test123',NULL,'2026-04-16','2026-04-16','2026-04-16','UMD South',1,1);
/*!40000 ALTER TABLE `group_workout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `motiv_group`
--

DROP TABLE IF EXISTS `motiv_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `motiv_group` (
  `group_id` int NOT NULL AUTO_INCREMENT,
  `group_name` varchar(255) NOT NULL,
  `group_description` text,
  `group_date_created` date NOT NULL,
  `admin_id` int NOT NULL,
  `group_admin_id` int NOT NULL,
  PRIMARY KEY (`group_id`),
  KEY `fk_group_admin` (`admin_id`),
  KEY `fk_group_group_admin` (`group_admin_id`),
  CONSTRAINT `fk_group_admin` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`admin_id`),
  CONSTRAINT `fk_group_group_admin` FOREIGN KEY (`group_admin_id`) REFERENCES `group_admin` (`group_admin_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `motiv_group`
--

LOCK TABLES `motiv_group` WRITE;
/*!40000 ALTER TABLE `motiv_group` DISABLE KEYS */;
INSERT INTO `motiv_group` VALUES (1,'Morning lifters','good workouts','2026-01-15',1,1),(2,'Campus Runners','Track and trail runs','2026-02-01',1,1),(3,'Big Workout','Fun','2026-02-10',2,2),(4,'x','x','2026-04-07',1,3),(5,'test','test','2026-04-07',1,4);
/*!40000 ALTER TABLE `motiv_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `post`
--

DROP TABLE IF EXISTS `post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `post` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `post_content` text,
  `post_created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `post_time` time DEFAULT NULL,
  `post_date` date DEFAULT NULL,
  `admin_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`post_id`),
  KEY `fk_post_admin` (`admin_id`),
  KEY `fk_post_user` (`user_id`),
  CONSTRAINT `fk_post_admin` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`admin_id`),
  CONSTRAINT `fk_post_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `post`
--

LOCK TABLES `post` WRITE;
/*!40000 ALTER TABLE `post` DISABLE KEYS */;
INSERT INTO `post` VALUES (2,'Hit a new PR on squat','2026-04-07 19:27:26','18:00:00','2026-04-02',NULL,2),(5,'TEST GA','2026-04-08 11:44:26','11:44:26','2026-04-08',NULL,5),(6,'I\'m Bob!','2026-04-08 11:56:38','11:56:38','2026-04-08',NULL,3),(7,'Test','2026-04-08 12:16:54','12:16:54','2026-04-08',NULL,4);
/*!40000 ALTER TABLE `post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_group`
--

DROP TABLE IF EXISTS `user_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_group` (
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`user_id`,`group_id`),
  KEY `fk_ug_group` (`group_id`),
  CONSTRAINT `fk_ug_group` FOREIGN KEY (`group_id`) REFERENCES `motiv_group` (`group_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ug_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_group`
--

LOCK TABLES `user_group` WRITE;
/*!40000 ALTER TABLE `user_group` DISABLE KEYS */;
INSERT INTO `user_group` VALUES (1,1),(2,1),(1,2),(3,2),(3,3);
/*!40000 ALTER TABLE `user_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout`
--

DROP TABLE IF EXISTS `workout`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout` (
  `workout_id` int NOT NULL AUTO_INCREMENT,
  `workout_date` date NOT NULL,
  `workout_duration_minutes` int DEFAULT NULL COMMENT 'Duration stored in minutes',
  `user_id` int NOT NULL,
  `group_workout_id` int DEFAULT NULL,
  PRIMARY KEY (`workout_id`),
  KEY `fk_workout_user` (`user_id`),
  KEY `fk_workout_gw` (`group_workout_id`),
  CONSTRAINT `fk_workout_gw` FOREIGN KEY (`group_workout_id`) REFERENCES `group_workout` (`group_workout_id`),
  CONSTRAINT `fk_workout_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout`
--

LOCK TABLES `workout` WRITE;
/*!40000 ALTER TABLE `workout` DISABLE KEYS */;
INSERT INTO `workout` VALUES (1,'2026-03-27',40,1,1),(2,'2026-03-27',36,1,NULL),(3,'2026-03-26',25,2,NULL),(4,'2026-03-25',15,3,2),(5,'2026-04-15',30,2,NULL),(6,'2026-04-07',30,2,NULL),(7,'2026-04-07',30,2,NULL),(8,'2026-04-07',30,2,NULL),(9,'2026-04-07',30,2,NULL);
/*!40000 ALTER TABLE `workout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workout_log`
--

DROP TABLE IF EXISTS `workout_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workout_log` (
  `workout_log_id` int NOT NULL AUTO_INCREMENT,
  `workout_num_sets` int DEFAULT NULL,
  `workout_num_reps` int DEFAULT NULL,
  `workout_num_weight` decimal(10,2) DEFAULT NULL,
  `workout_id` int NOT NULL,
  `exercise_id` int NOT NULL,
  PRIMARY KEY (`workout_log_id`),
  KEY `fk_wl_workout` (`workout_id`),
  KEY `fk_wl_exercise` (`exercise_id`),
  CONSTRAINT `fk_wl_exercise` FOREIGN KEY (`exercise_id`) REFERENCES `exercise` (`exercise_id`),
  CONSTRAINT `fk_wl_workout` FOREIGN KEY (`workout_id`) REFERENCES `workout` (`workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_log`
--

LOCK TABLES `workout_log` WRITE;
/*!40000 ALTER TABLE `workout_log` DISABLE KEYS */;
INSERT INTO `workout_log` VALUES (1,3,10,135.00,1,1),(2,4,8,185.00,1,2),(3,3,20,0.00,2,3),(4,5,5,225.00,3,4),(5,3,10,5.00,5,3),(6,3,10,5.00,6,3),(7,3,10,5.00,7,3),(8,3,10,5.00,8,3),(9,3,10,5.00,9,3);
/*!40000 ALTER TABLE `workout_log` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-08 16:22:50
