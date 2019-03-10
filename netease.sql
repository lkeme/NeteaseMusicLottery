/*
 Navicat Premium Data Transfer

 Source Server         : 本地服务器
 Source Server Type    : MySQL
 Source Server Version : 50724
 Source Host           : localhost:3306
 Source Schema         : netease

 Target Server Type    : MySQL
 Target Server Version : 50724
 File Encoding         : 65001

 Date: 10/03/2019 18:32:02
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for event_information
-- ----------------------------
DROP TABLE IF EXISTS `event_information`;
CREATE TABLE `event_information`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `uid` int(11) NULL DEFAULT NULL,
  `event_msg` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `event_id` bigint(20) NULL DEFAULT NULL,
  `lottery_id` int(11) NULL DEFAULT NULL,
  `lottery_time` bigint(20) NULL DEFAULT NULL,
  `crt_time` bigint(20) NULL DEFAULT NULL,
  `is_reposted` int(255) NULL DEFAULT NULL,
  `is_deleted` int(255) NULL DEFAULT NULL,
  `pre_event_id` bigint(20) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 50 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
