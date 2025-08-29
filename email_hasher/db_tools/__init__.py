import psycopg2
import traceback
import json

import socket
import time


def wait_for_port(host, port, logging=True, retry_interval=2):
    # Loop indefinitely until the port is found to be in use.
    while True:
        if is_port_in_use(host, int(port)):
            if logging:
                print(f"Success! Port {host}:{port} is now in use.")
            break  # Exit the loop once the port is open.
        else:
            if logging:
                print(f"Port {host}:{port} is not in use. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)


def is_port_in_use(host, port):
    """
    Checks if a port is in use by trying to bind to it.
    This method avoids establishing a connection.

    Args:
        host (str): The hostname or IP address to check.
        port (int): The port number to check.

    Returns:
        bool: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            # Try to bind to the port. If it's already in use, this will raise an OSError.
            s.bind((host, port))
            # If we successfully bind, the port is NOT in use.
            return False
        except OSError:
            # If an OSError occurs, it means the port is already bound by another process.
            return True

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


def run_query(conn, cursor, query):
    try:
        # Ensure the pgcrypto extension is available.
        cursor.execute(query)
        conn.commit()

    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()


def encrypt_columns(conn, cursor, encryption_key, fields_to_encrypt={}, schema="augur_data"):
    try:
        # Ensure the pgcrypto extension is available.
        cursor.execute(f"CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA {schema};")
        conn.commit()

        # List of columns to encrypt.
        if fields_to_encrypt == {}:

            fields_to_encrypt = {
                "commits": [
                    "cmt_author_raw_email",
                    "cmt_author_email",
                    "cmt_committer_raw_email",
                    "cmt_committer_email"
                ],
                "contributors": [
                    "cntrb_email",
                    "cntrb_canonical"
                ]
            }
        
        for table, columns in fields_to_encrypt:
            print(f"Encrypting table {table}...")
            for field in columns:
                # Build the query string using .format() instead of an f-string.
                print(f"Encrypting column {table}.{field}...")
                query = """
                    UPDATE {schema}.{table}
                    SET {field} = encode(
                        {schema}.pgp_sym_encrypt({field}::text, '{secret_key}'::text),
                        'base64'
                    )
                    WHERE {field} IS NOT NULL;
                """.format(table=table, field=field, secret_key=encryption_key, schema=schema)
                cursor.execute(query)
                conn.commit()
                print("Encrypted column:", field)

        print("All encryption updates applied successfully.")

    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
