-- MySQL dump 10.13  Distrib 5.1.59, for apple-darwin10.3.0 (i386)
--
-- Host: opsdb.tagged.com    Database: TagOpsDB
-- ------------------------------------------------------
-- Server version	5.1.73-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `app_definitions`
--

DROP TABLE IF EXISTS `app_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_definitions` (
  `AppID` smallint(2) NOT NULL AUTO_INCREMENT,
  `distribution` enum('centos5.4','centos6.2','centos6.4','centos6.5','centos7.0','fedora18','rhel5.3','rhel6.2','rhel6.3','rhel6.4','rhel6.5') DEFAULT NULL,
  `appType` varchar(100) NOT NULL,
  `hostBase` varchar(100) DEFAULT NULL,
  `puppetClass` varchar(100) NOT NULL DEFAULT 'baseclass',
  `GangliaID` int(11) NOT NULL DEFAULT '1',
  `GgroupName` varchar(25) DEFAULT NULL,
  `description` varchar(100) DEFAULT NULL,
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  PRIMARY KEY (`AppID`),
  KEY `GangliaID` (`GangliaID`),
  CONSTRAINT `app_definitions_ibfk_6` FOREIGN KEY (`GangliaID`) REFERENCES `ganglia` (`GangliaID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `app_deployments`
--

DROP TABLE IF EXISTS `app_deployments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_deployments` (
  `AppDeploymentID` int(11) NOT NULL AUTO_INCREMENT,
  `DeploymentID` int(11) NOT NULL,
  `AppID` smallint(6) NOT NULL,
  `user` varchar(32) NOT NULL,
  `status` enum('complete','incomplete','inprogress','invalidated','validated') NOT NULL,
  `environment_id` int(11) NOT NULL,
  `realized` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`AppDeploymentID`),
  KEY `DeploymentID` (`DeploymentID`),
  KEY `AppID` (`AppID`),
  KEY `fk_app_deployments_environment_id_environments` (`environment_id`),
  CONSTRAINT `app_deployments_ibfk_1` FOREIGN KEY (`DeploymentID`) REFERENCES `deployments` (`DeploymentID`) ON DELETE CASCADE,
  CONSTRAINT `app_deployments_ibfk_2` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE,
  CONSTRAINT `fk_app_deployments_environment_id_environments` FOREIGN KEY (`environment_id`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `app_hipchat_rooms`
--

DROP TABLE IF EXISTS `app_hipchat_rooms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_hipchat_rooms` (
  `AppID` smallint(6) NOT NULL,
  `roomID` int(11) NOT NULL,
  PRIMARY KEY (`AppID`,`roomID`),
  KEY `roomID` (`roomID`),
  CONSTRAINT `app_hipchat_rooms_ibfk_1` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE,
  CONSTRAINT `app_hipchat_rooms_ibfk_2` FOREIGN KEY (`roomID`) REFERENCES `hipchat` (`roomID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `app_jmx_attributes`
--

DROP TABLE IF EXISTS `app_jmx_attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_jmx_attributes` (
  `jmx_attribute_id` int(11) NOT NULL,
  `AppID` smallint(6) NOT NULL,
  PRIMARY KEY (`AppID`,`jmx_attribute_id`),
  KEY `jmx_attribute_id` (`jmx_attribute_id`),
  CONSTRAINT `app_jmx_attributes_ibfk_1` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE,
  CONSTRAINT `app_jmx_attributes_ibfk_2` FOREIGN KEY (`jmx_attribute_id`) REFERENCES `jmx_attributes` (`jmx_attribute_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `app_packages`
--

DROP TABLE IF EXISTS `app_packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `app_packages` (
  `pkgLocationID` int(11) NOT NULL,
  `AppID` smallint(6) NOT NULL,
  PRIMARY KEY (`pkgLocationID`,`AppID`),
  KEY `AppID` (`AppID`),
  CONSTRAINT `app_packages_ibfk_1` FOREIGN KEY (`pkgLocationID`) REFERENCES `package_locations` (`pkgLocationID`) ON DELETE CASCADE,
  CONSTRAINT `app_packages_ibfk_2` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `asset`
--

DROP TABLE IF EXISTS `asset`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asset` (
  `AssetID` int(11) NOT NULL AUTO_INCREMENT,
  `HostID` int(11) NOT NULL,
  `dateReceived` date DEFAULT NULL,
  `description` varchar(20) DEFAULT NULL,
  `oemSerial` varchar(30) DEFAULT NULL,
  `serviceTag` varchar(20) DEFAULT NULL,
  `taggedSerial` varchar(20) DEFAULT NULL,
  `invoiceNumber` varchar(20) DEFAULT NULL,
  `locationSite` varchar(20) DEFAULT NULL,
  `locationOwner` varchar(20) DEFAULT NULL,
  `costPerItem` varchar(20) DEFAULT NULL,
  `dateOfInvoice` date DEFAULT NULL,
  `warrantyStart` date DEFAULT NULL,
  `warrantyEnd` date DEFAULT NULL,
  `warrantyLevel` varchar(20) DEFAULT NULL,
  `warrantyID` varchar(20) DEFAULT NULL,
  `vendorContact` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`AssetID`),
  UNIQUE KEY `oemSerial` (`oemSerial`),
  KEY `HostID` (`HostID`),
  CONSTRAINT `asset_ibfk_1` FOREIGN KEY (`HostID`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `cname`
--

DROP TABLE IF EXISTS `cname`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cname` (
  `CnameID` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(40) DEFAULT NULL,
  `IpID` int(11) DEFAULT NULL,
  `ZoneID` int(11) DEFAULT NULL,
  PRIMARY KEY (`CnameID`),
  UNIQUE KEY `name_ZoneID` (`name`,`ZoneID`),
  KEY `IpID` (`IpID`),
  KEY `ZoneID` (`ZoneID`),
  CONSTRAINT `host_ips_fk` FOREIGN KEY (`IpID`) REFERENCES `host_ips` (`IpID`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `zones_fk` FOREIGN KEY (`ZoneID`) REFERENCES `zones` (`ZoneID`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `default_specs`
--

DROP TABLE IF EXISTS `default_specs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `default_specs` (
  `specID` int(11) NOT NULL,
  `AppID` smallint(6) NOT NULL,
  `environmentID` int(11) NOT NULL,
  `priority` int(4) NOT NULL DEFAULT '10',
  PRIMARY KEY (`specID`,`AppID`,`environmentID`),
  KEY `AppID` (`AppID`),
  KEY `environmentID` (`environmentID`),
  CONSTRAINT `default_specs_ibfk_1` FOREIGN KEY (`specID`) REFERENCES `host_specs` (`specID`) ON DELETE CASCADE,
  CONSTRAINT `default_specs_ibfk_2` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE,
  CONSTRAINT `default_specs_ibfk_3` FOREIGN KEY (`environmentID`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `deployments`
--

DROP TABLE IF EXISTS `deployments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `deployments` (
  `DeploymentID` int(11) NOT NULL AUTO_INCREMENT,
  `package_id` int(11) NOT NULL,
  `user` varchar(32) NOT NULL,
  `dep_type` enum('deploy','rollback') NOT NULL,
  `declared` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`DeploymentID`),
  KEY `PackageID` (`package_id`),
  CONSTRAINT `deployments_ibfk_1` FOREIGN KEY (`package_id`) REFERENCES `packages` (`package_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `environments`
--

DROP TABLE IF EXISTS `environments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `environments` (
  `environmentID` int(11) NOT NULL AUTO_INCREMENT,
  `environment` varchar(15) NOT NULL,
  `env` varchar(12) NOT NULL,
  `domain` varchar(32) NOT NULL,
  `prefix` varchar(1) NOT NULL,
  PRIMARY KEY (`environmentID`),
  UNIQUE KEY `domain` (`domain`),
  UNIQUE KEY `environment` (`environment`),
  UNIQUE KEY `env` (`env`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ganglia`
--

DROP TABLE IF EXISTS `ganglia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ganglia` (
  `GangliaID` int(11) NOT NULL AUTO_INCREMENT,
  `cluster_name` varchar(50) DEFAULT NULL,
  `port` int(5) NOT NULL DEFAULT '8649',
  PRIMARY KEY (`GangliaID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hipchat`
--

DROP TABLE IF EXISTS `hipchat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `hipchat` (
  `roomID` int(11) NOT NULL AUTO_INCREMENT,
  `room_name` varchar(50) NOT NULL,
  PRIMARY KEY (`roomID`),
  UNIQUE KEY `room_name` (`room_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `host_deployments`
--

DROP TABLE IF EXISTS `host_deployments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host_deployments` (
  `HostDeploymentID` int(11) NOT NULL AUTO_INCREMENT,
  `DeploymentID` int(11) NOT NULL,
  `HostID` int(11) NOT NULL,
  `user` varchar(32) NOT NULL,
  `status` enum('inprogress','failed','ok') NOT NULL,
  `realized` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`HostDeploymentID`),
  KEY `DeploymentID` (`DeploymentID`),
  KEY `HostID` (`HostID`),
  CONSTRAINT `host_deployments_ibfk_1` FOREIGN KEY (`DeploymentID`) REFERENCES `deployments` (`DeploymentID`) ON DELETE CASCADE,
  CONSTRAINT `host_deployments_ibfk_2` FOREIGN KEY (`HostID`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `host_interfaces`
--

DROP TABLE IF EXISTS `host_interfaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host_interfaces` (
  `InterfaceID` int(11) NOT NULL AUTO_INCREMENT,
  `HostID` int(11) DEFAULT NULL,
  `NetworkID` int(11) DEFAULT NULL,
  `interfaceName` varchar(10) DEFAULT NULL,
  `macAddress` varchar(18) DEFAULT NULL,
  `PortID` int(11) DEFAULT NULL,
  PRIMARY KEY (`InterfaceID`),
  UNIQUE KEY `HostID_2` (`HostID`,`interfaceName`),
  UNIQUE KEY `macAddress` (`macAddress`),
  UNIQUE KEY `PortID_2` (`PortID`),
  KEY `HostID` (`HostID`),
  KEY `PortID` (`PortID`),
  KEY `NetworkID` (`NetworkID`),
  CONSTRAINT `host_interfaces_ibfk_1` FOREIGN KEY (`HostID`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE,
  CONSTRAINT `host_interfaces_ibfk_2` FOREIGN KEY (`PortID`) REFERENCES `ports` (`PortID`),
  CONSTRAINT `host_interfaces_ibfk_3` FOREIGN KEY (`NetworkID`) REFERENCES `networkDevice` (`NetworkID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `host_ips`
--

DROP TABLE IF EXISTS `host_ips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host_ips` (
  `IpID` int(11) NOT NULL AUTO_INCREMENT,
  `InterfaceID` int(11) NOT NULL,
  `SubnetID` int(11) NOT NULL,
  `priority` int(10) unsigned NOT NULL DEFAULT '1',
  `ARecord` varchar(200) DEFAULT NULL,
  `comments` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`IpID`),
  UNIQUE KEY `SubnetID_2` (`SubnetID`),
  KEY `InterfaceID` (`InterfaceID`),
  KEY `SubnetID` (`SubnetID`),
  CONSTRAINT `host_ips_ibfk_2` FOREIGN KEY (`SubnetID`) REFERENCES `subnet` (`SubnetID`) ON DELETE CASCADE,
  CONSTRAINT `host_ips_ibfk_3` FOREIGN KEY (`InterfaceID`) REFERENCES `host_interfaces` (`InterfaceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `host_specs`
--

DROP TABLE IF EXISTS `host_specs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `host_specs` (
  `specID` int(11) NOT NULL AUTO_INCREMENT,
  `gen` varchar(4) DEFAULT NULL,
  `memorySize` int(4) DEFAULT NULL,
  `cores` smallint(2) NOT NULL,
  `cpuSpeed` int(6) DEFAULT NULL,
  `diskSize` int(6) DEFAULT NULL,
  `vendor` varchar(20) DEFAULT NULL,
  `model` varchar(20) DEFAULT NULL,
  `control` enum('digi','ipmi','vmware','libvirt') DEFAULT NULL,
  `virtual` tinyint(1) NOT NULL DEFAULT '0',
  `expansions` mediumtext,
  PRIMARY KEY (`specID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hosts`
--

DROP TABLE IF EXISTS `hosts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `hosts` (
  `HostID` int(11) NOT NULL AUTO_INCREMENT,
  `SpecID` int(11) DEFAULT NULL,
  `state` enum('baremetal','operational','repair','parts','reserved','escrow') NOT NULL,
  `hostname` varchar(30) DEFAULT NULL,
  `arch` varchar(10) DEFAULT NULL,
  `kernelVersion` varchar(20) DEFAULT NULL,
  `distribution` varchar(20) DEFAULT NULL,
  `timezone` varchar(10) DEFAULT NULL,
  `AppID` smallint(6) NOT NULL,
  `cageLocation` int(11) DEFAULT NULL,
  `cabLocation` varchar(10) DEFAULT NULL,
  `section` varchar(10) DEFAULT NULL,
  `rackLocation` int(11) DEFAULT NULL,
  `consolePort` varchar(11) DEFAULT NULL,
  `powerPort` varchar(10) DEFAULT NULL,
  `powerCircuit` varchar(10) DEFAULT NULL,
  `environment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`HostID`),
  UNIQUE KEY `cageLocation` (`cageLocation`,`cabLocation`,`consolePort`),
  UNIQUE KEY `cageLocation_2` (`cageLocation`,`cabLocation`,`rackLocation`),
  KEY `SpecID` (`SpecID`),
  KEY `AppID` (`AppID`),
  KEY `fk_hosts_environment_id_environments` (`environment_id`),
  CONSTRAINT `fk_hosts_environment_id_environments` FOREIGN KEY (`environment_id`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE,
  CONSTRAINT `hosts_ibfk_1` FOREIGN KEY (`SpecID`) REFERENCES `host_specs` (`specID`),
  CONSTRAINT `hosts_ibfk_2` FOREIGN KEY (`AppID`) REFERENCES `app_definitions` (`AppID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `iloms`
--

DROP TABLE IF EXISTS `iloms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `iloms` (
  `ILomID` int(11) NOT NULL AUTO_INCREMENT,
  `HostID` int(11) DEFAULT NULL,
  `SubnetID` int(11) NOT NULL,
  `macAddress` varchar(18) DEFAULT NULL,
  `PortID` int(11) DEFAULT NULL,
  `ARecord` varchar(200) DEFAULT NULL,
  `comments` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`ILomID`),
  UNIQUE KEY `SubnetID_2` (`SubnetID`),
  UNIQUE KEY `HostID_2` (`HostID`),
  UNIQUE KEY `macAddress` (`macAddress`),
  UNIQUE KEY `PortID_2` (`PortID`),
  KEY `HostID` (`HostID`),
  KEY `SubnetID` (`SubnetID`),
  KEY `PortID` (`PortID`),
  CONSTRAINT `ilom_ibfk_1` FOREIGN KEY (`HostID`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE,
  CONSTRAINT `ilom_ibfk_2` FOREIGN KEY (`SubnetID`) REFERENCES `subnet` (`SubnetID`) ON DELETE CASCADE,
  CONSTRAINT `ilom_ibfk_3` FOREIGN KEY (`PortID`) REFERENCES `ports` (`PortID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `jmx_attributes`
--

DROP TABLE IF EXISTS `jmx_attributes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jmx_attributes` (
  `jmx_attribute_id` int(11) NOT NULL AUTO_INCREMENT,
  `obj` varchar(300) NOT NULL,
  `attr` varchar(300) NOT NULL,
  `GgroupName` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`jmx_attribute_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `locks`
--

DROP TABLE IF EXISTS `locks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `locks` (
  `val` varchar(64) NOT NULL,
  `host` varchar(32) NOT NULL,
  UNIQUE KEY `val` (`val`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_apptypes_services`
--

DROP TABLE IF EXISTS `nag_apptypes_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_apptypes_services` (
  `app_id` smallint(2) NOT NULL,
  `service_id` int(11) NOT NULL,
  `server_app_id` smallint(6) NOT NULL,
  `environment_id` int(11) NOT NULL,
  PRIMARY KEY (`app_id`,`service_id`,`server_app_id`,`environment_id`),
  KEY `service_id` (`service_id`),
  KEY `environment_id` (`environment_id`),
  KEY `server_app_id` (`server_app_id`),
  CONSTRAINT `nag_apptypes_services_ibfk_1` FOREIGN KEY (`app_id`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE,
  CONSTRAINT `nag_apptypes_services_ibfk_2` FOREIGN KEY (`service_id`) REFERENCES `nag_services` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_apptypes_services_ibfk_4` FOREIGN KEY (`environment_id`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE,
  CONSTRAINT `nag_apptypes_services_ibfk_5` FOREIGN KEY (`server_app_id`) REFERENCES `app_definitions` (`AppID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_check_commands`
--

DROP TABLE IF EXISTS `nag_check_commands`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_check_commands` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `command_name` varchar(32) NOT NULL,
  `command_line` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `command_name` (`command_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_command_arguments`
--

DROP TABLE IF EXISTS `nag_command_arguments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_command_arguments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `check_command_id` int(11) NOT NULL,
  `label` varchar(32) NOT NULL,
  `description` varchar(255) NOT NULL,
  `arg_order` int(11) NOT NULL,
  `default_value` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `check_command_arg_order` (`check_command_id`,`arg_order`),
  CONSTRAINT `nag_command_arguments_ibfk_1` FOREIGN KEY (`check_command_id`) REFERENCES `nag_check_commands` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_contact_groups`
--

DROP TABLE IF EXISTS `nag_contact_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_contact_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `alias` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_contact_groups_members`
--

DROP TABLE IF EXISTS `nag_contact_groups_members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_contact_groups_members` (
  `contact_id` int(11) NOT NULL,
  `contact_group_id` int(11) NOT NULL,
  PRIMARY KEY (`contact_id`,`contact_group_id`),
  KEY `contact_group_id` (`contact_group_id`),
  CONSTRAINT `nag_contact_groups_members_ibfk_1` FOREIGN KEY (`contact_id`) REFERENCES `nag_contacts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_contact_groups_members_ibfk_2` FOREIGN KEY (`contact_group_id`) REFERENCES `nag_contact_groups` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_contacts`
--

DROP TABLE IF EXISTS `nag_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_contacts` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `alias` varchar(80) DEFAULT NULL,
  `email` varchar(80) DEFAULT NULL,
  `pager` varchar(80) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_hosts_services`
--

DROP TABLE IF EXISTS `nag_hosts_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_hosts_services` (
  `host_id` int(11) NOT NULL,
  `service_id` int(11) NOT NULL,
  `server_app_id` smallint(6) NOT NULL,
  PRIMARY KEY (`host_id`,`service_id`,`server_app_id`),
  KEY `service_id` (`service_id`),
  KEY `server_app_id` (`server_app_id`),
  CONSTRAINT `nag_hosts_services_ibfk_1` FOREIGN KEY (`host_id`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE,
  CONSTRAINT `nag_hosts_services_ibfk_2` FOREIGN KEY (`service_id`) REFERENCES `nag_services` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_hosts_services_ibfk_4` FOREIGN KEY (`server_app_id`) REFERENCES `app_definitions` (`AppID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_services`
--

DROP TABLE IF EXISTS `nag_services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_services` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `check_command_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  `max_check_attempts` int(11) NOT NULL,
  `check_interval` int(11) NOT NULL,
  `check_period_id` int(11) NOT NULL,
  `retry_interval` int(11) NOT NULL,
  `notification_interval` int(11) NOT NULL,
  `notification_period_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `check_command_id` (`check_command_id`),
  KEY `check_period_id` (`check_period_id`),
  KEY `notification_period_id` (`notification_period_id`),
  CONSTRAINT `nag_services_ibfk_1` FOREIGN KEY (`check_command_id`) REFERENCES `nag_check_commands` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_services_ibfk_2` FOREIGN KEY (`check_period_id`) REFERENCES `nag_time_periods` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_services_ibfk_3` FOREIGN KEY (`notification_period_id`) REFERENCES `nag_time_periods` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_services_arguments`
--

DROP TABLE IF EXISTS `nag_services_arguments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_services_arguments` (
  `service_id` int(11) NOT NULL,
  `command_argument_id` int(11) NOT NULL,
  `value` varchar(120) NOT NULL,
  PRIMARY KEY (`service_id`,`command_argument_id`),
  KEY `command_argument_id` (`command_argument_id`),
  CONSTRAINT `nag_services_arguments_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `nag_services` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_services_arguments_ibfk_2` FOREIGN KEY (`command_argument_id`) REFERENCES `nag_command_arguments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_services_contact_groups`
--

DROP TABLE IF EXISTS `nag_services_contact_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_services_contact_groups` (
  `service_id` int(11) NOT NULL,
  `contact_group_id` int(11) NOT NULL,
  PRIMARY KEY (`service_id`,`contact_group_id`),
  KEY `contact_group_id` (`contact_group_id`),
  CONSTRAINT `nag_services_contact_groups_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `nag_services` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_services_contact_groups_ibfk_2` FOREIGN KEY (`contact_group_id`) REFERENCES `nag_contact_groups` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_services_contacts`
--

DROP TABLE IF EXISTS `nag_services_contacts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_services_contacts` (
  `service_id` int(11) NOT NULL,
  `contact_id` int(11) NOT NULL,
  PRIMARY KEY (`service_id`,`contact_id`),
  KEY `contact_id` (`contact_id`),
  CONSTRAINT `nag_services_contacts_ibfk_1` FOREIGN KEY (`service_id`) REFERENCES `nag_services` (`id`) ON DELETE CASCADE,
  CONSTRAINT `nag_services_contacts_ibfk_2` FOREIGN KEY (`contact_id`) REFERENCES `nag_contacts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `nag_time_periods`
--

DROP TABLE IF EXISTS `nag_time_periods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nag_time_periods` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) NOT NULL,
  `alias` varchar(80) DEFAULT NULL,
  `sunday` varchar(32) DEFAULT NULL,
  `monday` varchar(32) DEFAULT NULL,
  `tuesday` varchar(32) DEFAULT NULL,
  `wednesday` varchar(32) DEFAULT NULL,
  `thursday` varchar(32) DEFAULT NULL,
  `friday` varchar(32) DEFAULT NULL,
  `saturday` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `net_default_ips`
--

DROP TABLE IF EXISTS `net_default_ips`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `net_default_ips` (
  `net_default_ip_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `net_default_id` int(10) unsigned NOT NULL,
  `vlan_id` int(11) NOT NULL,
  `priority` int(10) unsigned NOT NULL,
  PRIMARY KEY (`net_default_ip_id`),
  UNIQUE KEY `ip_key` (`net_default_id`,`vlan_id`,`priority`),
  KEY `vlan_id` (`vlan_id`),
  CONSTRAINT `net_default_ips_ibfk_1` FOREIGN KEY (`net_default_id`) REFERENCES `net_default_maps` (`net_default_id`) ON DELETE CASCADE,
  CONSTRAINT `net_default_ips_ibfk_2` FOREIGN KEY (`vlan_id`) REFERENCES `vlans` (`VlanID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `net_default_maps`
--

DROP TABLE IF EXISTS `net_default_maps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `net_default_maps` (
  `net_default_id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `environment_id` int(11) NOT NULL,
  `app_id` smallint(6) NOT NULL,
  `interface_name` varchar(10) NOT NULL,
  PRIMARY KEY (`net_default_id`),
  UNIQUE KEY `map_key` (`environment_id`,`app_id`,`interface_name`),
  KEY `app_id` (`app_id`),
  CONSTRAINT `net_default_maps_ibfk_1` FOREIGN KEY (`environment_id`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE,
  CONSTRAINT `net_default_maps_ibfk_2` FOREIGN KEY (`app_id`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `net_default_trunks`
--

DROP TABLE IF EXISTS `net_default_trunks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `net_default_trunks` (
  `net_default_id` int(10) unsigned NOT NULL,
  `vlan_id` int(11) NOT NULL,
  UNIQUE KEY `trunk_key` (`net_default_id`,`vlan_id`),
  KEY `vlan_id` (`vlan_id`),
  CONSTRAINT `net_default_trunks_ibfk_1` FOREIGN KEY (`net_default_id`) REFERENCES `net_default_maps` (`net_default_id`) ON DELETE CASCADE,
  CONSTRAINT `net_default_trunks_ibfk_2` FOREIGN KEY (`vlan_id`) REFERENCES `vlans` (`VlanID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `networkDevice`
--

DROP TABLE IF EXISTS `networkDevice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `networkDevice` (
  `NetworkID` int(11) NOT NULL AUTO_INCREMENT,
  `systemName` varchar(20) DEFAULT NULL,
  `model` varchar(50) DEFAULT NULL,
  `hardwareCode` varchar(20) DEFAULT NULL,
  `softwareCode` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`NetworkID`),
  UNIQUE KEY `systemName_UNIQUE` (`systemName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_device`
--

DROP TABLE IF EXISTS `ns_device`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_device` (
  `deviceID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `proto` varchar(6) NOT NULL,
  `host` varchar(32) NOT NULL,
  PRIMARY KEY (`deviceID`),
  UNIQUE KEY `proto_host` (`proto`,`host`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_monitor`
--

DROP TABLE IF EXISTS `ns_monitor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_monitor` (
  `monitorID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `monitor` varchar(32) NOT NULL,
  PRIMARY KEY (`monitorID`),
  UNIQUE KEY `monitor` (`monitor`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_service`
--

DROP TABLE IF EXISTS `ns_service`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_service` (
  `serviceID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `serviceName` varchar(64) NOT NULL,
  `proto` varchar(16) NOT NULL,
  `port` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`serviceID`),
  UNIQUE KEY `serviceName` (`serviceName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_service_binds`
--

DROP TABLE IF EXISTS `ns_service_binds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_service_binds` (
  `serviceID` int(10) unsigned NOT NULL,
  `monitorID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`serviceID`,`monitorID`),
  KEY `monitorID` (`monitorID`),
  KEY `serviceID` (`serviceID`),
  CONSTRAINT `ns_service_binds_ibfk_1` FOREIGN KEY (`monitorID`) REFERENCES `ns_monitor` (`monitorID`) ON DELETE CASCADE,
  CONSTRAINT `ns_service_binds_ibfk_2` FOREIGN KEY (`serviceID`) REFERENCES `ns_service` (`serviceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_service_max`
--

DROP TABLE IF EXISTS `ns_service_max`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_service_max` (
  `specID` int(11) NOT NULL,
  `serviceID` int(10) unsigned NOT NULL,
  `maxClient` int(10) unsigned NOT NULL DEFAULT '0',
  `maxReq` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`specID`,`serviceID`),
  KEY `serviceID` (`serviceID`),
  CONSTRAINT `ns_service_max_ibfk_1` FOREIGN KEY (`specID`) REFERENCES `host_specs` (`specID`) ON DELETE CASCADE,
  CONSTRAINT `ns_service_max_ibfk_2` FOREIGN KEY (`serviceID`) REFERENCES `ns_service` (`serviceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_service_params`
--

DROP TABLE IF EXISTS `ns_service_params`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_service_params` (
  `serviceID` int(10) unsigned NOT NULL,
  `param` varchar(32) NOT NULL,
  `value` varchar(128) NOT NULL,
  PRIMARY KEY (`serviceID`,`param`),
  KEY `serviceID` (`serviceID`),
  CONSTRAINT `ns_service_params_ibfk_1` FOREIGN KEY (`serviceID`) REFERENCES `ns_service` (`serviceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_vip`
--

DROP TABLE IF EXISTS `ns_vip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_vip` (
  `vipID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `vserver` varchar(64) NOT NULL,
  `deviceID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`vipID`),
  UNIQUE KEY `device_vserver` (`deviceID`,`vserver`),
  CONSTRAINT `ns_vip_ibfk_1` FOREIGN KEY (`deviceID`) REFERENCES `ns_device` (`deviceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_vip_binds`
--

DROP TABLE IF EXISTS `ns_vip_binds`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_vip_binds` (
  `net_default_ip_id` int(10) unsigned NOT NULL,
  `vipID` int(10) unsigned NOT NULL,
  `serviceID` int(10) unsigned NOT NULL,
  PRIMARY KEY (`vipID`,`serviceID`,`net_default_ip_id`),
  KEY `vipID` (`vipID`),
  KEY `serviceID` (`serviceID`),
  KEY `net_default_ip_id_foreign_key` (`net_default_ip_id`),
  CONSTRAINT `net_default_ip_id_foreign_key` FOREIGN KEY (`net_default_ip_id`) REFERENCES `net_default_ips` (`net_default_ip_id`) ON DELETE CASCADE,
  CONSTRAINT `ns_vip_binds_ibfk_2` FOREIGN KEY (`vipID`) REFERENCES `ns_vip` (`vipID`) ON DELETE CASCADE,
  CONSTRAINT `ns_vip_binds_ibfk_3` FOREIGN KEY (`serviceID`) REFERENCES `ns_service` (`serviceID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ns_weight`
--

DROP TABLE IF EXISTS `ns_weight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ns_weight` (
  `vipID` int(10) unsigned NOT NULL,
  `specID` int(11) NOT NULL,
  `weight` tinyint(3) unsigned NOT NULL,
  PRIMARY KEY (`vipID`,`specID`),
  KEY `specID` (`specID`),
  CONSTRAINT `ns_weight_ibfk_1` FOREIGN KEY (`vipID`) REFERENCES `ns_vip` (`vipID`) ON DELETE CASCADE,
  CONSTRAINT `ns_weight_ibfk_2` FOREIGN KEY (`specID`) REFERENCES `host_specs` (`specID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `package_definitions`
--

DROP TABLE IF EXISTS `package_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `package_definitions` (
  `pkg_def_id` int(11) NOT NULL AUTO_INCREMENT,
  `deploy_type` varchar(30) NOT NULL,
  `validation_type` varchar(15) NOT NULL,
  `pkg_name` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  `arch` enum('i386','x86_64','noarch') NOT NULL DEFAULT 'noarch',
  `build_type` enum('developer','hudson','jenkins') NOT NULL DEFAULT 'jenkins',
  `build_host` varchar(255) NOT NULL,
  `env_specific` tinyint(1) NOT NULL DEFAULT '0',
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`pkg_def_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `package_locations`
--

DROP TABLE IF EXISTS `package_locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `package_locations` (
  `pkgLocationID` int(11) NOT NULL AUTO_INCREMENT,
  `project_type` enum('application','kafka-config','tagconfig') NOT NULL DEFAULT 'application',
  `pkg_type` varchar(255) NOT NULL,
  `pkg_name` varchar(255) NOT NULL,
  `app_name` varchar(255) NOT NULL,
  `path` varchar(255) NOT NULL,
  `arch` enum('i386','x86_64','noarch') NOT NULL DEFAULT 'noarch',
  `build_host` varchar(30) NOT NULL,
  `environment` tinyint(1) NOT NULL,
  PRIMARY KEY (`pkgLocationID`),
  UNIQUE KEY `pkg_name` (`pkg_name`),
  UNIQUE KEY `app_name` (`app_name`),
  UNIQUE KEY `path` (`path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `package_names`
--

DROP TABLE IF EXISTS `package_names`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `package_names` (
  `pkg_name_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `pkg_def_id` int(11) NOT NULL,
  PRIMARY KEY (`pkg_name_id`),
  UNIQUE KEY `name_pkg_def_id` (`name`,`pkg_def_id`),
  KEY `pkg_def_id` (`pkg_def_id`),
  CONSTRAINT `package_names_ibfk_1` FOREIGN KEY (`pkg_def_id`) REFERENCES `package_definitions` (`pkg_def_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `packages`
--

DROP TABLE IF EXISTS `packages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `packages` (
  `package_id` int(11) NOT NULL AUTO_INCREMENT,
  `pkg_def_id` int(11) NOT NULL,
  `pkg_name` varchar(255) NOT NULL,
  `version` varchar(63) NOT NULL,
  `revision` varchar(63) NOT NULL,
  `status` enum('completed','failed','pending','processing','removed') NOT NULL,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `creator` varchar(255) NOT NULL,
  `builder` enum('developer','hudson','jenkins') NOT NULL DEFAULT 'developer',
  `project_type` enum('application','kafka-config','tagconfig') NOT NULL DEFAULT 'application',
  PRIMARY KEY (`package_id`),
  UNIQUE KEY `unique_package` (`pkg_name`,`version`,`revision`,`builder`) USING BTREE,
  KEY `pkg_def_id` (`pkg_def_id`),
  CONSTRAINT `packages_ibfk_1` FOREIGN KEY (`pkg_def_id`) REFERENCES `package_definitions` (`pkg_def_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ports`
--

DROP TABLE IF EXISTS `ports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ports` (
  `PortID` int(11) NOT NULL AUTO_INCREMENT,
  `NetworkID` int(11) DEFAULT NULL,
  `portNumber` varchar(20) DEFAULT NULL,
  `description` varchar(50) DEFAULT NULL,
  `speed` varchar(20) DEFAULT NULL,
  `duplex` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`PortID`),
  UNIQUE KEY `NetworkID_portNumber` (`NetworkID`,`portNumber`),
  KEY `NetworkID` (`NetworkID`),
  CONSTRAINT `ports_ibfk_1` FOREIGN KEY (`NetworkID`) REFERENCES `networkDevice` (`NetworkID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_package`
--

DROP TABLE IF EXISTS `project_package`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_package` (
  `project_id` int(11) NOT NULL,
  `pkg_def_id` int(11) NOT NULL,
  `app_id` smallint(6) NOT NULL,
  PRIMARY KEY (`project_id`,`pkg_def_id`,`app_id`),
  KEY `pkg_def_id` (`pkg_def_id`),
  KEY `app_id` (`app_id`),
  CONSTRAINT `project_package_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`project_id`) ON DELETE CASCADE,
  CONSTRAINT `project_package_ibfk_2` FOREIGN KEY (`pkg_def_id`) REFERENCES `package_definitions` (`pkg_def_id`) ON DELETE CASCADE,
  CONSTRAINT `project_package_ibfk_3` FOREIGN KEY (`app_id`) REFERENCES `app_definitions` (`AppID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `projects`
--

DROP TABLE IF EXISTS `projects`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `projects` (
  `project_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`project_id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `serviceEvent`
--

DROP TABLE IF EXISTS `serviceEvent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `serviceEvent` (
  `ServiceID` int(11) NOT NULL AUTO_INCREMENT,
  `HostID` int(11) DEFAULT NULL,
  `user` varchar(20) DEFAULT NULL,
  `serviceStatus` varchar(100) DEFAULT NULL,
  `powerStatus` varchar(10) DEFAULT NULL,
  `vendorTicket` varchar(20) DEFAULT NULL,
  `comments` text,
  `serviceDate` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`ServiceID`),
  KEY `HostID` (`HostID`),
  CONSTRAINT `serviceEvent_ibfk_1` FOREIGN KEY (`HostID`) REFERENCES `hosts` (`HostID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `subnet`
--

DROP TABLE IF EXISTS `subnet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `subnet` (
  `SubnetID` int(11) NOT NULL AUTO_INCREMENT,
  `VlanID` int(11) DEFAULT NULL,
  `ipAddress` varchar(15) DEFAULT NULL,
  `netmask` varchar(15) DEFAULT NULL,
  `gateway` varchar(15) DEFAULT NULL,
  `ZoneID` int(11) DEFAULT NULL,
  PRIMARY KEY (`SubnetID`),
  UNIQUE KEY `ipAddress` (`ipAddress`),
  KEY `VlanID` (`VlanID`),
  KEY `ZoneID` (`ZoneID`),
  CONSTRAINT `subnet_ibfk_1` FOREIGN KEY (`VlanID`) REFERENCES `vlans` (`VlanID`) ON DELETE CASCADE,
  CONSTRAINT `subnet_ibfk_2` FOREIGN KEY (`ZoneID`) REFERENCES `zones` (`ZoneID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vlans`
--

DROP TABLE IF EXISTS `vlans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `vlans` (
  `VlanID` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(20) DEFAULT NULL,
  `environmentID` int(11) DEFAULT NULL,
  `description` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`VlanID`),
  KEY `environmentID` (`environmentID`),
  CONSTRAINT `vlans_ibfk_1` FOREIGN KEY (`environmentID`) REFERENCES `environments` (`environmentID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zones`
--

DROP TABLE IF EXISTS `zones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `zones` (
  `ZoneID` int(11) NOT NULL AUTO_INCREMENT,
  `zoneName` varchar(30) DEFAULT NULL,
  `mxPriority` int(11) DEFAULT NULL,
  `mxHostID` varchar(30) DEFAULT NULL,
  `nsPriority` int(11) DEFAULT NULL,
  `nameserver` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`ZoneID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-08-04 17:30:58
