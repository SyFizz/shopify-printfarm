-- Database Client 8.2.5
-- Host: 127.0.0.1 Port: 3306 Database: null 
-- Dump is still an early version, please use the dumped SQL with caution

CREATE TABLE product_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            component_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1, color_constraint TEXT,
            UNIQUE(product_name, component_name)
        );
INSERT INTO product_components(id,product_name,component_name,quantity,color_constraint) VALUES(1,'CableCatch','CableCatch',1,'same_as_main'),(2,'FlexiRex','FlexiRex',1,'same_as_main'),(3,'GyroToy','GyroToy',1,'same_as_main'),(4,'Infinity Cube','Infinity Cube',1,'same_as_main'),(6,'OctoTwist','OctoTwist',1,'same_as_main'),(7,'StarNest','StarNest',1,'same_as_main'),(8,'SpinRing','SpinRing - Left',1,'same_as_main'),(9,'SpinRing','SpinRing - Right',1,'same_as_main'),(10,'SpinRing','SpinRing - Montant',2,'fixed:Noir'),(11,'ClickyPaw','ClickyPaw - Corps',1,'same_as_main'),(12,'ClickyPaw','ClickyPaw - Petit clicker',4,'fixed:Sakura Pink'),(14,'ClickyPaw','ClickyPaw - Clicker central',1,'fixed:Sakura Pink'),(15,'ClickyPaw','MX Switch',6,null);