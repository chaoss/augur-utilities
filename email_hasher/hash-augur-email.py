#SPDX-License-Identifier: MIT
""" 
    _email_columns_
    cmt_author_raw_email
    cmt_author_email
    cmt_committer_raw_email
    cmt_committer_email
    
    ## Decode: 

        SELECT convert_from(pgp_sym_decrypt(decode(your_text_column, 'base64'), 'your_secret_key'), 'UTF8') AS decrypted_text
        FROM your_table;
"""
# -- Enable the pgcrypto extension if not already enabled.
import psycopg2
import json
import sys
import traceback
from email_hasher.helpers import encrypt_emails

# Read database connection details from JSON file
def read_db_config(file_path="db.config.json"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading database config from {file_path}: {e}")
        return None

# Connect to PostgreSQL database
def connect_to_db(db_config):
    try:
        conn = psycopg2.connect(
            dbname=db_config["database_name"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"]
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def main(secret_key):
    db_config = read_db_config()
    if db_config is None:
        print("Database configuration could not be loaded. Exiting.")
        return

    conn = connect_to_db(db_config)
    if conn is None:
        print("Database connection failed. Exiting.")
        return

    cursor = conn.cursor()
    
    encrypt_emails(conn, cursor, secret_key)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash-augur-email.py <secret_key>")
    else:
        secret_key = sys.argv[1]
        main(secret_key)