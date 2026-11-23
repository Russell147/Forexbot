-- Generated from SQLAlchemy models (PostgreSQL). Prefer Alembic migrations in production.

CREATE TABLE bot_logs (
	id SERIAL NOT NULL, 
	level VARCHAR(10) NOT NULL, 
	message TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE bot_settings (
	id SERIAL NOT NULL, 
	desired_state VARCHAR(12) NOT NULL, 
	actual_state VARCHAR(14) NOT NULL, 
	emergency_close_done BOOLEAN NOT NULL, 
	heartbeat TIMESTAMP WITH TIME ZONE, 
	mt5_connected BOOLEAN NOT NULL, 
	account_login BIGINT, 
	account_type VARCHAR(10) NOT NULL, 
	balance FLOAT NOT NULL, 
	equity FLOAT NOT NULL, 
	peak_equity FLOAT NOT NULL, 
	day_start_equity FLOAT NOT NULL, 
	day_start_date VARCHAR(10) NOT NULL, 
	telegram_enabled BOOLEAN NOT NULL, 
	ai_enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	message TEXT NOT NULL, 
	sent BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE performance (
	id SERIAL NOT NULL, 
	ts TIMESTAMP WITH TIME ZONE NOT NULL, 
	balance FLOAT NOT NULL, 
	equity FLOAT NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE risk_settings (
	id SERIAL NOT NULL, 
	risk_per_trade FLOAT NOT NULL, 
	max_daily_loss FLOAT NOT NULL, 
	max_drawdown FLOAT NOT NULL, 
	max_open_positions INTEGER NOT NULL, 
	min_risk_reward FLOAT NOT NULL, 
	max_spread_pips FLOAT NOT NULL, 
	session VARCHAR(30) NOT NULL, 
	trailing_enabled BOOLEAN NOT NULL, 
	trailing_atr_mult FLOAT NOT NULL, 
	close_on_emergency BOOLEAN NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE strategies (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	timeframes VARCHAR(50) NOT NULL, 
	params JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE trades (
	id SERIAL NOT NULL, 
	ticket BIGINT, 
	symbol VARCHAR(12) NOT NULL, 
	type VARCHAR(4) NOT NULL, 
	volume FLOAT NOT NULL, 
	entry_price FLOAT NOT NULL, 
	stop_loss FLOAT NOT NULL, 
	take_profit FLOAT NOT NULL, 
	exit_price FLOAT, 
	profit FLOAT NOT NULL, 
	status VARCHAR(8) NOT NULL, 
	strategy VARCHAR(50) NOT NULL, 
	close_reason VARCHAR(50), 
	opened_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (ticket)
);

CREATE TABLE trading_pairs (
	id SERIAL NOT NULL, 
	symbol VARCHAR(12) NOT NULL, 
	description VARCHAR(80) NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (symbol)
);

CREATE TABLE trading_signals (
	id SERIAL NOT NULL, 
	symbol VARCHAR(12) NOT NULL, 
	strategy VARCHAR(50) NOT NULL, 
	timeframe VARCHAR(5) NOT NULL, 
	direction VARCHAR(4) NOT NULL, 
	status VARCHAR(12) NOT NULL, 
	reason TEXT NOT NULL, 
	ai_note TEXT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	is_admin BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE trading_accounts (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	login BIGINT NOT NULL, 
	server VARCHAR(100) NOT NULL, 
	broker VARCHAR(100) NOT NULL, 
	account_type VARCHAR(10) NOT NULL, 
	currency VARCHAR(8) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

