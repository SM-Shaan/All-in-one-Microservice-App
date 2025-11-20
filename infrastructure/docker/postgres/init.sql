-- Initialize databases for different services
-- This script runs when PostgreSQL container starts for the first time

-- Create databases for each service that uses PostgreSQL
CREATE DATABASE users;
CREATE DATABASE inventory;
CREATE DATABASE payments;
CREATE DATABASE cart;
CREATE DATABASE admin;

-- Grant privileges (optional, but good practice)
GRANT ALL PRIVILEGES ON DATABASE users TO postgres;
GRANT ALL PRIVILEGES ON DATABASE inventory TO postgres;
GRANT ALL PRIVILEGES ON DATABASE payments TO postgres;
GRANT ALL PRIVILEGES ON DATABASE cart TO postgres;
GRANT ALL PRIVILEGES ON DATABASE admin TO postgres;

-- Log success
\echo 'Databases created successfully!'
