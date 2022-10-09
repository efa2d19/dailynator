-- initial migration

CREATE TABLE channels (
    channel_id VARCHAR(20) PRIMARY KEY,
    team_id VARCHAR(20) NOT NULL,
    channel_name VARCHAR NOT NULL,
    cron VARCHAR,
    cron_tz VARCHAR
);

CREATE TABLE users (
    user_id VARCHAR(20) PRIMARY KEY,
    daily_status BOOLEAN NOT NULL default FALSE,
    q_idx INTEGER,
    main_channel_id VARCHAR(20) NOT NULL,
    real_name VARCHAR NOT NULL,
    FOREIGN KEY (main_channel_id) REFERENCES channels (channel_id)
);

CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    channel_id VARCHAR(20) NOT NULL,
    body VARCHAR not null,
    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
);

CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    question_id INTEGER NOT NULL,
    answer VARCHAR NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (question_id) REFERENCES questions (id)
);

CREATE TABLE daily (
    thread_ts VARCHAR(16) PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);