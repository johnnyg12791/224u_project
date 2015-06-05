from CommentFeatures import CommentFeatures
 

##############Initialize features model:
cf = CommentFeatures()


##############Set cutoff on review count, verbosity, features query:
cf.limitNumComments(50000) #50,000 samples will be our default "small" size
cf.setEditorPicksProportion(0.5, 0.5) #Start with a 50/50 editor/non-editor split
cf.setVerbose()
cf.setFeaturesQuery(basic_af)
cf.zeroBlankColumns()
#cf.preprocessText()
#cf.setResultsFile("results.csv") ##JOHN-- pulled this out of "classify"


##############Query the database to make feature vectors/clean data:
cf.featureModel()
#cf.featuresAndCommentWordsModel(maxNgram=2)
#cf.recursiveFeatureElimination()
#cf.bagOfWordsModel()
#cf.calcPCA()
#cf.splitClassifierModel(splitOn=200)

##############Choose classifier: (Choose ONE)
#cf.setSGD()
cf.setLinearSVM(C_val=.5, penalty='l1', dual=False)
#cf.setKernelSVM("poly")
#cf.useCVSearch()
#cf.setRandomForest()
#cf.useNeuralNetwork() #Recommend: low # features
#cf.useTwoClassifiers()


##############Perform the classification step, show metrics:
#cf.classify()
cf.useEnsemble()
#cf.classifyOnSplit()

##############Visualization of results:
#cf.visualize_tsne()
#Can only use this with a Linear Kernel
#Note: to see topNCoefficients, must include CommentText and CommentID in select query
#cf.topNCoefficients(30) #Check to see which coefficients are assigned highest classification weight
#cf.viewMisclassifiedReviews()

##############Close up the database, cursors, etc
cf.close()

