import sqlite3

DB_FILE = "notes.db"

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER DEFAULT 0,
                image_path TEXT
            )
        ''')
        self.conn.commit()

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, content, created, modified, word_count, image_path FROM notes ORDER BY modified DESC")
        return cursor.fetchall()

    def get_by_id(self, note_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, content, created, modified, word_count, image_path FROM notes WHERE id=?", (note_id,))
        return cursor.fetchone()

    def insert(self, title="", content="", image_path=""):
        cursor = self.conn.cursor()
        word_count = len(content.split()) if content else 0
        cursor.execute('''
            INSERT INTO notes (title, content, word_count, image_path)
            VALUES (?, ?, ?, ?)
        ''', (title, content, word_count, image_path))
        self.conn.commit()
        return cursor.lastrowid

    def update(self, note_id, title, content, image_path=None):
        cursor = self.conn.cursor()
        word_count = len(content.split()) if content else 0
        if image_path is None:
            cursor.execute('''
                UPDATE notes SET title=?, content=?, word_count=?, modified=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (title, content, word_count, note_id))
        else:
            cursor.execute('''
                UPDATE notes SET title=?, content=?, word_count=?, image_path=?, modified=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (title, content, word_count, image_path, note_id))
        self.conn.commit()

    def delete(self, note_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self.conn.commit()

    def search(self, query):
        cursor = self.conn.cursor()
        like = f"%{query}%"
        cursor.execute('''
            SELECT id, title, content, created, modified, word_count, image_path
            FROM notes
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY modified DESC
        ''', (like, like))
        return cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
