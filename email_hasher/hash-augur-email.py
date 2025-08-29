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
import sys
from db_tools import encrypt_columns, read_db_config, connect_to_db

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
    
    encrypt_columns(conn, cursor, secret_key)

    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hash-augur-email.py <secret_key>")
    else:
        secret_key = sys.argv[1]
        main(secret_key)