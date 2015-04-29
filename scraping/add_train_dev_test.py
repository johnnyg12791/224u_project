###THis program will add a train/dev/test split for comments that have
#already been added to the database. It will first ensure that there is not
#currently a tdt label on the comment; if not, it will add it to train (70%),
#dev (20%) or test(10%) data. Note that this is the same split scheme that is
#used for the comment classification in the current version of the nyt_scraper.


import sqlite3
import random


def main():
	selectCommand = "SELECT CommentID, TrainTest FROM Comments"
	for comID, trtest in loop_cursor.execute(selectCommand):
		TDT = train_dev_test()
		if trtest == None:
			updateCommand = "UPDATE Comments SET TrainTest = (?) WHERE CommentID = (?)"
			exec_cursor.execute(updateCommand, (TDT, comID))




#Splits dataset into 70/20/10 train/dev/test
#Where 1 = train, 2 = dev, 3 = test
def train_dev_test():
    classification = random.random()
    if classification < .7:
        return 1
    if classification < .9:
        return 2
    return 3

comments_db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
loop_cursor = comments_db.cursor() #Cursor to do update of comments table
exec_cursor = comments_db.cursor()
#Run main method:
if __name__ == "__main__":
    main()
#Close database and cursors:
comments_db.commit()
loop_cursor.close()
exec_cursor.close()
comments_db.close()
