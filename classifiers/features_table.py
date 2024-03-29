from features import *
import sqlite3
import os
import sys
import time


#Returns that database, basically two options, specified via command line
def get_database(arg1):
    DB_PATH = "/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/" + arg1

    if(arg1 == "real"):
       DB_PATH = "/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db"

    if(arg1 == "local"):
        DB_PATH = "../john_test_4.db"

    if not os.path.isfile(DB_PATH):
        raise EnvironmentError('Database "' + DB_PATH + '" not found, please create symbolic link.')
    comments_db = sqlite3.connect(DB_PATH)
    
    return comments_db


#
def main():
    comments_db = get_database(sys.argv[1])#test or something else
    cursor = comments_db.cursor()

    #helper method that adds all comment IDs from Comments to Features
    if(len(sys.argv) == 2): #Add a 3rd arg to skip this (if table already populated)     
        add_commentIDs_to_feature_table(cursor)


    #For each row in the Comments Table, we want to add all features associated with that text
    comments_data = [(c_id, c_text) for (c_id, c_text) in cursor.execute("SELECT CommentID, CommentText FROM Comments")]
    counter = 0
    start = time.time()

    for comment_id, comment_text in comments_data:    
        features = all_comment_feats(comment_text) #Feature dictionary based on comment text
        
        if(counter % 1000 == 0):
            print counter, " took ", time.time() - start
        counter += 1
        cursor.execute("SELECT * FROM Features LIMIT 1")
        list_of_features = {description[0] for description in cursor.description}


        for feature_name, feature_value in features.items():      
            #If that column doesn't exist, alter table by adding it
            if feature_name not in list_of_features: #{description[0] for description in cursor.description}:
                try:
                    cursor.execute("ALTER TABLE Features ADD COLUMN '%s' REAL" % feature_name)
                except Exception as e:
                    pass
            #Now that the column exists, add specifed value
            #I should only do this if NOT EXISTS    
            insert_statement = ("UPDATE Features SET %s= %f WHERE CommentID = %d" % (feature_name, feature_value, comment_id))
            cursor.execute(insert_statement)

        #I would like to do the previous step in one update
        if(counter % 1000 == 0):#Update every 10k
            comments_db.commit()#Does not take a long time to run

    comments_db.commit()
    cursor.close()    
    comments_db.close()



#Goes throught the comments table, adding all IDs to features
def add_commentIDs_to_feature_table(cursor):
    commentIDs = [(comment_id, editorsSelection) for comment_id, editorsSelection in cursor.execute("SELECT CommentID, EditorSelection FROM Comments")]
    for comment_id, editorsSelection in commentIDs:
        #print comment_id
        cursor.execute("INSERT OR IGNORE INTO Features(CommentID, EditorSelection) VALUES (?, ?)", (comment_id, editorsSelection))




if __name__ == '__main__':
    main()



    
        
'''update_string = "UPDATE Features SET "
ordered_vals = []
for ft_name, ft_value in features.items():
    #buildString based on names/values
        update_string += (ft_name + " = ?, ")       
    ordered_vals.append(ft_value)
print update_string[:len(update_string)-2]
#cusor.execute(execute_string, tuple(ordered_vals))
'''
