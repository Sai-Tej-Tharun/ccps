-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: ccps_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `adminpanel_adminactionlog`
--

DROP TABLE IF EXISTS `adminpanel_adminactionlog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `adminpanel_adminactionlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `details` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `admin_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `adminpanel_adminactionlog_admin_user_id_8a1cea0e_fk_auth_user_id` (`admin_user_id`),
  CONSTRAINT `adminpanel_adminactionlog_admin_user_id_8a1cea0e_fk_auth_user_id` FOREIGN KEY (`admin_user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `adminpanel_adminactionlog`
--

LOCK TABLES `adminpanel_adminactionlog` WRITE;
/*!40000 ALTER TABLE `adminpanel_adminactionlog` DISABLE KEYS */;
INSERT INTO `adminpanel_adminactionlog` VALUES (1,'Exported transactions CSV','filters={}, row_count=7','2026-10-02 12:33:16.878697',1),(2,'Exported transactions CSV','filters={}, row_count=11','2026-10-02 12:58:33.430622',1);
/*!40000 ALTER TABLE `adminpanel_adminactionlog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add blacklisted token',7,'add_blacklistedtoken'),(26,'Can change blacklisted token',7,'change_blacklistedtoken'),(27,'Can delete blacklisted token',7,'delete_blacklistedtoken'),(28,'Can view blacklisted token',7,'view_blacklistedtoken'),(29,'Can add outstanding token',8,'add_outstandingtoken'),(30,'Can change outstanding token',8,'change_outstandingtoken'),(31,'Can delete outstanding token',8,'delete_outstandingtoken'),(32,'Can view outstanding token',8,'view_outstandingtoken'),(33,'Can add card',9,'add_card'),(34,'Can change card',9,'change_card'),(35,'Can delete card',9,'delete_card'),(36,'Can view card',9,'view_card'),(37,'Can add transaction',10,'add_transaction'),(38,'Can change transaction',10,'change_transaction'),(39,'Can delete transaction',10,'delete_transaction'),(40,'Can view transaction',10,'view_transaction'),(41,'Can add admin action log',11,'add_adminactionlog'),(42,'Can change admin action log',11,'change_adminactionlog'),(43,'Can delete admin action log',11,'delete_adminactionlog'),(44,'Can view admin action log',11,'view_adminactionlog');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$720000$BxZ3bW2Zmt98iV0AHQ3kl6$VAido/l6HQo7fA9JYLrtMgGq0qhemC+iUDCL244vD6Q=',NULL,1,'admin@example.com','','','admin@example.com',1,1,'2026-10-02 11:58:29.060100'),(2,'pbkdf2_sha256$720000$X4qidrVYnSW5hxAaWXEpNJ$97A13tMsa9rsN9IY9TXFqE9+3/TJk17zjGl2Fhxmevo=',NULL,0,'sai@example.com','sai','tharun','sai@example.com',0,1,'2026-10-02 12:05:36.333925'),(3,'pbkdf2_sha256$720000$xbcK3UufhbRVzGs5ZCAwCG$84pYyZPR9hE3bz/65KyLYf+OUPAFOCGDatq8AbQ1XiI=',NULL,0,'jane@example.com','Jane','Doe','jane@example.com',0,1,'2026-10-02 12:41:48.780945'),(4,'pbkdf2_sha256$720000$8WZJaFtN05w41FKaSfrbqO$25VUjmBFFvEbush/uiErQ/VfZLpOp8ghInNdfJCgF64=',NULL,0,'sai1@example.com','sai1','tharun','sai1@example.com',0,1,'2026-10-02 12:42:32.424397'),(5,'pbkdf2_sha256$720000$nlCpKP2so2pWXsAGGdnDbJ$i4caKOtITsjMZoKZRBRV56muMymWBE8vU/i1lU0G2Tk=',NULL,0,'sai2@example.com','sai','tharun','sai2@example.com',0,1,'2026-10-02 12:56:53.072518'),(6,'pbkdf2_sha256$720000$pLPuJrTf16M2nKogilpVvD$XhgLtrb23upXz/e5CEs3/jWvjqqVTx1DJZ3ZbjdoX9w=',NULL,0,'sai3@example.com','sai3','tharun','sai3@example.com',0,1,'2026-10-02 12:59:24.083767');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cards_card`
--

DROP TABLE IF EXISTS `cards_card`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cards_card` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `brand` varchar(20) NOT NULL,
  `masked_number` varchar(32) NOT NULL,
  `last4` varchar(4) NOT NULL,
  `cardholder_name` varchar(150) NOT NULL,
  `expiry_month` smallint unsigned NOT NULL,
  `expiry_year` smallint unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `cards_card_user_id_9c174339_fk_auth_user_id` (`user_id`),
  CONSTRAINT `cards_card_user_id_9c174339_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `cards_card_chk_1` CHECK ((`expiry_month` >= 0)),
  CONSTRAINT `cards_card_chk_2` CHECK ((`expiry_year` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cards_card`
--

LOCK TABLES `cards_card` WRITE;
/*!40000 ALTER TABLE `cards_card` DISABLE KEYS */;
INSERT INTO `cards_card` VALUES (1,'VISA','**** **** **** 1111','1111','sai tharun',10,2036,'2026-10-02 12:09:02.158159',2),(2,'VISA','**** **** **** 0002','0002','invalid card',10,2036,'2026-10-02 12:16:37.524961',2),(3,'VISA','**** **** **** 1111','1111','sai1 tharun',10,2036,'2026-10-02 12:47:07.140360',4),(4,'VISA','**** **** **** 1111','1111','sai tharun',10,2036,'2026-10-02 12:57:18.773705',2),(5,'VISA','**** **** **** 1111','1111','sai3 tharun',10,2036,'2026-10-02 12:59:45.391561',6);
/*!40000 ALTER TABLE `cards_card` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(11,'adminpanel','adminactionlog'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(9,'cards','card'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(7,'token_blacklist','blacklistedtoken'),(8,'token_blacklist','outstandingtoken'),(10,'transactions','transaction');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-02 11:58:13.476190'),(2,'auth','0001_initial','2026-10-02 11:58:17.120419'),(3,'admin','0001_initial','2026-10-02 11:58:17.946975'),(4,'admin','0002_logentry_remove_auto_add','2026-10-02 11:58:17.973786'),(5,'admin','0003_logentry_add_action_flag_choices','2026-10-02 11:58:18.000206'),(6,'adminpanel','0001_initial','2026-10-02 11:58:18.707943'),(7,'contenttypes','0002_remove_content_type_name','2026-10-02 11:58:19.241769'),(8,'auth','0002_alter_permission_name_max_length','2026-10-02 11:58:19.590659'),(9,'auth','0003_alter_user_email_max_length','2026-10-02 11:58:19.674949'),(10,'auth','0004_alter_user_username_opts','2026-10-02 11:58:19.705825'),(11,'auth','0005_alter_user_last_login_null','2026-10-02 11:58:19.996472'),(12,'auth','0006_require_contenttypes_0002','2026-10-02 11:58:20.012846'),(13,'auth','0007_alter_validators_add_error_messages','2026-10-02 11:58:20.045444'),(14,'auth','0008_alter_user_username_max_length','2026-10-02 11:58:20.440405'),(15,'auth','0009_alter_user_last_name_max_length','2026-10-02 11:58:20.794166'),(16,'auth','0010_alter_group_name_max_length','2026-10-02 11:58:20.862308'),(17,'auth','0011_update_proxy_permissions','2026-10-02 11:58:20.892072'),(18,'auth','0012_alter_user_first_name_max_length','2026-10-02 11:58:21.217165'),(19,'cards','0001_initial','2026-10-02 11:58:21.690305'),(20,'sessions','0001_initial','2026-10-02 11:58:21.908782'),(21,'token_blacklist','0001_initial','2026-10-02 11:58:22.894796'),(22,'token_blacklist','0002_outstandingtoken_jti_hex','2026-10-02 11:58:23.164505'),(23,'token_blacklist','0003_auto_20171017_2007','2026-10-02 11:58:23.196974'),(24,'token_blacklist','0004_auto_20171017_2013','2026-10-02 11:58:23.681979'),(25,'token_blacklist','0005_remove_outstandingtoken_jti','2026-10-02 11:58:23.991471'),(26,'token_blacklist','0006_auto_20171017_2113','2026-10-02 11:58:24.102206'),(27,'token_blacklist','0007_auto_20171017_2214','2026-10-02 11:58:25.455405'),(28,'token_blacklist','0008_migrate_to_bigautofield','2026-10-02 11:58:26.885608'),(29,'token_blacklist','0010_fix_migrate_to_bigautofield','2026-10-02 11:58:26.922553'),(30,'token_blacklist','0011_linearizes_history','2026-10-02 11:58:26.942096'),(31,'token_blacklist','0012_alter_outstandingtoken_user','2026-10-02 11:58:26.972982'),(32,'transactions','0001_initial','2026-10-02 11:58:28.059920');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `token_blacklist_blacklistedtoken`
--

DROP TABLE IF EXISTS `token_blacklist_blacklistedtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_blacklistedtoken` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `blacklisted_at` datetime(6) NOT NULL,
  `token_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_id` (`token_id`),
  CONSTRAINT `token_blacklist_blacklistedtoken_token_id_3cc7fe56_fk` FOREIGN KEY (`token_id`) REFERENCES `token_blacklist_outstandingtoken` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `token_blacklist_blacklistedtoken`
--

LOCK TABLES `token_blacklist_blacklistedtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` DISABLE KEYS */;
INSERT INTO `token_blacklist_blacklistedtoken` VALUES (1,'2026-10-02 12:22:49.672099',1),(2,'2026-10-02 12:30:11.098065',2),(3,'2026-10-02 12:55:17.228604',3),(4,'2026-10-02 12:58:21.059288',5);
/*!40000 ALTER TABLE `token_blacklist_blacklistedtoken` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `token_blacklist_outstandingtoken`
--

DROP TABLE IF EXISTS `token_blacklist_outstandingtoken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `token_blacklist_outstandingtoken` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `token` longtext NOT NULL,
  `created_at` datetime(6) DEFAULT NULL,
  `expires_at` datetime(6) NOT NULL,
  `user_id` int DEFAULT NULL,
  `jti` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token_blacklist_outstandingtoken_jti_hex_d9bdf6f7_uniq` (`jti`),
  KEY `token_blacklist_outs_user_id_83bc629a_fk_auth_user` (`user_id`),
  CONSTRAINT `token_blacklist_outs_user_id_83bc629a_fk_auth_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `token_blacklist_outstandingtoken`
--

LOCK TABLES `token_blacklist_outstandingtoken` WRITE;
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` DISABLE KEYS */;
INSERT INTO `token_blacklist_outstandingtoken` VALUES (1,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU0NzYwNSwiaWF0IjoxNzkwOTQyODA1LCJqdGkiOiJiMjdiNTFmZWM0YWM0MzM0Yjc1NGZmNGVjZDVhNDU3NSIsInVzZXJfaWQiOjJ9.WgHI8zCKc8dpWHEIFL28vS2lmjbRbRpMX44ZpdQJgAo','2026-10-02 12:06:45.394810','2026-10-09 12:06:45.000000',2,'b27b51fec4ac4334b754ff4ecd5a4575'),(2,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU0OTAwNCwiaWF0IjoxNzkwOTQ0MjA0LCJqdGkiOiIzZmQxOGIzMzQwZTA0OWU1YjgyMTdhMzQ5N2UzZGRmMSIsInVzZXJfaWQiOjJ9.0AQnvvs3PG17qce4TPtyc61Q_7D7TPBPbRdgdjGd_l4','2026-10-02 12:30:04.799435','2026-10-09 12:30:04.000000',2,'3fd18b3340e049e5b8217a3497e3ddf1'),(3,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU0OTAyMCwiaWF0IjoxNzkwOTQ0MjIwLCJqdGkiOiIzY2ZkMWJjMTE0OGI0ZjA2OTRkYjMzYjgxZjE3MTBkOCIsInVzZXJfaWQiOjF9.xBPe1jnubZYZVpRxVvH6PvVrOVvqqytl3Hw-iF4tOH8','2026-10-02 12:30:20.183933','2026-10-09 12:30:20.000000',1,'3cfd1bc1148b4f0694db33b81f1710d8'),(4,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU0OTc2NSwiaWF0IjoxNzkwOTQ0OTY1LCJqdGkiOiJmZWJjOTE4ZGUxZDk0N2NiYWRjYjFjZDBmYmI4NzNhYSIsInVzZXJfaWQiOjR9.CIv8eljKX-HnFHpw4tBcF8xu9ex3SxAE4YX885Z3BYM','2026-10-02 12:42:45.365806','2026-10-09 12:42:45.000000',4,'febc918de1d947cbadcb1cd0fbb873aa'),(5,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU1MDYyMCwiaWF0IjoxNzkwOTQ1ODIwLCJqdGkiOiJkNmM1NjcyYWE2Y2Y0YmQ3YWM5NWZjMDg2MmE3YTAwNiIsInVzZXJfaWQiOjJ9.vSw0wyEq9M2GmyxcjNeKHk1aTPbNhuGOzW6OuiUzb8s','2026-10-02 12:57:00.772068','2026-10-09 12:57:00.000000',2,'d6c5672aa6cf4bd7ac95fc0862a7a006'),(6,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU1MDcwNSwiaWF0IjoxNzkwOTQ1OTA1LCJqdGkiOiJjMGRkODQ5YmQ4NWU0YTkyOGM5MDI3NmJhNDhkMTkxOCIsInVzZXJfaWQiOjF9.VbgRxK4sVnSpyLaQ6bHBFcxpf-Wk7MZyFC4MKkWl-sM','2026-10-02 12:58:25.481288','2026-10-09 12:58:25.000000',1,'c0dd849bd85e4a928c90276ba48d1918'),(7,'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc5MTU1MDc3MywiaWF0IjoxNzkwOTQ1OTczLCJqdGkiOiIyMDY5MjcxMTVlZDE0ZmU3Yjg2NzllZWMxZTFmZDJhNCIsInVzZXJfaWQiOjZ9.kKk3lsD6W1X3x42h2EX6VtQqmYI5fcc78iGPWAbvDg0','2026-10-02 12:59:33.807778','2026-10-09 12:59:33.000000',6,'206927115ed14fe7b8679eec1e1fd2a4');
/*!40000 ALTER TABLE `token_blacklist_outstandingtoken` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transactions_transaction`
--

DROP TABLE IF EXISTS `transactions_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transactions_transaction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(12,2) NOT NULL,
  `currency` varchar(3) NOT NULL,
  `status` varchar(10) NOT NULL,
  `reference` varchar(36) NOT NULL,
  `failure_reason` varchar(255) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `card_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference` (`reference`),
  KEY `transactions_transaction_card_id_b6891695_fk_cards_card_id` (`card_id`),
  KEY `transaction_user_id_9cef77_idx` (`user_id`,`status`),
  KEY `transaction_created_67ce7b_idx` (`created_at`),
  CONSTRAINT `transactions_transaction_card_id_b6891695_fk_cards_card_id` FOREIGN KEY (`card_id`) REFERENCES `cards_card` (`id`),
  CONSTRAINT `transactions_transaction_user_id_b9ecc248_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transactions_transaction`
--

LOCK TABLES `transactions_transaction` WRITE;
/*!40000 ALTER TABLE `transactions_transaction` DISABLE KEYS */;
INSERT INTO `transactions_transaction` VALUES (1,25.02,'USD','SUCCESS','2068a4d853b447199ba71fa6b7e14c5e','','2026-10-02 12:12:50.279158','2026-10-02 12:12:50.304721',1,2),(2,5001.00,'USD','FAILED','61b6403f9292485b81e59b7b60c5d0ae','Amount exceeds simulated processing limit of 5000.00.','2026-10-02 12:14:23.999182','2026-10-02 12:14:24.019920',1,2),(3,25.00,'USD','FAILED','eb6031613c754625a3f336336bc14ec7','Card declined by simulated issuer.','2026-10-02 12:16:44.580338','2026-10-02 12:16:44.604413',2,2),(4,50001.00,'USD','FAILED','b21085f20e79487ca5ba1d3c860fed66','Amount exceeds simulated processing limit of 5000.00.','2026-10-02 12:18:42.538260','2026-10-02 12:18:42.559974',1,2),(5,34.00,'USD','SUCCESS','1a199c7b226f4bcbab8fb781485d7c04','','2026-10-02 12:19:14.500119','2026-10-02 12:19:14.520085',1,2),(6,45.00,'USD','SUCCESS','161567db435841c4a739c9f62fcea686','','2026-10-02 12:19:18.068233','2026-10-02 12:19:18.090153',1,2),(7,56.00,'USD','SUCCESS','08952a27382a43328a13b162c627482a','','2026-10-02 12:19:19.786762','2026-10-02 12:19:19.813332',1,2),(8,25.00,'USD','SUCCESS','1303db8031744a49bf48d9925d688366','','2026-10-02 12:48:52.460825','2026-10-02 12:48:52.486719',3,4),(9,25.00,'USD','SUCCESS','f0bce6fdd6e24f358ec4c9d843a46bd3','','2026-10-02 12:57:28.212054','2026-10-02 12:57:28.234358',4,2),(10,25.00,'USD','FAILED','3b011995e27e4ceda0d0f138cd28963a','Card declined by simulated issuer.','2026-10-02 12:57:39.562613','2026-10-02 12:57:39.585560',2,2),(11,5001.00,'USD','FAILED','30b00a6326b141798962872684b735cd','Amount exceeds simulated processing limit of 5000.00.','2026-10-02 12:57:53.767434','2026-10-02 12:57:53.797599',4,2),(12,25.00,'USD','SUCCESS','fa1b38a8214744dcb99223aa2e4da9a3','','2026-10-02 13:00:00.761338','2026-10-02 13:00:00.788180',5,6);
/*!40000 ALTER TABLE `transactions_transaction` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-02 13:08:39
