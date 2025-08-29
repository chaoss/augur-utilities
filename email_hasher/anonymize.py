#SPDX-License-Identifier: MIT
import sys
from db_tools import encrypt_columns, read_db_config, connect_to_db, wait_for_port, delete_rows

def main(secret_key):
    db_config = read_db_config()
    if db_config is None:
        print("Database configuration could not be loaded. Exiting.")
        return

    wait_for_port("localhost", db_config.get("port", 5432))

    conn = connect_to_db(db_config)
    if conn is None:
        print("Database connection failed. Exiting.")
        return

    cursor = conn.cursor()
    
    encrypt_columns(conn, cursor, secret_key)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash-augur-email.py <secret_key>")
    else:
        secret_key = sys.argv[1]
        main(secret_key)