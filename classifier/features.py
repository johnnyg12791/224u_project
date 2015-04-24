# Borrowed some from https://github.com/markulrich/chambot/blob/master/config/features.py
import string
from textblob import TextBlob
from collections import Counter

class UnaryFeatures:
    def __init__(self, text):
        self.text = text

    def avg_word_len(self):
        words = self.text.split()
        return sum(len(w) for w in words) / len(words)

    def total_len(self):
        return len(self.text)


class BinaryFeatures:
    def __init__(self, textA, textB):
        self.textA = textA
        self.textB = textB

    def similarity_word_feature(self):
        splitA = self.textA.split()
        splitB = self.textB.split()
        num_same_words = len(set(splitA).intersection(set(splitB)))
        num_total_words = len(set(splitA + splitB))
        return float(num_same_words) / num_total_words