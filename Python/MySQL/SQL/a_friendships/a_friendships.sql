-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema friendships
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema friendships
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `friendships` DEFAULT CHARACTER SET utf8 ;
USE `friendships` ;

-- -----------------------------------------------------
-- Table `friendships`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `friendships`.`users` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(45) NULL DEFAULT NULL,
  `last_name` VARCHAR(45) NULL DEFAULT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `friendships`.`friendships`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `friendships`.`friendships` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL,
  `friend_id` INT(11) NOT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `fk_friendships_users_idx` (`user_id` ASC),
  INDEX `fk_friendships_users1_idx` (`friend_id` ASC),
  CONSTRAINT `fk_friendships_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `friendships`.`users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_friendships_users1`
    FOREIGN KEY (`friend_id`)
    REFERENCES `friendships`.`users` (`id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

	INSERT INTO users (first_name, last_name, created_at, updated_at)
	VALUES 
	('Chris', 'Baker', now(), now()),
	('Diana', 'Smith', now(), now()),
	('James', 'Johnson', now(), now()),
	('Jessica', 'Davidson', now(), now());


	INSERT INTO friendships (user_id, friend_id, created_at, updated_at)
	VALUES
	((SELECT id from users WHERE first_name='Chris' AND last_name='Baker'), (SELECT id from users WHERE first_name='James' AND last_name='Johnson'), now(), now()),
	((SELECT id from users WHERE first_name='Chris' AND last_name='Baker'), (SELECT id from users WHERE first_name='Diana' AND last_name='Smith'), now(), now()),
	((SELECT id from users WHERE first_name='Jessica' AND last_name='Davidson'), (SELECT id from users WHERE first_name='James' AND last_name='Johnson'), now(), now()),
	((SELECT id from users WHERE first_name='James' AND last_name='Johnson'), (SELECT id from users WHERE first_name='Jessica' AND last_name='Davidson'), now(), now()),
    ((SELECT id from users WHERE first_name='Diana' AND last_name='Smith'), (SELECT id from users WHERE first_name='Chris' AND last_name='Baker'), now(), now()),
    ((SELECT id from users WHERE first_name='James' AND last_name='Johnson'), (SELECT id from users WHERE first_name='Chris' AND last_name='Baker'), now(), now());



SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;


