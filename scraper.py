import sqlite3
import requests
import json
import time

# Connect to your existing database file
db = sqlite3.connect('main.sqlite')
cursor = db.cursor()

# Ensure the static pool table exists
cursor.execute('''
CREATE TABLE IF NOT EXISTS local_quote_pool(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    quote TEXT UNIQUE,  -- UNIQUE constraint prevents exact duplicates
    author VARCHAR(64)
)
''')
db.commit()


def harvest_quotes(target_count=1000):
    current_count = cursor.execute(
        "SELECT COUNT(*) FROM local_quote_pool").fetchone()[0]
    print(
        f"Starting harvest. Current local database has {current_count} quotes."
    )

    while current_count < target_count:
        try:
            print("Fetching 50 random quotes from ZenQuotes...")
            response = requests.get("https://zenquotes.io/api/quotes",
                                    timeout=5)

            if response.status_code == 200:
                raw_data = json.loads(response.text)
                inserted_this_round = 0

                for item in raw_data:
                    q = item.get('q')
                    a = item.get('a')
                    if q and a:
                        try:
                            # INSERT OR IGNORE skips the entry if the quote text already exists
                            cursor.execute(
                                "INSERT OR IGNORE INTO local_quote_pool (quote, author) VALUES (?, ?)",
                                (q, a))
                            if cursor.rowcount > 0:
                                inserted_this_round += 1
                        except sqlite3.Error:
                            pass

                db.commit()
                current_count = cursor.execute(
                    "SELECT COUNT(*) FROM local_quote_pool").fetchone()[0]
                print(
                    f"Added {inserted_this_round} new unique quotes. Total stockpile: {current_count}/{target_count}"
                )

            else:
                print(
                    f"API returned status code {response.status_code}. Waiting a bit..."
                )

        except Exception as e:
            print(f"Error harvesting: {e}")

        # Wait 1 hour between batches to get fresh quotes
        if current_count < target_count:
            print("Sleeping for 1 hour to avoid API rate limits...")
            time.sleep(60 * 60 + 10)

    print("Harvest complete! You can safely delete or ignore scraper.py now.")


if __name__ == "__main__":
    harvest_quotes(
        target_count=1000)  # Adjust this number if you want a larger pool
