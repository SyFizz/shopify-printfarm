-- Database Client 8.2.5
-- Host: 127.0.0.1 Port: 3306 Database: null 
-- Dump is still an early version, please use the dumped SQL with caution

CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            );
INSERT INTO products(id,name,description) VALUES(1,'CableCatch',''),(2,'FlexiRex',''),(3,'GyroToy',''),(4,'Infinity Cube',''),(5,'OctoTwist',''),(6,'StarNest',''),(7,'SpinRing',''),(8,'ClickyPaw','');