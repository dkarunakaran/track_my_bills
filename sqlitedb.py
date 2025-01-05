import sqlite3

class SqliteDB:
    def __init__(self):

        # Create a SQLite database and table
        self.conn = sqlite3.connect('data/data.db')
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
                amount VARCHAR(100) NOT NULL,
                payment VARCHAR(100),
                processed INTEGER NOT NULL,
                Paid INTEGER DEFAULT 0,
                created_date TEXT NOT NULL
            )
        ''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Payment_methods (
                payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL
            )
        ''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Download_methods (
                download_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL
            )
        ''')
        self.conn.commit()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject VARCHAR(200) NOT NULL,
                payment_method_id INTEGER NOT NULL,
                download_method_id INTEGER NOT NULL,
                sender VARCHAR(200) NOT NULL,
                FOREIGN KEY (payment_method_id) REFERENCES Payment_methods(payment_method_id),
                FOREIGN KEY (download_method_id) REFERENCES Download_methods(download_method_id)
            )
        ''')
        self.conn.commit()




        
