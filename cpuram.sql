DROP table IF EXISTS metrics;
DROP table IF EXISTS machines;

create table machines (
    token VARCHAR(32) PRIMARY KEY NOT NULL,
    name  VARCHAR(256) NOT NULL
);

create table metrics (
    machine VARCHAR(32) REFERENCES machines (token) NOT NULL,
    cpu REAL NOT NULL,
    ram REAL NOT NULL,
    ts INTEGER NOT NULL
);

PRAGMA journal_mode=wal;
