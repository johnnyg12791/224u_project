from features import *
import sqlite3
import os
import sys
import time


#
def get_database(arg1):
    DB_PATH = 'nyt_comments.db'
    if(arg1 == "real"):
	DB_PATH = "/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db"

    if(arg1 == "test"):
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
    counter = 0
    for comment_id, comment_text in comments_data:
	
	start = time.time()
	features = all_comment_feats(comment_text) #Feature dictionary based on comment text
	print "To get all features it took: " , time.time() - start
	
	if(counter % 1000 == 0):
	    print counter
	counter += 1
	cursor.execute("SELECT * FROM Features LIMIT 1")
	list_of_features = {description[0] for description in cursor.description}
	#print list_of_features
	#raw_input("")

	#start = time.time()
	
	'''update_string = "UPDATE Features SET "
	ordered_vals = []
	for ft_name, ft_value in features.items():
	    #buildString based on names/values
            update_string += (ft_name + " = ?, ")	    
	    ordered_vals.append(ft_value)
	print update_string[:len(update_string)-2]
	#cusor.execute(execute_string, tuple(ordered_vals))
	'''

        for feature_name, feature_value in features.items():      
            #If that column doesn't exist, alter table by adding it
            #cursor.execute("SELECT * FROM Features LIMIT 1")
            if feature_name not in list_of_features: #{description[0] for description in cursor.description}:
                #add_col = ("ALTER TABLE Features ADD COLUMN '%s' REAL" % feature_name)
		#print add_col
		try:
		    cursor.execute("ALTER TABLE Features ADD COLUMN '%s' REAL" % feature_name)
            	except Exception as e:
 		    pass
            #Now that the column exists, add specifed value
            insert_statement = ("UPDATE Features SET '%s'= %f WHERE CommentID = %d" % (feature_name, feature_value, comment_id))
            cursor.execute(insert_statement)
	#print "To add all features it took: " , time.time() - start

	#I would like to do the previous step in one update
	if(counter % 5000 == 0):#Update every 10k
            #start = time.time()
	    comments_db.commit()
	    #print "The commit took " , time.time() - start

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
