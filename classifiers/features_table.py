from features import *
import sqlite3
import os
import sys



#
def get_database(test):
    DB_PATH = 'nyt_comments.db'
    if(test == "test"):
        DB_PATH = "../database/test.db"

    if not os.path.isfile(DB_PATH):
        raise EnvironmentError('Database "' + DB_PATH + '" not found, please create symbolic link.')
    comments_db = sqlite3.connect(DB_PATH)
    
    return comments_db


#
def main():
    comments_db = get_database(sys.argv[1])#test or something else
    cursor = comments_db.cursor()

    #helper method that adds all comment IDs from Comments to Features
    add_commentIDs_to_feature_table(cursor)


    #For each row in the Comments Table, we want to add all features associated with that text
    comments_data = [(c_id, c_text) for (c_id, c_text) in cursor.execute("SELECT CommentID, CommentText FROM Comments")]
    for comment_id, comment_text in comments_data:
        features = basic_feats(comment_text) #Feature dictionary based on comment text

        for feature_name, feature_value in features.items():      
            #If that column doesn't exist, alter table by adding it
            cursor.execute("SELECT * FROM Features LIMIT 1")
            if feature_name not in {description[0] for description in cursor.description}:
                cursor.execute("ALTER TABLE Features ADD COLUMN '%s' 'float'" % feature_name)
            
            #Now that the column exists, add specifed value
            insert_statement = ("UPDATE Features SET '%s'= %f WHERE CommentID = %d" % (feature_name, feature_value, comment_id))
            cursor.execute(insert_statement)


    comments_db.commit()
    cursor.close()    
    comments_db.close()



#Goes throught the comments table, adding all IDs to features
def add_commentIDs_to_feature_table(cursor):
    commentIDs = [comment_id for comment_id in cursor.execute("SELECT CommentID FROM Comments")]
    for comment_id in commentIDs:
        #print comment_id
        cursor.execute("INSERT OR IGNORE INTO Features(CommentID) VALUES (?)", comment_id)




if __name__ == '__main__':
    main()