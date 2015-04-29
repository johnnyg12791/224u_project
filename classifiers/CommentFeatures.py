
import sqlite3
import numpy as np
import sklearn.feature_extraction as fe


class CommentFeatures():

	def __init__(self):
		self.db = sqlite3.connect("/afs/ir.stanford.edu/users/l/m/lmhunter/CS224U/224u_project/nyt_comments.db")
		self.c = self.db.cursor()
		self.trainSelectQuery = "SELECT CommentID, ArticleURL, CommentText, FullText FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =1"
		self.devSelectQuery = "SELECT CommentID, ArticleURL, CommentText, FullText FROM Comments c, ArticleText a WHERE c.ArticleURL = a.URL AND c.TrainTest =2"

