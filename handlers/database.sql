CREATE DATABASE dbnm; 					-- create the database with name DB_NAME
CREATE USER 'usr'@'host' IDENTIFIED BY 'pswd'; 		-- add user and password for the host
GRANT ALL PRIVILEGES ON dbnm.* TO 'usr'@'host'; 

USE dbnm; 

CREATE TABLE weather_data(
    `Station_ID` VARCHAR(4) NOT NULL,   -- unique station identifier
    `Date` DATE NOT NULL,               -- date of sampling
    `Time` TIME NOT NULL,               -- exact time of sampling
    `Temperature` FLOAT NOT NULL,	-- air temperature in *C
    `Humidity` FLOAT NOT NULL,		-- air relative humidity in %
    `Pressure` FLOAT NOT NULL,		-- barometric pressure in hPa
    `Wind_Speed` FLOAT NOT NULL, 	-- wind speed in km/h
    `Wind_Direction` FLOAT NOT NULL,    -- wind direction in deg 
    `Rainfall` FLOAT NOT NULL, 		-- rainfall rate in mm
);
