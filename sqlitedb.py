import sqlite3
class SqliteDB:
    def __init__(self):

        # Create a SQLite database and table
        self.conn = sqlite3.connect('data/data.sqlite3')
        self.cursor = self.conn.cursor()
        self.create_table()

    def conn_close(self):
        self.conn.close()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                date VARCHAR(100) NOT NULL,
                amount VARCHAR(100) NOT NULL
            )
        ''')
        self.conn.commit()

        
