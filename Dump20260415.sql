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

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '021e6b4c-296b-11f1-b5e2-fdd32a594137:1-420';

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
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1,'Admin One','Alex','Rivera','admin@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(2,'Admin Two','Sam','Chen','admin2@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(3,'Bulk Anchor Admin','Bulk','Anchor','bulk-anchor-admin@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70');
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
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `app_user`
--

LOCK TABLES `app_user` WRITE;
/*!40000 ALTER TABLE `app_user` DISABLE KEYS */;
INSERT INTO `app_user` VALUES (1,'jdoe','John','Doe','john@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(2,'jsmith','Jane','Smith','jane@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(3,'bobk','Bob','Kim','bob@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(4,'ga_bulk_0001','GA','Bulk01','ga-bulk+0001@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(5,'ga_bulk_0002','GA','Bulk02','ga-bulk+0002@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(6,'ga_bulk_0003','GA','Bulk03','ga-bulk+0003@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(7,'ga_bulk_0004','GA','Bulk04','ga-bulk+0004@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(8,'ga_bulk_0005','GA','Bulk05','ga-bulk+0005@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(9,'ga_bulk_0006','GA','Bulk06','ga-bulk+0006@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(10,'ga_bulk_0007','GA','Bulk07','ga-bulk+0007@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(11,'ga_bulk_0008','GA','Bulk08','ga-bulk+0008@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(12,'ga_bulk_0009','GA','Bulk09','ga-bulk+0009@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(13,'ga_bulk_0010','GA','Bulk10','ga-bulk+0010@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(14,'ga_bulk_0011','GA','Bulk11','ga-bulk+0011@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(15,'ga_bulk_0012','GA','Bulk12','ga-bulk+0012@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(16,'ga_bulk_0013','GA','Bulk13','ga-bulk+0013@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(17,'ga_bulk_0014','GA','Bulk14','ga-bulk+0014@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(18,'ga_bulk_0015','GA','Bulk15','ga-bulk+0015@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(19,'ga_bulk_0016','GA','Bulk16','ga-bulk+0016@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(20,'ga_bulk_0017','GA','Bulk17','ga-bulk+0017@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(21,'ga_bulk_0018','GA','Bulk18','ga-bulk+0018@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(22,'ga_bulk_0019','GA','Bulk19','ga-bulk+0019@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(23,'ga_bulk_0020','GA','Bulk20','ga-bulk+0020@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(24,'user_bulk_0001','User','Bulk0001','user-bulk+0001@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(25,'user_bulk_0002','User','Bulk0002','user-bulk+0002@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(26,'user_bulk_0003','User','Bulk0003','user-bulk+0003@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(27,'user_bulk_0004','User','Bulk0004','user-bulk+0004@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(28,'user_bulk_0005','User','Bulk0005','user-bulk+0005@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(29,'user_bulk_0006','User','Bulk0006','user-bulk+0006@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(30,'user_bulk_0007','User','Bulk0007','user-bulk+0007@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(31,'user_bulk_0008','User','Bulk0008','user-bulk+0008@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(32,'user_bulk_0009','User','Bulk0009','user-bulk+0009@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(33,'user_bulk_0010','User','Bulk0010','user-bulk+0010@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(34,'user_bulk_0011','User','Bulk0011','user-bulk+0011@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(35,'user_bulk_0012','User','Bulk0012','user-bulk+0012@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(36,'user_bulk_0013','User','Bulk0013','user-bulk+0013@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(37,'user_bulk_0014','User','Bulk0014','user-bulk+0014@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(38,'user_bulk_0015','User','Bulk0015','user-bulk+0015@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(39,'user_bulk_0016','User','Bulk0016','user-bulk+0016@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(40,'user_bulk_0017','User','Bulk0017','user-bulk+0017@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(41,'user_bulk_0018','User','Bulk0018','user-bulk+0018@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(42,'user_bulk_0019','User','Bulk0019','user-bulk+0019@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(43,'user_bulk_0020','User','Bulk0020','user-bulk+0020@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(44,'user_bulk_0021','User','Bulk0021','user-bulk+0021@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(45,'user_bulk_0022','User','Bulk0022','user-bulk+0022@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(46,'user_bulk_0023','User','Bulk0023','user-bulk+0023@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(47,'user_bulk_0024','User','Bulk0024','user-bulk+0024@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(48,'user_bulk_0025','User','Bulk0025','user-bulk+0025@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(49,'user_bulk_0026','User','Bulk0026','user-bulk+0026@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(50,'user_bulk_0027','User','Bulk0027','user-bulk+0027@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(51,'user_bulk_0028','User','Bulk0028','user-bulk+0028@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(52,'user_bulk_0029','User','Bulk0029','user-bulk+0029@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(53,'user_bulk_0030','User','Bulk0030','user-bulk+0030@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(54,'user_bulk_0031','User','Bulk0031','user-bulk+0031@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(55,'user_bulk_0032','User','Bulk0032','user-bulk+0032@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(56,'user_bulk_0033','User','Bulk0033','user-bulk+0033@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(57,'user_bulk_0034','User','Bulk0034','user-bulk+0034@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(58,'user_bulk_0035','User','Bulk0035','user-bulk+0035@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(59,'user_bulk_0036','User','Bulk0036','user-bulk+0036@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(60,'user_bulk_0037','User','Bulk0037','user-bulk+0037@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(61,'user_bulk_0038','User','Bulk0038','user-bulk+0038@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(62,'user_bulk_0039','User','Bulk0039','user-bulk+0039@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1),(63,'user_bulk_0040','User','Bulk0040','user-bulk+0040@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70',1);
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
) ENGINE=InnoDB AUTO_INCREMENT=103 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `challenge`
--

LOCK TABLES `challenge` WRITE;
/*!40000 ALTER TABLE `challenge` DISABLE KEYS */;
INSERT INTO `challenge` VALUES (1,'Spring Step Count','2026-03-01','2026-03-01','2026-03-31','active','Walk 10k steps daily',1,1),(2,'April Strength','2026-04-01','2026-04-01','2026-04-30','active','12 workouts this month',1,2),(3,'GA01 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 01 groups.',3,4),(4,'GA01 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 01 groups.',3,5),(5,'GA01 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 01 groups.',3,4),(6,'GA01 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 01 groups.',3,5),(7,'GA01 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 01 groups.',3,4),(8,'GA02 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 02 groups.',4,6),(9,'GA02 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 02 groups.',4,7),(10,'GA02 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 02 groups.',4,6),(11,'GA02 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 02 groups.',4,7),(12,'GA02 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 02 groups.',4,6),(13,'GA03 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 03 groups.',5,8),(14,'GA03 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 03 groups.',5,9),(15,'GA03 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 03 groups.',5,8),(16,'GA03 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 03 groups.',5,9),(17,'GA03 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 03 groups.',5,8),(18,'GA04 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 04 groups.',6,10),(19,'GA04 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 04 groups.',6,11),(20,'GA04 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 04 groups.',6,10),(21,'GA04 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 04 groups.',6,11),(22,'GA04 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 04 groups.',6,10),(23,'GA05 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 05 groups.',7,12),(24,'GA05 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 05 groups.',7,13),(25,'GA05 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 05 groups.',7,12),(26,'GA05 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 05 groups.',7,13),(27,'GA05 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 05 groups.',7,12),(28,'GA06 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 06 groups.',8,14),(29,'GA06 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 06 groups.',8,15),(30,'GA06 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 06 groups.',8,14),(31,'GA06 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 06 groups.',8,15),(32,'GA06 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 06 groups.',8,14),(33,'GA07 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 07 groups.',9,16),(34,'GA07 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 07 groups.',9,17),(35,'GA07 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 07 groups.',9,16),(36,'GA07 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 07 groups.',9,17),(37,'GA07 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 07 groups.',9,16),(38,'GA08 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 08 groups.',10,18),(39,'GA08 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 08 groups.',10,19),(40,'GA08 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 08 groups.',10,18),(41,'GA08 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 08 groups.',10,19),(42,'GA08 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 08 groups.',10,18),(43,'GA09 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 09 groups.',11,20),(44,'GA09 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 09 groups.',11,21),(45,'GA09 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 09 groups.',11,20),(46,'GA09 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 09 groups.',11,21),(47,'GA09 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 09 groups.',11,20),(48,'GA10 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 10 groups.',12,22),(49,'GA10 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 10 groups.',12,23),(50,'GA10 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 10 groups.',12,22),(51,'GA10 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 10 groups.',12,23),(52,'GA10 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 10 groups.',12,22),(53,'GA11 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 11 groups.',13,24),(54,'GA11 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 11 groups.',13,25),(55,'GA11 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 11 groups.',13,24),(56,'GA11 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 11 groups.',13,25),(57,'GA11 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 11 groups.',13,24),(58,'GA12 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 12 groups.',14,26),(59,'GA12 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 12 groups.',14,27),(60,'GA12 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 12 groups.',14,26),(61,'GA12 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 12 groups.',14,27),(62,'GA12 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 12 groups.',14,26),(63,'GA13 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 13 groups.',15,28),(64,'GA13 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 13 groups.',15,29),(65,'GA13 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 13 groups.',15,28),(66,'GA13 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 13 groups.',15,29),(67,'GA13 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 13 groups.',15,28),(68,'GA14 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 14 groups.',16,30),(69,'GA14 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 14 groups.',16,31),(70,'GA14 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 14 groups.',16,30),(71,'GA14 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 14 groups.',16,31),(72,'GA14 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 14 groups.',16,30),(73,'GA15 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 15 groups.',17,32),(74,'GA15 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 15 groups.',17,33),(75,'GA15 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 15 groups.',17,32),(76,'GA15 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 15 groups.',17,33),(77,'GA15 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 15 groups.',17,32),(78,'GA16 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 16 groups.',18,34),(79,'GA16 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 16 groups.',18,35),(80,'GA16 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 16 groups.',18,34),(81,'GA16 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 16 groups.',18,35),(82,'GA16 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 16 groups.',18,34),(83,'GA17 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 17 groups.',19,36),(84,'GA17 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 17 groups.',19,37),(85,'GA17 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 17 groups.',19,36),(86,'GA17 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 17 groups.',19,37),(87,'GA17 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 17 groups.',19,36),(88,'GA18 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 18 groups.',20,38),(89,'GA18 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 18 groups.',20,39),(90,'GA18 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 18 groups.',20,38),(91,'GA18 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 18 groups.',20,39),(92,'GA18 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 18 groups.',20,38),(93,'GA19 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 19 groups.',21,40),(94,'GA19 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 19 groups.',21,41),(95,'GA19 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 19 groups.',21,40),(96,'GA19 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 19 groups.',21,41),(97,'GA19 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 19 groups.',21,40),(98,'GA20 Challenge 1','2026-04-13','2026-04-13','2026-04-19','active','Complete challenge 1 goals for GA 20 groups.',22,42),(99,'GA20 Challenge 2','2026-04-20','2026-04-20','2026-04-26','active','Complete challenge 2 goals for GA 20 groups.',22,43),(100,'GA20 Challenge 3','2026-04-27','2026-04-27','2026-05-03','upcoming','Complete challenge 3 goals for GA 20 groups.',22,42),(101,'GA20 Challenge 4','2026-05-04','2026-05-04','2026-05-10','upcoming','Complete challenge 4 goals for GA 20 groups.',22,43),(102,'GA20 Challenge 5','2026-05-11','2026-05-11','2026-05-17','upcoming','Complete challenge 5 goals for GA 20 groups.',22,42);
/*!40000 ALTER TABLE `challenge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `challenge_participant_exclusion`
--

DROP TABLE IF EXISTS `challenge_participant_exclusion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `challenge_participant_exclusion` (
  `exclusion_id` int NOT NULL AUTO_INCREMENT,
  `challenge_id` int NOT NULL,
  `user_id` int NOT NULL,
  `removed_by_admin_id` int NOT NULL,
  `removed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`exclusion_id`),
  UNIQUE KEY `uq_cpe_challenge_user` (`challenge_id`,`user_id`),
  KEY `fk_cpe_user` (`user_id`),
  KEY `fk_cpe_admin` (`removed_by_admin_id`),
  CONSTRAINT `fk_cpe_admin` FOREIGN KEY (`removed_by_admin_id`) REFERENCES `admin` (`admin_id`),
  CONSTRAINT `fk_cpe_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenge` (`challenge_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_cpe_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `challenge_participant_exclusion`
--

LOCK TABLES `challenge_participant_exclusion` WRITE;
/*!40000 ALTER TABLE `challenge_participant_exclusion` DISABLE KEYS */;
/*!40000 ALTER TABLE `challenge_participant_exclusion` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_admin`
--

LOCK TABLES `group_admin` WRITE;
/*!40000 ALTER TABLE `group_admin` DISABLE KEYS */;
INSERT INTO `group_admin` VALUES (1,'GA Jordan','Jordan','Lee','ga@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(2,'GA Morgan','Morgan','Patel','ga2@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(3,'GA Bulk 01','GA','Bulk01','ga-bulk+0001@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(4,'GA Bulk 02','GA','Bulk02','ga-bulk+0002@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(5,'GA Bulk 03','GA','Bulk03','ga-bulk+0003@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(6,'GA Bulk 04','GA','Bulk04','ga-bulk+0004@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(7,'GA Bulk 05','GA','Bulk05','ga-bulk+0005@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(8,'GA Bulk 06','GA','Bulk06','ga-bulk+0006@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(9,'GA Bulk 07','GA','Bulk07','ga-bulk+0007@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(10,'GA Bulk 08','GA','Bulk08','ga-bulk+0008@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(11,'GA Bulk 09','GA','Bulk09','ga-bulk+0009@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(12,'GA Bulk 10','GA','Bulk10','ga-bulk+0010@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(13,'GA Bulk 11','GA','Bulk11','ga-bulk+0011@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(14,'GA Bulk 12','GA','Bulk12','ga-bulk+0012@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(15,'GA Bulk 13','GA','Bulk13','ga-bulk+0013@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(16,'GA Bulk 14','GA','Bulk14','ga-bulk+0014@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(17,'GA Bulk 15','GA','Bulk15','ga-bulk+0015@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(18,'GA Bulk 16','GA','Bulk16','ga-bulk+0016@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(19,'GA Bulk 17','GA','Bulk17','ga-bulk+0017@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(20,'GA Bulk 18','GA','Bulk18','ga-bulk+0018@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(21,'GA Bulk 19','GA','Bulk19','ga-bulk+0019@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70'),(22,'GA Bulk 20','GA','Bulk20','ga-bulk+0020@motiv.test','scrypt:32768:8:1$ytdxORmJta7mFCdr$56f13e1b0e42ca1de03143fe583815404d1702b5151a3e3c2fc8eb31610195c0480284d182f42a998edffde730c1c8d760a564de6476ff1dc98fe17ada890e70');
/*!40000 ALTER TABLE `group_admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_invite`
--

DROP TABLE IF EXISTS `group_invite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_invite` (
  `invite_id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `invited_user_id` int NOT NULL,
  `invited_by_group_admin_id` int NOT NULL,
  `invite_created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `invite_status` varchar(32) NOT NULL DEFAULT 'pending',
  PRIMARY KEY (`invite_id`),
  UNIQUE KEY `uq_group_invite_user` (`group_id`,`invited_user_id`),
  KEY `fk_gi_user` (`invited_user_id`),
  KEY `fk_gi_ga` (`invited_by_group_admin_id`),
  CONSTRAINT `fk_gi_ga` FOREIGN KEY (`invited_by_group_admin_id`) REFERENCES `group_admin` (`group_admin_id`),
  CONSTRAINT `fk_gi_group` FOREIGN KEY (`group_id`) REFERENCES `motiv_group` (`group_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_gi_user` FOREIGN KEY (`invited_user_id`) REFERENCES `app_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_invite`
--

LOCK TABLES `group_invite` WRITE;
/*!40000 ALTER TABLE `group_invite` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_invite` ENABLE KEYS */;
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
  `group_workout_scheduled_time` time DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=104 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_workout`
--

LOCK TABLES `group_workout` WRITE;
/*!40000 ALTER TABLE `group_workout` DISABLE KEYS */;
INSERT INTO `group_workout` VALUES (1,'Leg Day','Squats and accessories','2026-04-07',NULL,'2026-04-07','2026-04-07','Eppley Rec Center',1,1),(2,'Group Run','5K easy pace','2026-04-08',NULL,'2026-04-08','2026-04-08','Campus loop',2,1),(3,'Morning Yoga','Vinyasa flow','2026-04-09',NULL,'2026-04-09','2026-04-09','Studio B',3,2),(4,'GA01 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 01.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 01',4,3),(5,'GA01 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 01.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 01',5,3),(6,'GA01 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 01.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 01',4,3),(7,'GA01 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 01.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 01',5,3),(8,'GA01 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 01.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 01',4,3),(9,'GA02 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 02.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 02',6,4),(10,'GA02 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 02.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 02',7,4),(11,'GA02 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 02.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 02',6,4),(12,'GA02 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 02.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 02',7,4),(13,'GA02 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 02.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 02',6,4),(14,'GA03 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 03.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 03',8,5),(15,'GA03 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 03.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 03',9,5),(16,'GA03 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 03.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 03',8,5),(17,'GA03 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 03.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 03',9,5),(18,'GA03 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 03.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 03',8,5),(19,'GA04 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 04.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 04',10,6),(20,'GA04 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 04.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 04',11,6),(21,'GA04 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 04.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 04',10,6),(22,'GA04 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 04.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 04',11,6),(23,'GA04 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 04.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 04',10,6),(24,'GA05 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 05.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 05',12,7),(25,'GA05 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 05.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 05',13,7),(26,'GA05 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 05.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 05',12,7),(27,'GA05 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 05.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 05',13,7),(28,'GA05 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 05.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 05',12,7),(29,'GA06 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 06.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 06',14,8),(30,'GA06 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 06.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 06',15,8),(31,'GA06 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 06.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 06',14,8),(32,'GA06 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 06.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 06',15,8),(33,'GA06 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 06.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 06',14,8),(34,'GA07 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 07.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 07',16,9),(35,'GA07 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 07.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 07',17,9),(36,'GA07 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 07.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 07',16,9),(37,'GA07 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 07.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 07',17,9),(38,'GA07 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 07.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 07',16,9),(39,'GA08 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 08.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 08',18,10),(40,'GA08 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 08.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 08',19,10),(41,'GA08 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 08.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 08',18,10),(42,'GA08 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 08.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 08',19,10),(43,'GA08 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 08.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 08',18,10),(44,'GA09 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 09.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 09',20,11),(45,'GA09 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 09.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 09',21,11),(46,'GA09 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 09.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 09',20,11),(47,'GA09 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 09.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 09',21,11),(48,'GA09 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 09.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 09',20,11),(49,'GA10 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 10.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 10',22,12),(50,'GA10 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 10.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 10',23,12),(51,'GA10 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 10.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 10',22,12),(52,'GA10 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 10.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 10',23,12),(53,'GA10 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 10.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 10',22,12),(54,'GA11 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 11.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 11',24,13),(55,'GA11 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 11.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 11',25,13),(56,'GA11 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 11.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 11',24,13),(57,'GA11 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 11.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 11',25,13),(58,'GA11 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 11.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 11',24,13),(59,'GA12 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 12.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 12',26,14),(60,'GA12 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 12.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 12',27,14),(61,'GA12 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 12.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 12',26,14),(62,'GA12 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 12.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 12',27,14),(63,'GA12 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 12.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 12',26,14),(64,'GA13 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 13.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 13',28,15),(65,'GA13 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 13.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 13',29,15),(66,'GA13 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 13.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 13',28,15),(67,'GA13 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 13.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 13',29,15),(68,'GA13 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 13.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 13',28,15),(69,'GA14 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 14.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 14',30,16),(70,'GA14 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 14.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 14',31,16),(71,'GA14 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 14.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 14',30,16),(72,'GA14 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 14.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 14',31,16),(73,'GA14 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 14.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 14',30,16),(74,'GA15 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 15.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 15',32,17),(75,'GA15 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 15.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 15',33,17),(76,'GA15 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 15.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 15',32,17),(77,'GA15 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 15.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 15',33,17),(78,'GA15 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 15.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 15',32,17),(79,'GA16 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 16.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 16',34,18),(80,'GA16 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 16.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 16',35,18),(81,'GA16 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 16.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 16',34,18),(82,'GA16 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 16.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 16',35,18),(83,'GA16 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 16.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 16',34,18),(84,'GA17 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 17.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 17',36,19),(85,'GA17 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 17.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 17',37,19),(86,'GA17 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 17.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 17',36,19),(87,'GA17 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 17.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 17',37,19),(88,'GA17 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 17.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 17',36,19),(89,'GA18 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 18.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 18',38,20),(90,'GA18 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 18.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 18',39,20),(91,'GA18 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 18.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 18',38,20),(92,'GA18 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 18.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 18',39,20),(93,'GA18 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 18.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 18',38,20),(94,'GA19 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 19.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 19',40,21),(95,'GA19 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 19.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 19',41,21),(96,'GA19 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 19.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 19',40,21),(97,'GA19 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 19.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 19',41,21),(98,'GA19 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 19.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 19',40,21),(99,'GA20 Scheduled Workout 1','Auto-generated scheduled workout 1 for GA 20.','2026-04-13','07:00:00','2026-04-13','2026-04-13','Demo Facility 20',42,22),(100,'GA20 Scheduled Workout 2','Auto-generated scheduled workout 2 for GA 20.','2026-04-14','08:00:00','2026-04-14','2026-04-14','Demo Facility 20',43,22),(101,'GA20 Scheduled Workout 3','Auto-generated scheduled workout 3 for GA 20.','2026-04-15','09:00:00','2026-04-15','2026-04-15','Demo Facility 20',42,22),(102,'GA20 Scheduled Workout 4','Auto-generated scheduled workout 4 for GA 20.','2026-04-16','10:00:00','2026-04-16','2026-04-16','Demo Facility 20',43,22),(103,'GA20 Scheduled Workout 5','Auto-generated scheduled workout 5 for GA 20.','2026-04-17','11:00:00','2026-04-17','2026-04-17','Demo Facility 20',42,22);
/*!40000 ALTER TABLE `group_workout` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_workout_attendance`
--

DROP TABLE IF EXISTS `group_workout_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_workout_attendance` (
  `attendance_id` int NOT NULL AUTO_INCREMENT,
  `group_workout_id` int NOT NULL,
  `user_id` int NOT NULL,
  `attendance_status` varchar(16) NOT NULL DEFAULT 'pending',
  `attendance_updated` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`attendance_id`),
  UNIQUE KEY `uq_gwa_workout_user` (`group_workout_id`,`user_id`),
  KEY `fk_gwa_user` (`user_id`),
  CONSTRAINT `fk_gwa_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_gwa_workout` FOREIGN KEY (`group_workout_id`) REFERENCES `group_workout` (`group_workout_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_workout_attendance`
--

LOCK TABLES `group_workout_attendance` WRITE;
/*!40000 ALTER TABLE `group_workout_attendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `group_workout_attendance` ENABLE KEYS */;
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
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `motiv_group`
--

LOCK TABLES `motiv_group` WRITE;
/*!40000 ALTER TABLE `motiv_group` DISABLE KEYS */;
INSERT INTO `motiv_group` VALUES (1,'Morning Lifters','Early gym crew','2026-01-15',1,1),(2,'Campus Runners','Track and trail runs','2026-02-01',1,1),(3,'Yoga Circle','Relaxation and mobility','2026-02-10',2,2),(4,'Bulk GA01 Group 1','Synthetic demo group 1 for GA 01 to validate dashboards, groups, and invites.','2026-04-15',3,3),(5,'Bulk GA01 Group 2','Synthetic demo group 2 for GA 01 to validate dashboards, groups, and invites.','2026-04-15',3,3),(6,'Bulk GA02 Group 1','Synthetic demo group 1 for GA 02 to validate dashboards, groups, and invites.','2026-04-15',3,4),(7,'Bulk GA02 Group 2','Synthetic demo group 2 for GA 02 to validate dashboards, groups, and invites.','2026-04-15',3,4),(8,'Bulk GA03 Group 1','Synthetic demo group 1 for GA 03 to validate dashboards, groups, and invites.','2026-04-15',3,5),(9,'Bulk GA03 Group 2','Synthetic demo group 2 for GA 03 to validate dashboards, groups, and invites.','2026-04-15',3,5),(10,'Bulk GA04 Group 1','Synthetic demo group 1 for GA 04 to validate dashboards, groups, and invites.','2026-04-15',3,6),(11,'Bulk GA04 Group 2','Synthetic demo group 2 for GA 04 to validate dashboards, groups, and invites.','2026-04-15',3,6),(12,'Bulk GA05 Group 1','Synthetic demo group 1 for GA 05 to validate dashboards, groups, and invites.','2026-04-15',3,7),(13,'Bulk GA05 Group 2','Synthetic demo group 2 for GA 05 to validate dashboards, groups, and invites.','2026-04-15',3,7),(14,'Bulk GA06 Group 1','Synthetic demo group 1 for GA 06 to validate dashboards, groups, and invites.','2026-04-15',3,8),(15,'Bulk GA06 Group 2','Synthetic demo group 2 for GA 06 to validate dashboards, groups, and invites.','2026-04-15',3,8),(16,'Bulk GA07 Group 1','Synthetic demo group 1 for GA 07 to validate dashboards, groups, and invites.','2026-04-15',3,9),(17,'Bulk GA07 Group 2','Synthetic demo group 2 for GA 07 to validate dashboards, groups, and invites.','2026-04-15',3,9),(18,'Bulk GA08 Group 1','Synthetic demo group 1 for GA 08 to validate dashboards, groups, and invites.','2026-04-15',3,10),(19,'Bulk GA08 Group 2','Synthetic demo group 2 for GA 08 to validate dashboards, groups, and invites.','2026-04-15',3,10),(20,'Bulk GA09 Group 1','Synthetic demo group 1 for GA 09 to validate dashboards, groups, and invites.','2026-04-15',3,11),(21,'Bulk GA09 Group 2','Synthetic demo group 2 for GA 09 to validate dashboards, groups, and invites.','2026-04-15',3,11),(22,'Bulk GA10 Group 1','Synthetic demo group 1 for GA 10 to validate dashboards, groups, and invites.','2026-04-15',3,12),(23,'Bulk GA10 Group 2','Synthetic demo group 2 for GA 10 to validate dashboards, groups, and invites.','2026-04-15',3,12),(24,'Bulk GA11 Group 1','Synthetic demo group 1 for GA 11 to validate dashboards, groups, and invites.','2026-04-15',3,13),(25,'Bulk GA11 Group 2','Synthetic demo group 2 for GA 11 to validate dashboards, groups, and invites.','2026-04-15',3,13),(26,'Bulk GA12 Group 1','Synthetic demo group 1 for GA 12 to validate dashboards, groups, and invites.','2026-04-15',3,14),(27,'Bulk GA12 Group 2','Synthetic demo group 2 for GA 12 to validate dashboards, groups, and invites.','2026-04-15',3,14),(28,'Bulk GA13 Group 1','Synthetic demo group 1 for GA 13 to validate dashboards, groups, and invites.','2026-04-15',3,15),(29,'Bulk GA13 Group 2','Synthetic demo group 2 for GA 13 to validate dashboards, groups, and invites.','2026-04-15',3,15),(30,'Bulk GA14 Group 1','Synthetic demo group 1 for GA 14 to validate dashboards, groups, and invites.','2026-04-15',3,16),(31,'Bulk GA14 Group 2','Synthetic demo group 2 for GA 14 to validate dashboards, groups, and invites.','2026-04-15',3,16),(32,'Bulk GA15 Group 1','Synthetic demo group 1 for GA 15 to validate dashboards, groups, and invites.','2026-04-15',3,17),(33,'Bulk GA15 Group 2','Synthetic demo group 2 for GA 15 to validate dashboards, groups, and invites.','2026-04-15',3,17),(34,'Bulk GA16 Group 1','Synthetic demo group 1 for GA 16 to validate dashboards, groups, and invites.','2026-04-15',3,18),(35,'Bulk GA16 Group 2','Synthetic demo group 2 for GA 16 to validate dashboards, groups, and invites.','2026-04-15',3,18),(36,'Bulk GA17 Group 1','Synthetic demo group 1 for GA 17 to validate dashboards, groups, and invites.','2026-04-15',3,19),(37,'Bulk GA17 Group 2','Synthetic demo group 2 for GA 17 to validate dashboards, groups, and invites.','2026-04-15',3,19),(38,'Bulk GA18 Group 1','Synthetic demo group 1 for GA 18 to validate dashboards, groups, and invites.','2026-04-15',3,20),(39,'Bulk GA18 Group 2','Synthetic demo group 2 for GA 18 to validate dashboards, groups, and invites.','2026-04-15',3,20),(40,'Bulk GA19 Group 1','Synthetic demo group 1 for GA 19 to validate dashboards, groups, and invites.','2026-04-15',3,21),(41,'Bulk GA19 Group 2','Synthetic demo group 2 for GA 19 to validate dashboards, groups, and invites.','2026-04-15',3,21),(42,'Bulk GA20 Group 1','Synthetic demo group 1 for GA 20 to validate dashboards, groups, and invites.','2026-04-15',3,22),(43,'Bulk GA20 Group 2','Synthetic demo group 2 for GA 20 to validate dashboards, groups, and invites.','2026-04-15',3,22);
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
  `post_photo_path` varchar(255) DEFAULT NULL,
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
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `post`
--

LOCK TABLES `post` WRITE;
/*!40000 ALTER TABLE `post` DISABLE KEYS */;
INSERT INTO `post` VALUES (1,'Great session today everyone!',NULL,'2026-04-15 22:24:32','09:30:00','2026-04-01',1,1),(2,'Hit a new PR on squat',NULL,'2026-04-15 22:24:32','18:00:00','2026-04-02',NULL,2),(3,'Who is joining the weekend run?',NULL,'2026-04-15 22:24:32','12:15:00','2026-04-03',NULL,3),(4,'Auto post from bulk user 0001',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,24),(5,'Auto post from bulk user 0002',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,25),(6,'Auto post from bulk user 0003',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,26),(7,'Auto post from bulk user 0004',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,27),(8,'Auto post from bulk user 0005',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,28),(9,'Auto post from bulk user 0006',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,29),(10,'Auto post from bulk user 0007',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,30),(11,'Auto post from bulk user 0008',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,31),(12,'Auto post from bulk user 0009',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,32),(13,'Auto post from bulk user 0010',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,33),(14,'Auto post from bulk user 0011',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,34),(15,'Auto post from bulk user 0012',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,35),(16,'Auto post from bulk user 0013',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,36),(17,'Auto post from bulk user 0014',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,37),(18,'Auto post from bulk user 0015',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,38),(19,'Auto post from bulk user 0016',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,39),(20,'Auto post from bulk user 0017',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,40),(21,'Auto post from bulk user 0018',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,41),(22,'Auto post from bulk user 0019',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,42),(23,'Auto post from bulk user 0020',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,43),(24,'Auto post from bulk user 0021',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,44),(25,'Auto post from bulk user 0022',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,45),(26,'Auto post from bulk user 0023',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,46),(27,'Auto post from bulk user 0024',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,47),(28,'Auto post from bulk user 0025',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,48),(29,'Auto post from bulk user 0026',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,49),(30,'Auto post from bulk user 0027',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,50),(31,'Auto post from bulk user 0028',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,51),(32,'Auto post from bulk user 0029',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,52),(33,'Auto post from bulk user 0030',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,53),(34,'Auto post from bulk user 0031',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,54),(35,'Auto post from bulk user 0032',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,55),(36,'Auto post from bulk user 0033',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,56),(37,'Auto post from bulk user 0034',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,57),(38,'Auto post from bulk user 0035',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,58),(39,'Auto post from bulk user 0036',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,59),(40,'Auto post from bulk user 0037',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,60),(41,'Auto post from bulk user 0038',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,61),(42,'Auto post from bulk user 0039',NULL,'2026-04-15 22:34:32',NULL,'2026-04-15',NULL,62);
/*!40000 ALTER TABLE `post` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_challenge_leave`
--

DROP TABLE IF EXISTS `user_challenge_leave`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_challenge_leave` (
  `leave_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `challenge_id` int NOT NULL,
  `left_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`leave_id`),
  UNIQUE KEY `uq_ucl_user_challenge` (`user_id`,`challenge_id`),
  KEY `fk_ucl_challenge` (`challenge_id`),
  CONSTRAINT `fk_ucl_challenge` FOREIGN KEY (`challenge_id`) REFERENCES `challenge` (`challenge_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ucl_user` FOREIGN KEY (`user_id`) REFERENCES `app_user` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_challenge_leave`
--

LOCK TABLES `user_challenge_leave` WRITE;
/*!40000 ALTER TABLE `user_challenge_leave` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_challenge_leave` ENABLE KEYS */;
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
INSERT INTO `user_group` VALUES (1,1),(2,1),(1,2),(3,2),(3,3),(24,4),(25,5),(26,6),(27,7),(28,8),(29,9),(30,10),(31,11),(32,12),(33,13),(34,14),(35,15),(36,16),(37,17),(38,18),(39,19),(40,20),(41,21),(42,22),(43,23),(44,24),(45,25),(46,26),(47,27),(48,28),(49,29),(50,30),(51,31),(52,32),(53,33),(54,34),(55,35),(56,36),(57,37),(58,38),(59,39),(60,40),(61,41),(62,42),(63,43);
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
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout`
--

LOCK TABLES `workout` WRITE;
/*!40000 ALTER TABLE `workout` DISABLE KEYS */;
INSERT INTO `workout` VALUES (1,'2026-03-27',40,1,1),(2,'2026-03-27',36,1,NULL),(3,'2026-03-26',25,2,NULL),(4,'2026-03-25',15,3,2),(5,'2026-04-13',29,24,NULL),(6,'2026-04-15',30,24,NULL),(7,'2026-04-14',32,25,NULL),(8,'2026-04-16',33,25,NULL),(9,'2026-04-15',35,26,NULL),(10,'2026-04-17',36,26,NULL),(11,'2026-04-16',38,27,NULL),(12,'2026-04-18',39,27,NULL),(13,'2026-04-17',41,28,NULL),(14,'2026-04-19',42,28,NULL),(15,'2026-04-18',44,29,NULL),(16,'2026-04-13',45,29,NULL),(17,'2026-04-19',47,30,NULL),(18,'2026-04-14',48,30,NULL),(19,'2026-04-13',50,31,NULL),(20,'2026-04-15',51,31,NULL),(21,'2026-04-14',53,32,NULL),(22,'2026-04-16',54,32,NULL),(23,'2026-04-15',56,33,NULL),(24,'2026-04-17',57,33,NULL),(25,'2026-04-16',59,34,NULL),(26,'2026-04-18',60,34,NULL),(27,'2026-04-17',62,35,NULL),(28,'2026-04-19',63,35,NULL),(29,'2026-04-18',25,36,NULL),(30,'2026-04-13',26,36,NULL),(31,'2026-04-19',28,37,NULL),(32,'2026-04-14',29,37,NULL),(33,'2026-04-13',31,38,NULL),(34,'2026-04-15',32,38,NULL),(35,'2026-04-14',34,39,NULL),(36,'2026-04-16',35,39,NULL),(37,'2026-04-15',37,40,NULL),(38,'2026-04-17',38,40,NULL),(39,'2026-04-16',40,41,NULL),(40,'2026-04-18',41,41,NULL),(41,'2026-04-17',43,42,NULL),(42,'2026-04-19',44,42,NULL),(43,'2026-04-18',46,43,NULL),(44,'2026-04-13',47,43,NULL),(45,'2026-04-19',49,44,NULL),(46,'2026-04-14',50,44,NULL),(47,'2026-04-13',52,45,NULL),(48,'2026-04-15',53,45,NULL),(49,'2026-04-14',55,46,NULL),(50,'2026-04-16',56,46,NULL),(51,'2026-04-15',58,47,NULL),(52,'2026-04-17',59,47,NULL),(53,'2026-04-16',61,48,NULL),(54,'2026-04-18',62,48,NULL),(55,'2026-04-17',64,49,NULL),(56,'2026-04-19',25,49,NULL),(57,'2026-04-18',27,50,NULL),(58,'2026-04-13',28,50,NULL),(59,'2026-04-19',30,51,NULL),(60,'2026-04-14',31,51,NULL),(61,'2026-04-13',33,52,NULL),(62,'2026-04-15',34,52,NULL),(63,'2026-04-14',36,53,NULL),(64,'2026-04-16',37,53,NULL),(65,'2026-04-15',39,54,NULL),(66,'2026-04-17',40,54,NULL),(67,'2026-04-16',42,55,NULL),(68,'2026-04-18',43,55,NULL),(69,'2026-04-17',45,56,NULL),(70,'2026-04-19',46,56,NULL),(71,'2026-04-18',48,57,NULL),(72,'2026-04-13',49,57,NULL),(73,'2026-04-19',51,58,NULL),(74,'2026-04-14',52,58,NULL),(75,'2026-04-13',54,59,NULL),(76,'2026-04-15',55,59,NULL),(77,'2026-04-14',57,60,NULL),(78,'2026-04-16',58,60,NULL),(79,'2026-04-15',60,61,NULL),(80,'2026-04-17',61,61,NULL),(81,'2026-04-16',63,62,NULL),(82,'2026-04-18',64,62,NULL),(83,'2026-04-17',26,63,NULL),(84,'2026-04-19',27,63,NULL);
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
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workout_log`
--

LOCK TABLES `workout_log` WRITE;
/*!40000 ALTER TABLE `workout_log` DISABLE KEYS */;
INSERT INTO `workout_log` VALUES (1,3,10,135.00,1,1),(2,4,8,185.00,1,2),(3,3,20,0.00,2,3),(4,5,5,225.00,3,4),(5,5,11,61.00,5,3),(6,3,12,70.00,6,4),(7,3,13,68.00,7,4),(8,4,14,77.00,8,5),(9,4,15,75.00,9,5),(10,5,16,84.00,10,1),(11,5,17,82.00,11,1),(12,3,8,91.00,12,2),(13,3,9,89.00,13,2),(14,4,10,98.00,14,3),(15,4,11,96.00,15,3),(16,5,12,105.00,16,4),(17,5,13,103.00,17,4),(18,3,14,112.00,18,5),(19,3,15,110.00,19,5),(20,4,16,119.00,20,1),(21,4,17,117.00,21,1),(22,5,8,126.00,22,2),(23,5,9,124.00,23,2),(24,3,10,133.00,24,3),(25,3,11,131.00,25,3),(26,4,12,140.00,26,4),(27,4,13,138.00,27,4),(28,5,14,147.00,28,5),(29,5,15,145.00,29,5),(30,3,16,154.00,30,1),(31,3,17,152.00,31,1),(32,4,8,161.00,32,2),(33,4,9,159.00,33,2),(34,5,10,168.00,34,3),(35,5,11,166.00,35,3),(36,3,12,175.00,36,4),(37,3,13,173.00,37,4),(38,4,14,182.00,38,5),(39,4,15,180.00,39,5),(40,5,16,189.00,40,1),(41,5,17,187.00,41,1),(42,3,8,196.00,42,2),(43,3,9,194.00,43,2),(44,4,10,48.00,44,3),(45,4,11,46.00,45,3),(46,5,12,55.00,46,4),(47,5,13,53.00,47,4),(48,3,14,62.00,48,5),(49,3,15,60.00,49,5),(50,4,16,69.00,50,1),(51,4,17,67.00,51,1),(52,5,8,76.00,52,2),(53,5,9,74.00,53,2),(54,3,10,83.00,54,3),(55,3,11,81.00,55,3),(56,4,12,90.00,56,4),(57,4,13,88.00,57,4),(58,5,14,97.00,58,5),(59,5,15,95.00,59,5),(60,3,16,104.00,60,1),(61,3,17,102.00,61,1),(62,4,8,111.00,62,2),(63,4,9,109.00,63,2),(64,5,10,118.00,64,3),(65,5,11,116.00,65,3),(66,3,12,125.00,66,4),(67,3,13,123.00,67,4),(68,4,14,132.00,68,5),(69,4,15,130.00,69,5),(70,5,16,139.00,70,1),(71,5,17,137.00,71,1),(72,3,8,146.00,72,2),(73,3,9,144.00,73,2),(74,4,10,153.00,74,3),(75,4,11,151.00,75,3),(76,5,12,160.00,76,4),(77,5,13,158.00,77,4),(78,3,14,167.00,78,5),(79,3,15,165.00,79,5),(80,4,16,174.00,80,1),(81,4,17,172.00,81,1),(82,5,8,181.00,82,2),(83,5,9,179.00,83,2),(84,3,10,188.00,84,3);
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

-- Dump completed on 2026-04-15 22:44:23
