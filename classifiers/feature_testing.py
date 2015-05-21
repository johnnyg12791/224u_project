from CommentFeatures import CommentFeatures
 
may_8_query = "SELECT c.CommentID, perc_5_char_words, perc_3_char_words, words_per_sentence, n_chars, n_upper, avg_sentence_len, n_periods FROM Features f, Comments c WHERE c.CommentID = f.CommentID"

cf = CommentFeatures()
cf.limitNumComments(3000)
cf.setFeaturesQuery(may_8_query)
cf.setLinearSVM()
cf.featureModel()
cf.classify()
cf.close()
