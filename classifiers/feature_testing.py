from CommentFeatures import CommentFeatures
 
trivial_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"
all_query = "SELECT f.*, c.EditorSelection FROM Comments c, Features f WHERE c.CommentID = f.CommentID"
medium_query = "SELECT c.CommentID, c.EditorSelection, JJ, n_periods, WP, n_sentences, perc_1_char_words, NN, starts_with_I, CC, n_chars, n_upper, n_words, VBZ FROM Features f, Comments c WHERE c.CommentID = f.CommentID"

#Initialize features model:
cf = CommentFeatures()

#Set cutoff on review count, verbosity, features query:
cf.limitNumComments(5000) #50,000 samples will be our default "small" size
cf.setVerbose()
cf.setFeaturesQuery(all_query)

#Choose classifier: (Choose ONE)
cf.setLinearSVM()
#cf.setSGD()

#Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.calcPCA()

#Perform the classification step, show metrics:
cf.classify()
cf.topNCoefficients(10) #Check to see which coefficients are most popular

#Close up the database, cursors, etc
cf.close()