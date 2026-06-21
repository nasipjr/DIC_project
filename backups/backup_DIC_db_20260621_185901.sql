-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: DIC_db
-- ------------------------------------------------------
-- Server version	8.0.44

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
-- Table structure for table `client`
--

DROP TABLE IF EXISTS `client`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_client_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client`
--

LOCK TABLES `client` WRITE;
/*!40000 ALTER TABLE `client` DISABLE KEYS */;
INSERT INTO `client` VALUES (1,'أحمد المحمد','+963958111222','دمشق، ريف دمشق، الغوطة الشرقية','2026-06-21 04:31:38'),(2,'خالد العلي','+963944555666','حمص، الرستن','2026-06-21 04:31:38'),(3,'شركة النماء الزراعية','+963114445566','حلب، منطقة السفيرة','2026-06-21 04:31:38'),(4,'مزرعة الفيحاء الحديثة','+963933777888','درعا، إزرع','2026-06-21 04:31:38'),(5,'ياسر حميد',NULL,'اللاذقية، جبلة','2026-06-21 04:31:38'),(9,'نسيب جبارة','0998313283','اللاذقية','2026-06-21 18:01:09');
/*!40000 ALTER TABLE `client` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `client_file`
--

DROP TABLE IF EXISTS `client_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `client_file` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `filepath` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_size` int DEFAULT NULL,
  `uploaded_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `client_file_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `client_file`
--

LOCK TABLES `client_file` WRITE;
/*!40000 ALTER TABLE `client_file` DISABLE KEYS */;
/*!40000 ALTER TABLE `client_file` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_item`
--

DROP TABLE IF EXISTS `inventory_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `sku` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `company` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `last_updated` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_item`
--

