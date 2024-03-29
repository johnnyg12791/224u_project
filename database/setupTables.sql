CREATE TABLE Articles (URL text PRIMARY KEY, Author text, Title text, Section text, CommentsAdded boolean, TextAdded boolean);
CREATE TABLE Comments (CommentID integer PRIMARY KEY, ArticleURL text, RecommendedFlag integer, NumReplies integer, Trusted integer, UserDisplayName text, CreateDate integer, UserID integer, CommentTitle text, Sharing integer,  NumRecommendations integer, EditorSelection boolean, Timespeople integer, CommentText text, TrainTest integer);
CREATE TABLE ArticleText (URL text PRIMARY KEY, HaveFullText integer, FullText text);
CREATE TABLE Features (CommentID integer PRIMARY KEY, EditorSelection boolean);
