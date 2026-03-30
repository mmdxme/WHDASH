-- --------------------------------------------------------
-- Warehouse Dashboard - SQLite Database Schema
-- --------------------------------------------------------

-- --------------------------------------------------------
-- Table structure for table `companies` (Subsidiaries)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `companies` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO `companies` (`name`) VALUES ('Holding Company'), ('SDAD'), ('AFRA'), ('Carmania');

-- --------------------------------------------------------
-- Table structure for table `roles`
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `roles` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `role_name` TEXT NOT NULL,
  `company_id` INTEGER DEFAULT NULL,
  `can_edit_stock` INTEGER DEFAULT 0,
  `can_manage_users` INTEGER DEFAULT 0,
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON DELETE CASCADE
);

INSERT INTO `roles` (`role_name`, `company_id`, `can_edit_stock`, `can_manage_users`) 
VALUES ('Global Admin', NULL, 1, 1);

-- --------------------------------------------------------
-- Table structure for table `users`
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `username` TEXT NOT NULL UNIQUE,
  `email` TEXT NOT NULL UNIQUE,
  `password` TEXT NOT NULL,
  `role_id` INTEGER NOT NULL,
  `profile_pic` TEXT DEFAULT 'default.png',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)
);

-- Seed admin user (PBKDF2 SHA256 format for Werkzeug)
-- Password is 'password'
INSERT INTO `users` (`username`, `email`, `password`, `role_id`) 
VALUES ('admin', 'admin@warehouse.local', 'scrypt:32768:8:1$hU6BqZ043w2mH1d8$71676d05acaf9f7de688a4427b0b6da10c7336edff7c26dedfd760882772dc8c8f5f00e99dcb75eefee4b3cb15bfd42ca3a62ae217b1297e2f5ff57a917e7041', 1);

-- --------------------------------------------------------
-- Taxonomies
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS `categories` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS `brands` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT NOT NULL,
  `type` TEXT NOT NULL DEFAULT 'Genuine'
);

CREATE TABLE IF NOT EXISTS `statuses` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT NOT NULL
);

-- --------------------------------------------------------
-- Master Parts
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `parts` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `part_number` TEXT NOT NULL UNIQUE,
  `description` TEXT,
  `weight` REAL DEFAULT NULL,
  `dimension` TEXT DEFAULT NULL,
  `volume` REAL DEFAULT NULL,
  `category_id` INTEGER NULL,
  `brand_id` INTEGER NULL,
  `status_id` INTEGER NULL,
  `reorder_point` INTEGER DEFAULT 0,
  `cost_price` REAL DEFAULT 0.00,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`brand_id`) REFERENCES `brands`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`status_id`) REFERENCES `statuses`(`id`) ON DELETE SET NULL
);

-- --------------------------------------------------------
-- Inventory (Sub-Locations)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `inventory` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `part_id` INTEGER NOT NULL,
  `company_id` INTEGER NOT NULL,
  `zone` TEXT DEFAULT NULL,
  `quantity` INTEGER NOT NULL DEFAULT 0,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (`part_id`, `company_id`),
  FOREIGN KEY (`part_id`) REFERENCES `parts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON DELETE CASCADE
);

-- --------------------------------------------------------
-- Movements History
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS `movements` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `part_id` INTEGER NOT NULL,
  `company_id` INTEGER NOT NULL,
  `user_id` INTEGER DEFAULT NULL,
  `movement_type` TEXT NOT NULL,
  `quantity` INTEGER NOT NULL,
  `reference` TEXT DEFAULT NULL,
  `movement_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`part_id`) REFERENCES `parts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL
);
