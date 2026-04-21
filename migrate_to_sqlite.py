"""
Run once: exports MySQL/Docker ganjoor DB → ganjoor.db (SQLite)
Usage: python migrate_to_sqlite.py
"""
import sqlite3
import pymysql

MYSQL = dict(
    host="localhost",
    port=3306,
    user="root",
    password="root",
    database="ganjoor",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)

TABLES = {
    "poets": """
        CREATE TABLE IF NOT EXISTS poets (
            id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT
        )""",
    "categories": """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            poetId INTEGER,
            parentId INTEGER,
            name TEXT
        )""",
    "poems": """
        CREATE TABLE IF NOT EXISTS poems (
            id INTEGER PRIMARY KEY,
            categoryId INTEGER,
            title TEXT
        )""",
    "verses": """
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY,
            poemId INTEGER,
            `order` INTEGER,
            position INTEGER,
            text TEXT
        )""",
}

SELECTS = {
    "poets":      "SELECT id, name, description FROM poets",
    "categories": "SELECT id, poetId, parentId, name FROM categories",
    "poems":      "SELECT id, categoryId, title FROM poems",
    "verses":     "SELECT id, poemId, `order`, position, text FROM verses",
}

def migrate():
    print("Connecting to MySQL...")
    src = pymysql.connect(**MYSQL)
    dst = sqlite3.connect("ganjoor.db")
    dst.execute("PRAGMA journal_mode=WAL")
    dst.execute("PRAGMA synchronous=NORMAL")

    with src.cursor() as cur:
        for table, ddl in TABLES.items():
            print(f"  Creating table {table}...")
            dst.execute(f"DROP TABLE IF EXISTS {table}")
            dst.execute(ddl)

            print(f"  Fetching {table}...")
            cur.execute(SELECTS[table])
            rows = cur.fetchall()
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ",".join("?" * len(cols))
            col_names = ",".join(f"`{c}`" for c in cols)
            data = [tuple(r[c] for c in cols) for r in rows]
            dst.executemany(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", data)
            dst.commit()
            print(f"    → {len(data)} rows")

    # Indexes for speed
    dst.execute("CREATE INDEX IF NOT EXISTS idx_cat_poet   ON categories(poetId)")
    dst.execute("CREATE INDEX IF NOT EXISTS idx_cat_parent ON categories(parentId)")
    dst.execute("CREATE INDEX IF NOT EXISTS idx_poem_cat   ON poems(categoryId)")
    dst.execute("CREATE INDEX IF NOT EXISTS idx_verse_poem ON verses(poemId)")
    dst.commit()

    src.close()
    dst.close()
    print("\nDone! ganjoor.db created.")

if __name__ == "__main__":
    migrate()
