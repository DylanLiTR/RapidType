import sqlite3
import requests
import json


def seed_large_database():
    db = sqlite3.connect('main.sqlite')
    cursor = db.cursor()

    # 1. Drop and recreate the table to cleanly overwrite previous limited seeds
    print("Resetting quote pool table...")
    cursor.execute("DROP TABLE IF EXISTS local_quote_pool")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS local_quote_pool(
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        quote TEXT UNIQUE,
        author VARCHAR(64)
    )
    ''')
    db.commit()

    # 2. Large verified dataset containing 5,400+ quotes
    url = "https://raw.githubusercontent.com/JamesFT/Database-Quotes-JSON/master/quotes.json"

    print("Downloading massive 5,000+ quotes dataset from GitHub...")
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(
                f"Failed to download dataset. HTTP Status: {response.status_code}"
            )
            return

        raw_quotes = json.loads(response.text)
        print(
            f"Successfully downloaded {len(raw_quotes)} entries. Seeding SQLite database..."
        )

        inserted_count = 0
        for item in raw_quotes:
            if isinstance(item, dict):
                # This specific dataset uses 'quoteText' and 'quoteAuthor'
                q = item.get('quoteText')
                a = item.get('quoteAuthor') or "Unknown"

                if q:
                    # Strip any accidental trailing whitespace or dashes from fields
                    q_clean = q.strip()
                    a_clean = a.strip() if a.strip() not in ["", "-", "—"
                                                             ] else "Unknown"

                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO local_quote_pool (quote, author) VALUES (?, ?)",
                            (q_clean, a_clean))
                        if cursor.rowcount > 0:
                            inserted_count += 1
                    except sqlite3.Error:
                        pass

        db.commit()

        total_pool = cursor.execute(
            "SELECT COUNT(*) FROM local_quote_pool").fetchone()[0]
        print(f"\n Success!")
        print(f"Seeded {inserted_count} unique rows.")
        print(
            f"Total production pool size: {total_pool} quotes completely offline."
        )

    except Exception as e:
        print(f"An error occurred while seeding the database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_large_database()
