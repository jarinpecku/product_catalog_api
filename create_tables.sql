CREATE DATABASE product_catalog_db;

USE product_catalog_db;

CREATE TABLE `service` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `url` VARCHAR(100) NOT NULL COMMENT 'microservice base url',
    `access_token` VARCHAR(100) NOT NULL COMMENT 'microservice access token',
    PRIMARY KEY (`id`)
) COMMENT='registered microservices';

CREATE TABLE `product` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `service_id` INT UNSIGNED NOT NULL COMMENT 'id of service used for product registration',
  `name` VARCHAR(100) NOT NULL COMMENT 'Name of the product',
  `description` TEXT NOT NULL COMMENT 'Product description',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`service_id`) REFERENCES `service`(`id`) ON DELETE CASCADE,
  UNIQUE KEY (`name`)
) COMMENT='table of unique products';

CREATE TABLE `offer` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `product_id` INT UNSIGNED NOT NULL COMMENT 'multiple offers belongs to unique product',
  `foreign_id` INT UNSIGNED NOT NULL COMMENT 'id form offers microservice',
  `items_in_stock` INT NOT NULL COMMENT 'number of items in stock',
  PRIMARY KEY (`id`),
  FOREIGN KEY (`product_id`) REFERENCES `product`(`id`) ON DELETE CASCADE,
  UNIQUE KEY (`product_id`, `foreign_id`)
) COMMENT='product offers';

CREATE TABLE `price` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `offer_id` INT UNSIGNED NOT NULL COMMENT 'multiple prices belongs to unique offer',
    `price` INT NOT NULL COMMENT 'price of the offer, a unit should be specified, lets say it is EUR, I think it should be FLOAT but the given data model says INT',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'price creation time',
    PRIMARY KEY (`id`),
    FOREIGN KEY (`offer_id`) REFERENCES `offer`(`id`) ON DELETE CASCADE
) COMMENT='offer prices';