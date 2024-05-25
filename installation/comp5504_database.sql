-- Create the database
CREATE DATABASE IF NOT EXISTS comp5504_users;
USE comp5504_users;

-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (username)
);

