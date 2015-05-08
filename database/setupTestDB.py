#setup test database
#Select 10,000 from comments
import sqlite3


def main():
    ##Pull unprocessed articles from DB:
    #num_articles = db_article_cursor.execute("SELECT * FROM Comments WHERE CommentsAdded = 0").fetchone()[0]
    getLimitedComments = "SELECT * FROM Comments LIMIT 10000"
    comments = backup_db_cursor.execute(getLimitedComments)
    for commentRow in comments:
        command = "INSERT OR IGNORE INTO Comments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        test_db_cursor.execute(command, commentRow)
    
    '''
    So on and so forth...just comments for now    
    getLimitedArticles = "SELECT * FROM Articles LIMIT 10000"
    articles = co
    '''

#Open database and access cursor:
#backup_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/backup_may8.db")
#John for testing
backup_db = sqlite3.connect("../../backup_may8.db")
test_db = sqlite3.connect("test.db") #Needs to be run in the directory with test.db (database/)
backup_db_cursor = backup_db.cursor()
test_db_cursor = test_db.cursor()

#Run main method:
if __name__ == "__main__":
    main()
#Close database and cursor:

backup_db.commit()
test_db.commit()

backup_db_cursor.close()
test_db_cursor.close()

backup_db.close()
test_db.close()