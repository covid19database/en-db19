CREATE TABLE IF NOT EXISTS reported_keys (
    TEK          BYTEA,
    ENIN         TIMESTAMP NOT NULL,
    HAK          BYTEA NOT NULL,
    uploaded_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY(TEK, ENIN)
);
CREATE INDEX enin_idx ON reported_keys(ENIN);
CREATE INDEX hak_idx ON reported_keys(HAK);

CREATE TABLE IF NOT EXISTS health_authorities (
    HAK          BYTEA PRIMARY KEY,
    name         TEXT NOT NULL
);

INSERT INTO health_authorities(HAK, name) VALUES (decode('da250d7fbffca634bf9b38e9430508bb', 'hex'), 'A');
INSERT INTO health_authorities(HAK, name) VALUES (decode('577429c2be1353b08809dc28c0bf6bc0', 'hex'), 'B');
