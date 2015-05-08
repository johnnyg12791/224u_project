import features
import sqlite3
import os

def main():
    DB_PATH = 'nyt_comments.db'
    if not os.path.isfile(DB_PATH):
        raise EnvironmentError('Database "' + DB_PATH + '" not found, please create symbolic link.')
    comments_db = sqlite3.connect(DB_PATH)
    cursor = comments_db.cursor()
    cursor.execute("SELECT URL FROM Articles WHERE HaveFullText = 0")

if __name__ == '__main__':
    main()