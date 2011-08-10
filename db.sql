CREATE DATABASE IF NOT EXISTS thrifty;
USE thrifty;
CREATE TABLE IF NOT EXISTS user (
        _id BIGINT UNSIGNED NOT NULL,
        _email VARCHAR(100) NOT NULL,
        _openid VARCHAR(10000),
        _firstName VARCHAR(100),
        _lastName VARCHAR(100),
        _cellPhone VARCHAR(100),
        _memberSince INT UNSIGNED NOT NULL,
        _lastSeen INT UNSIGNED NOT NULL,
        _type ENUM('manual', 'auto') NOT NULL,
        _cookie BIGINT UNSIGNED NOT NULL,
        CONSTRAINT PRIMARY KEY USING BTREE (_id),
        INDEX _idx_email USING BTREE (_email),
        CONSTRAINT UNIQUE INDEX _idx_cookie USING BTREE (_cookie)
        ) ENGINE = InnoDB;
CREATE TABLE IF NOT EXISTS bill (
        _id BIGINT UNSIGNED NOT NULL,
        _amount FLOAT UNSIGNED ZEROFILL NOT NULL,
        _category VARCHAR(50) NOT NULL,
        _date INT UNSIGNED NOT NULL,
        _reportedAt INT UNSIGNED NOT NULL,
        _reportedBy BIGINT UNSIGNED NOT NULL,
        _type ENUM('individual', 'shared', 'itemized') NOT NULL,
        _participants VARCHAR(10000) NOT NULL,
        _tags VARCHAR(1000),
        _description VARCHAR(1000),
        CONSTRAINT PRIMARY KEY USING BTREE (_id),
        INDEX _idx_cat USING BTREE (_category),
        INDEX _idx_reporter USING BTREE (_reportedBy),
        CONSTRAINT FOREIGN KEY _cons_fkey_reporter (_reportedBy)
            REFERENCES user (_id)
        ) ENGINE = InnoDB;
CREATE TABLE IF NOT EXISTS expense (
        _billId BIGINT UNSIGNED NOT NULL,
        _userId BIGINT UNSIGNED NOT NULL,
        _amount FLOAT UNSIGNED ZEROFILL NOT NULL,
        _date INT UNSIGNED NOT NULL,
        _category VARCHAR(50) NOT NULL,
        _tags VARCHAR(1000),
        CONSTRAINT FOREIGN KEY _cons_fkey_bill_id (_billId)
            REFERENCES bill (_id),
        INDEX _idx_userExpense USING BTREE (_userId),
        CONSTRAINT FOREIGN KEY _cons_fkey_userId (_userId)
            REFERENCES user (_id)
        ) ENGINE = InnoDB;
CREATE TABLE IF NOT EXISTS category (
        _category VARCHAR(50) NOT NULL,
        _addedBy BIGINT UNSIGNED NOT NULL,
        _addedAt INT UNSIGNED NOT NULL,
        CONSTRAINT PRIMARY KEY USING BTREE (_category),
        CONSTRAINT FOREIGN KEY _cons_fkey_addedBy (_addedBy)
            REFERENCES user (_id)
        ) ENGINE = InnoDB;
CREATE TABLE IF NOT EXISTS tag (
        _tag VARCHAR(50) NOT NULL,
        _addedBy BIGINT UNSIGNED NOT NULL,
        _addedAt INT UNSIGNED NOT NULL,
        CONSTRAINT PRIMARY KEY USING BTREE (_tag),
        CONSTRAINT FOREIGN KEY _cons_fkey_addedBy (_addedBy)
            REFERENCES user (_id)
        ) ENGINE = InnoDB;
