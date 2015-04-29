import string
# import nltk
# from textblob import TextBlob
from collections import Counter

class Features:
    MAX_CHARS_PER_WORD = 10

    @staticmethod
    def len_feats(text):
        MAX_CHARS_PER_WORD = 10
        words = text.split()
        feats = {
            'n_chars': len(text),
            'n_words': len(words),
            'n_periods': sum(1 for c in text if c == '.'),
            'n_questions': sum(1 for c in text if c == '?')
        }
        for i in range(1, MAX_CHARS_PER_WORD + 1):
            feats['n_' + str(i) + '_char_words'] = sum(1 for w in words if len(w) == i)
        return feats

    @staticmethod
    def similarity_word_feature(textA, textB):
        splitA = textA.split()
        splitB = textB.split()
        num_same_words = len(set(splitA).intersection(set(splitB)))
        num_total_words = len(set(splitA + splitB))
        return float(num_same_words) / num_total_words