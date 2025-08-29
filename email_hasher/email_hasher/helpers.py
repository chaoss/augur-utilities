import psycopg2
import traceback

def encrypt_emails(conn, cursor, encryption_key):
    try:
        # Ensure the pgcrypto extension is available.
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto SCHEMA augur_data;")
        conn.commit()

        # List of columns to encrypt.
        fields_to_encrypt = [
            "cmt_author_raw_email",
            "cmt_author_email",
            "cmt_committer_raw_email",
            "cmt_committer_email"
        ]

        for field in fields_to_encrypt:
            # Build the query string using .format() instead of an f-string.
            print(f"Encrypting column {field}...")
            query = """
                UPDATE augur_data.commits
                SET {field} = encode(
                    augur_data.pgp_sym_encrypt({field}::text, '{secret_key}'::text),
                    'base64'
                )
                WHERE {field} IS NOT NULL;
            """.format(field=field, secret_key=encryption_key)
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