LOCK TABLES `inventory_item` WRITE;
/*!40000 ALTER TABLE `inventory_item` DISABLE KEYS */;
INSERT INTO `inventory_item` VALUES (1,'خراطيم تنقيط GR 16 مم - 40 سم','GR-16',50,85.00,'شركة شام للبلاستيك','لفة خراطيم تنقيط 400 متر، مسافة 40 سم بين المنقطات','2026-06-21 04:31:38'),(2,'مضخة مياه أفقية 5.5 حصان سبروني','PUMP-5.5',6,6500.00,'Speroni Italy','مضخة مياه كهربائية 3 فاز للري','2026-06-21 18:01:09'),(3,'فلتر رملي مزدوج 3 بوصة','FLTR-SAND-3',4,4200.00,'المركز التقني','شبكة فلاتر رملية لتصفية مياه الآبار من الشوائب','2026-06-21 04:31:38'),(4,'منقطات تعويض ضغط 4 لتر/ساعة','DRIP-PC-4',1200,1.25,'نتافيم','منقطات ذكية لتعويض الضغط وضمان التساوي في الري','2026-06-21 04:31:38'),(5,'محبس بوابة نحاسي 2 بوصة ITAP','VALVE-BR-2',35,180.00,'ITAP Italy','صمام بوابة نحاسي للتحكم بالشبكة الرئيسية','2026-06-21 04:31:38'),(6,'لوحة تحكم ري ذكية 8 محطات','CTRL-8',6,1250.00,'Hunter USA','لوحة تحكم إلكترونية مبرمجة لري الحدائق والمزارع','2026-06-21 04:31:38'),(7,'سماد ذواب 20-20-20 متوازن','FERT-20',120,45.00,'شركة أسمدة حمص','كيس 25 كغ سماد ذواب عالي النقاوة NPK','2026-06-21 04:31:38');
/*!40000 ALTER TABLE `inventory_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice`
--

DROP TABLE IF EXISTS `invoice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `client_phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `client_address` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `issue_date` datetime NOT NULL,
  `discount` decimal(10,2) NOT NULL,
  `discount_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tax_rate` decimal(5,2) NOT NULL,
  `total_amount` decimal(10,2) NOT NULL,
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice`
--

LOCK TABLES `invoice` WRITE;
/*!40000 ALTER TABLE `invoice` DISABLE KEYS */;
INSERT INTO `invoice` VALUES (1,'أحمد المحمد','+963958111222','دمشق، ريف دمشق، الغوطة الشرقية','2026-04-22 04:31:38',0.00,'value',0.00,8500.00,'Paid'),(2,'أحمد المحمد','+963958111222','دمشق، ريف دمشق، الغوطة الشرقية','2026-05-07 04:31:38',0.00,'value',0.00,11500.00,'Paid'),(3,'خالد العلي','+963944555666','حمص، الرستن','2026-05-22 04:31:38',140.00,'value',0.00,4720.00,'Partially Paid'),(4,'شركة النماء الزراعية','+963114445566','حلب، منطقة السفيرة','2026-06-06 04:31:38',0.00,'value',0.00,16700.00,'Unpaid'),(5,'مزرعة الفيحاء الحديثة','+963933777888','درعا، إزرع','2026-06-11 04:31:38',0.00,'value',0.00,1250.00,'Paid'),(13,'أحمد المحمد','+963958111222','دمشق، ريف دمشق، الغوطة الشرقية','2026-06-21 17:59:55',0.00,'value',0.00,6500.00,'Partially Paid'),(14,'نسيب جبارة','0998313283','اللاذقية','2026-06-21 18:01:09',0.00,'value',0.00,6500.00,'Partially Paid');
/*!40000 ALTER TABLE `invoice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoice_item`
--

DROP TABLE IF EXISTS `invoice_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoice_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `invoice_id` int NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` decimal(10,2) NOT NULL,
  `total_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `invoice_id` (`invoice_id`),
  CONSTRAINT `invoice_item_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoice_item`
--

LOCK TABLES `invoice_item` WRITE;
/*!40000 ALTER TABLE `invoice_item` DISABLE KEYS */;
INSERT INTO `invoice_item` VALUES (1,1,'خراطيم تنقيط GR 16 مم - 40 سم',100,85.00,8500.00),(2,2,'مضخة مياه أفقية 5.5 حصان سبروني',1,6500.00,6500.00),(3,2,'لوحة تحكم ري ذكية 8 محطات',4,1250.00,5000.00),(4,3,'سماد ذواب 20-20-20 متوازن',100,45.00,4500.00),(5,3,'محبس بوابة نحاسي 2 بوصة ITAP',2,180.00,360.00),(6,4,'فلتر رملي مزدوج 3 بوصة',2,4200.00,8400.00),(7,4,'مضخة مياه أفقية 5.5 حصان سبروني',1,6500.00,6500.00),(8,4,'محبس بوابة نحاسي 2 بوصة ITAP',10,180.00,1800.00),(9,5,'لوحة تحكم ري ذكية 8 محطات',1,1250.00,1250.00),(14,13,'مضخة مياه أفقية 5.5 حصان سبروني',1,6500.00,6500.00),(15,14,'مضخة مياه أفقية 5.5 حصان سبروني',1,6500.00,6500.00);
/*!40000 ALTER TABLE `invoice_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `client_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `payment_date` datetime NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `client_id` (`client_id`),
  CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `client` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
INSERT INTO `payment` VALUES (1,1,10000.00,'2026-05-12 04:31:38','دفعة أولى كاش'),(2,1,10500.00,'2026-05-22 04:31:38','دفعة ثانية عن طريق شيك بنكي'),(3,2,3500.00,'2026-06-01 04:31:38','دفعة أولى نقداً'),(4,4,2000.00,'2026-06-16 04:31:38','دفعة مقدمة لتغطية الفواتير القادمة'),(12,1,1000.00,'2026-06-21 17:59:55','دفعة تلقائية للفاتورة INV-0013 (جزئية)'),(13,9,5000.00,'2026-06-21 18:01:09','دفعة تلقائية للفاتورة INV-0014 (جزئية)');
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment_allocation`
--

DROP TABLE IF EXISTS `payment_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment_allocation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `payment_id` int NOT NULL,
  `invoice_id` int NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `payment_id` (`payment_id`),
  KEY `invoice_id` (`invoice_id`),
  CONSTRAINT `payment_allocation_ibfk_1` FOREIGN KEY (`payment_id`) REFERENCES `payment` (`id`),
  CONSTRAINT `payment_allocation_ibfk_2` FOREIGN KEY (`invoice_id`) REFERENCES `invoice` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment_allocation`
--

LOCK TABLES `payment_allocation` WRITE;
/*!40000 ALTER TABLE `payment_allocation` DISABLE KEYS */;
INSERT INTO `payment_allocation` VALUES (4,3,3,3500.00),(5,4,5,1250.00),(31,1,1,8500.00),(32,1,2,1500.00),(33,2,2,10000.00),(34,2,13,500.00),(35,12,13,1000.00),(36,13,14,5000.00);
/*!40000 ALTER TABLE `payment_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `system_setting`
--

DROP TABLE IF EXISTS `system_setting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_setting` (
  `id` int NOT NULL AUTO_INCREMENT,
  `key` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_system_setting_key` (`key`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `system_setting`
--

LOCK TABLES `system_setting` WRITE;
/*!40000 ALTER TABLE `system_setting` DISABLE KEYS */;
INSERT INTO `system_setting` VALUES (1,'clinic_name','Technical Center for Drip Irrigation'),(2,'clinic_phone','+963 958 948 727'),(3,'clinic_email','irrigation.tech.center@gmail.com'),(4,'clinic_address','Damascus, Syria'),(5,'currency_symbol','S.P'),(6,'default_appointment_duration','60'),(7,'working_hours_start','09:00'),(8,'working_hours_end','16:30'),(9,'working_days','0,1,2,3,4,6'),(10,'treatment_prices','{\"System Checkup\": 50000, \"Irrigation Design\": 150000, \"Piping Installation\": 300000, \"Pump Maintenance\": 120000, \"Drippers Setup\": 80000, \"Filter Cleaning\": 30000, \"System Optimization\": 100000, \"Urgent Leak Repair\": 75000}'),(11,'notification_enable_sms','false'),(12,'notification_enable_whatsapp','false'),(13,'notification_enable_email','false'),(14,'twilio_account_sid',''),(15,'twilio_auth_token',''),(16,'twilio_phone_number',''),(17,'twilio_whatsapp_number',''),(18,'smtp_host',''),(19,'smtp_port',''),(20,'smtp_user',''),(21,'smtp_password',''),(22,'smtp_from_email',''),(23,'tax_rate','0'),(24,'clinic_vat_number',''),(25,'clinic_description',''),(26,'social_facebook',''),(27,'social_instagram',''),(28,'social_linkedin',''),(29,'social_whatsapp',''),(30,'operating_hours_weekdays','Saturday - Thursday: 09:00 AM - 04:30 PM'),(31,'operating_hours_weekend','Friday: Closed'),(32,'companies','[\"Rain Bird\", \"Hunter\", \"Netafim\", \"Toro\"]');
/*!40000 ALTER TABLE `system_setting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `last_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `plain_password` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_user_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (1,'admin','scrypt:32768:8:1$ylm7PaPsxyf49vvE$b3693b6af1a6f4fcad8e0be8b8ffe4dc72538122940c0433825f1c647a5e3d8f20c8bdc136843675610692d9531b14dbb0dbc1c96254edb6eafa80084ffaed90','admin','أدمن','النظام',NULL);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-21 18:59:01
