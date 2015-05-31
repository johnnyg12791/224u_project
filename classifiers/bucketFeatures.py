
import sqlite3 
import nltk 
import re
from collections import defaultdict

#Method: makeWordLengthBuckets
#Note: heavily borrowing from Mark's "features.py"; steamlined to eliminate
#computation of additional NLTK features; do setting inside function
def makeWordLengthBuckets(text, c_id):
	#Clean the text:
	clean_text = re.sub(ur'[!\?\.\,-_()\[\]\"\'\%0123456789]', '', text)
	tokens = clean_text.lower().split()

	features = defaultdict(float)

	#Put into buckets based on word length: (not normalized)
	for word in tokens:
		w_len = len(word)
		if w_len == 1:
			features['num_1_letter_words'] += 1
		elif w_len < 6:
			features['num_2-5_letter_words'] += 1
		elif w_len < 10:
			features['num_6-9_letter_words'] += 1
		elif w_len < 15:
			features['num_10-14_letter_words'] += 1
		else:
			features['num_15plus_letter_words'] += 1

	num_words = len(tokens)
	if num_words < 1: return 
	#Add percent buckets:
	features['perc_1_letter'] = features['num_1_letter_words'] / num_words
	features['perc_2-5_letters'] = features['num_2-5_letter_words'] / num_words
	features['perc_6-9_letter_words'] = features['num_6-9_letter_words'] / num_words
	features['perc_10-14_letter_words'] = features['num_10-14_letter_words'] / num_words
	features['perc_15plus_letter_words'] = features['num_15plus_letter_words'] / num_words

	#Note: setting assumes you have already configured your table to have these buckets
	setter_cursor.execute("UPDATE Features SET num_1_letter_words = ?, num_2_5_letter_words = ?, num_6_9_letter_words = ?, num_10_14_letter_words =?, num_15plus_letter_words = ? WHERE CommentID=?",
		(features['num_1_letter_words'], features['num_2-5_letter_words'], features['num_6-9_letter_words'], features['num_10-14_letter_words'], features['num_15plus_letter_words'], c_id))
	setter_cursor.execute("UPDATE Features SET perc_1_letter_words = ?, perc_2_5_letter_words = ?, perc_6_9_letter_words = ?, perc_10_14_letter_words =?, perc_15plus_letter_words = ? WHERE CommentID=?",
		(features['perc_1_letter_words'], features['perc_2-5_letter_words'], features['perc_6-9_letter_words'], features['perc_10-14_letter_words'], features['perc_15plus_letter_words'], c_id))

#Initialize database plus cursors
db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/may31.db")
loop_cursor = db.cursor()
setter_cursor = db.cursor()

#Update buckets
count = 0
for c_id, c_text in loop_cursor.execute("SELECT CommentID, CommentText FROM Comments"):
	makeWordLengthBuckets(c_text, c_id)
	count += 1
	if count % 1000 == 0:
		print "Done %d so many" %count
		db.commit()

#Commit & close the database + cursors
db.commit()
loop_cursor.close()
setter_cursor.close()
db.close()





