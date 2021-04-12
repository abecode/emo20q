#!/usr/bin/python

import os
import re
from collections import defaultdict

DIRNAME = os.path.dirname(os.path.realpath(__file__))
DATADIR = os.path.join(DIRNAME, "data")
QUESTIONTABLE = "questionsTableFromCompling_emo20qData.txt"
DECLARATIVEPATCH = "declarativeGeneratorPatch.txt"

def isReady(string):
    """
    check to see if the player is ready:
    Try to match affirmative answers to the question, are you ready?
    """
    string = string.lower()
    match = re.search(r'\byes\b|\bready\b|\bsure\b|\bgo\b|\bok\b|\bokay\b|\byep\b|\byea\b|\byeah\b', string)
    nomatch = re.search(r'\bno\b|\bnot\b', string)
    return match and not nomatch

def classifyYN(string):
    """"Classify answers to a yes/no question into 1/yes, -1/no, or 0/other"""
    string = string.lower()
    if re.search(r'\n',string) : #only look at first line
        newstring = string.split("\n")[0]
        return classifyYN(newstring)

    yes = 0
    no = 0
    if re.search(r'\byes\b', string)  : yes += 1
    if re.search(r'\byeah\b', string)  : yes += 1
    if re.search(r'\byea\b', string)  : yes += 1
    if re.search(r'\byup\b', string)  : yes += 1
    if re.search(r'\byep\b', string)  : yes += 1
    if re.search(r'\baye\b', string)  : yes += 1
    if re.search(r'\bsure\b', string)  : yes += 1
    if re.search(r'\bok\b',  string)  : yes += 1
    if re.search(r'\bokay\b', string)  : yes += 1
    if re.search(r'\byou got it\b', string)  : yes += 1
    if re.search(r'\bno\b', string)  : no += 1
    if re.search(r'\bnope\b', string)  : no += 1
    if re.search(r'\bnegative\b', string)  : no += 1 #?
    # if yes and no:
    #     print string
    #     print yes
    #     print no
    if yes > 0 and no == 0:
        ans = 1
    elif no > 0 and yes == 0:
        ans = -1
    else:
        ans=0
    return ans

def isAffirmative(string):
    """"Classify answers to a yes/no question into 1/yes, -1/no, or 0/other"""
    if classifyYN(string) == 1:
        return True
    return False

def isQuestion(string):
    """"Determine whether an input is a question or not"""
    if re.search(r'\?', string):
        return True
    if re.search(r'(?:how|who|what|why) (?:do|is|are|does|did|was|can|would|should|old|you)', string):
        return True
    return False


def splitCommaList(string):
    out = []
    #for x in string.split(","):
    for x in re.split(r'(?:, *(?:and)?|\band\b)', string):
        x = x.strip()
        out.append(x)
    return out

import os
import csv
import random


class GenerateDeclarative():
    """
    This class will take a question gloss (semantic representation for a
    question) and generate a declarative sentence from a lookup table (this
    class inherits from dict

    instantiate
    >>> gd = GenerateDeclarative()

    generate/lookup
    >>> gd.generate('e.valence==negative')
    'it is considered a negative thing to feel'

    generate using a random realization (random is seeded)
    >>> gd.generateRandom('e.valence==negative')
    'it is a negative emotion'
    """

    def __init__(self):
        # read in the exported mysql table (compling_emo20qData db, questions table)
        self._dictionary = defaultdict(list)
        datafile = os.path.join(DATADIR, QUESTIONTABLE)
        datareader = csv.reader(open(datafile), delimiter="\t")
        header = next(datareader)
        col = {}
        for i, c in enumerate(header):
            col[c]=i

        for row in datareader:
            if re.search(r'NULL', row[col["atmplt"]]):
                continue
            if re.search(r'^\s*$', row[col["atmplt"]]):
                continue
            #print row
            #print row[col["gloss"]], row[col["atmplt"]]
            self._dictionary[row[col["gloss"]]].append(row[col["atmplt"]])

        patch = os.path.join(DATADIR, DECLARATIVEPATCH)
        datareader = csv.reader(open(patch), delimiter="\t")
        header = next(datareader)
        col = {}
        for i, c in enumerate(header):
            col[c]=i

        for row in datareader:
            if re.search(r'NULL', row[col["atmplt"]]):
                continue
            if re.search(r'^\s*$', row[col["atmplt"]]):
                continue
            #print row
            #print row[col["gloss"]], row[col["atmplt"]]
            self._dictionary[row[col["gloss"]]].append(row[col["atmplt"]])

        random.seed(1)

    def generate(self, gloss):
        """generates/looks up from a semantic representation to a templated
        surface realization"""
        if gloss in self._dictionary:
            return self.replace(self._dictionary[gloss][0])
        else:
            #print gloss
            raise KeyError(gloss)

    def allRealizations(self, gloss):
        """generates/looks up all realizations of a  semantic representation"""
        if gloss in self._dictionary:
            return list(map(self.replace, self._dictionary[gloss]))
        else:
            #print gloss
            raise KeyError(gloss)

    def allTemplates(self, gloss):
        """generates/looks up from a semantic representation to a templated
        surface realization"""
        if gloss in self._dictionary:
            return self._dictionary[gloss]
        else:
            #print gloss
            raise KeyError(gloss)

    def generateRandom(self, gloss):
        """generates a random realization"""
        if gloss in self._dictionary:
            return self.replace(random.choice(self._dictionary[gloss]))
        else:
            #print gloss
            raise KeyError(gloss)

    def replace(self, template):
        """ replaces templates in the semantic representation with default
        value """
        return re.sub(r'{(.+?):(.+?)}', r'\2', template)

    def __call__(self, gloss, ans="yes"):
        out = self.generateRandom(gloss)
        if(ans == "yes"):
            return out
        if(ans == "no"):
            return self.negate(out)
        else:
            return self.hedge(out)

    def negate(self, sentence):
        if re.search(r'^only', sentence):
            return re.sub(r'^only ', "not only ", sentence)
        if re.search(r' can ', sentence):
            return re.sub(r' can ', " can't ", sentence)
        if re.search(r' would ', sentence):
            return re.sub(r' would ', " wouldn't ", sentence)
        if re.search(r' is ', sentence):
            return re.sub(r' is ', r' is not ', sentence)
        if re.search(r'it [a-z]+s ', sentence):
            return re.sub(r'it ([a-z]+)s ', r"it doesn't \1 ", sentence)
        if re.search(r'(people|you) (show|feel) ', sentence):
            return re.sub(r'(people|you) (show|feel) ', r"\1 don't \2 ", sentence)
        if re.search(r' has ', sentence):
            return re.sub(r' has ', r" does not have ", sentence)
        return "not " + sentence
    def hedge(self, sentence):
        return "maybe " + sentence


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    #gd = GenerateDeclarative()
    #print gd
    print("ok")
