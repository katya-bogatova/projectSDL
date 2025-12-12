CREATE DATABASE db
    WITH OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'ru_RU.UTF-8'
    LC_CTYPE = 'ru_RU.UTF-8'
    TEMPLATE = template0;

CREATE ROLE myuser WITH LOGIN PASSWORD 'pass';

GRANT CONNECT ON DATABASE db TO myuser;

\connect db

GRANT USAGE ON SCHEMA public TO myuser;