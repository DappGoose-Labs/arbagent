#!/usr/bin/env python3
# db_config.py
import psycopg2
import logging
import json
from psycopg2 import sql
from psycopg2.extras import Json

logger = logging.getLogger("db_config")

# Database connection parameters (consider using environment variables for security)
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "arbitrage_db"
DB_USER = "arbitrage_user"
DB_PASSWORD = "arbitrage_password"

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info(f"Successfully connected to database '{DB_NAME}' on {DB_HOST}:{DB_PORT}")
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        # Consider more robust error handling or fallback
        # Maybe try creating the database if it doesn't exist?
        # For now, just raise the exception
        raise

def init_db(conn):
    """Initializes the database schema if tables don't exist."""
    try:
        with conn.cursor() as cur:
            # Create trades table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    trade_type VARCHAR(50),
                    dex_pair VARCHAR(255),
                    token_pair VARCHAR(100),
                    amount_in DECIMAL,
                    amount_out DECIMAL,
                    profit_usd DECIMAL,
                    gas_cost_usd DECIMAL,
                    tx_hash VARCHAR(255) UNIQUE,
                    status VARCHAR(50),
                    details JSONB
                );
            """)
            logger.info("Checked/Created 'trades' table.")

            # Create opportunities table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    opportunity_type VARCHAR(50),
                    details JSONB,
                    estimated_profit_usd DECIMAL,
                    status VARCHAR(50) DEFAULT 'detected' -- e.g., detected, simulated, executed, failed
                );
            """)
            logger.info("Checked/Created 'opportunities' table.")

            # Add indexes for potentially faster lookups
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_trades_tx_hash ON trades(tx_hash);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);")
            logger.info("Checked/Created indexes.")

        conn.commit()
        logger.info("Database schema initialization complete.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database schema: {e}")
        raise

def log_trade(conn, trade_data: dict):
    """Logs a completed trade to the database."""
    sql_insert = sql.SQL("""
        INSERT INTO trades (trade_type, dex_pair, token_pair, amount_in, amount_out, profit_usd, gas_cost_usd, tx_hash, status, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tx_hash) DO NOTHING;
    """)
    try:
        with conn.cursor() as cur:
            cur.execute(sql_insert, (
                trade_data.get('trade_type'),
                trade_data.get('dex_pair'),
                trade_data.get('token_pair'),
                trade_data.get('amount_in'),
                trade_data.get('amount_out'),
                trade_data.get('profit_usd'),
                trade_data.get('gas_cost_usd'),
                trade_data.get('tx_hash'),
                trade_data.get('status'),
                Json(trade_data.get('details', {}))
            ))
        conn.commit()
        logger.debug(f"Logged trade {trade_data.get('tx_hash')}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error logging trade {trade_data.get('tx_hash')}: {e}")

def log_opportunity(conn, opportunity_data: dict):
    """Logs a detected arbitrage opportunity."""
    sql_insert = sql.SQL("""
        INSERT INTO opportunities (opportunity_type, details, estimated_profit_usd, status)
        VALUES (%s, %s, %s, %s) RETURNING id;
    """)
    try:
        with conn.cursor() as cur:
            cur.execute(sql_insert, (
                opportunity_data.get('opportunity_type'),
                Json(opportunity_data.get('details', {})),
                opportunity_data.get('estimated_profit_usd'),
                opportunity_data.get('status', 'detected')
            ))
            opportunity_id = cur.fetchone()[0]
        conn.commit()
        logger.debug(f"Logged opportunity ID: {opportunity_id}")
        return opportunity_id
    except Exception as e:
        conn.rollback()
        logger.error(f"Error logging opportunity: {e}")
        return None

def update_opportunity_status(conn, opportunity_id: int, status: str):
    """Updates the status of an opportunity."""
    sql_update = sql.SQL("UPDATE opportunities SET status = %s WHERE id = %s;")
    try:
        with conn.cursor() as cur:
            cur.execute(sql_update, (status, opportunity_id))
        conn.commit()
        logger.debug(f"Updated opportunity {opportunity_id} status to {status}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating opportunity {opportunity_id} status: {e}")


# Example of running initialization directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Running DB initialization directly...")
    connection = None
    try:
        connection = get_db_connection()
        if connection:
            init_db(connection)
            logger.info("Database initialization script finished.")
        else:
            logger.error("Failed to get database connection.")
    except Exception as e:
        logger.error(f"An error occurred during direct DB initialization: {e}")
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed.")