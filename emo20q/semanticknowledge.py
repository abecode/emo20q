#!/usr/bin/env python3

from .gamedata import HumanHumanTournament,HumanComputerTournament,HumanComputerCouchDbTournament,HumanComputerCouchJsonTournament
from collections import defaultdict
import re
from nltk.probability import *
from nltk.classify.naivebayes import NaiveBayesClassifier

#refactoring ideas: use bayesian terminology?
# subclass naive bayes?
#   Semantic Knowledge is one child subclass of naive bayes
#   and working memory is another subclass


class SemanticKnowledge(NaiveBayesClassifier):

   def __init__(self):
      # read in tournament, do some testing, get some stats
      #tournament = HumanHumanTournament()
      #tournament = (HumanHumanTournament()+HumanComputerTournament()+HumanComputerCouchDbTournament())
      # workaround: use json dump of couch instead of db connection

      tournament = (HumanHumanTournament()+HumanComputerTournament()+HumanComputerCouchJsonTournament())
      #tournament = (HumanHumanTournament()+HumanComputerTournament())
      #tournament = HumanComputerCouchJsonTournament()

      #count turns in a dict, for pruning
      qcounts = defaultdict(int)
      for m in tournament.matches():
         for t in m.turns():
            qcounts[t.questionId()]+=1

      feature_count_threshold  = 2
      # get list of emotions(entities/labels) and a list of
      # questions(properties/features)
      self._labels   = set()
      self._features = set()
      #get FreqDist of emotions(entities/labels)
      self._label_freqdist = FreqDist()
      #get FreqDist of questions(properties/features) given emotions
      self._feature_freqdist = defaultdict(FreqDist)
      self._feature_values = defaultdict(set)
      for m in tournament.matches():
         #print(m.emotion())
         emotions = m.emotion().split("/") #deal with synonyms (sep'd w/ '/' )
         for e in emotions:
            self._labels.add(e)
            self._label_freqdist[e] += 1
            for t in m.turns():
               qid = t.questionId()
               if(qcounts[qid] >= feature_count_threshold):
                  #deal with b.s. questions
                  if (qid.find("non-yes-no")==0): continue
                  if (qid.find("giveup")==0): continue
                  self._features.add(qid)
                  #convert answer to yes/no/other
                  ans = t.answerId()
                  # try: 
                  #    ans = t.answerId()
                  # except AttributeError:
                  #    print(m)
                  #    print(e)
                  #    print(t)
                  #if ans == "other": continue
                  #deal with guesses:
                  #guess = re.search(r'^e==(\w+)$',t.qgloss )
                  #if(guess):
                  self._feature_freqdist[e,qid][ans] += 1
                  self._feature_values[qid].add(ans)

      # assign "None" to properties of entities when property is unseen
      for e in self._labels:
         num_samples = self._label_freqdist[e]
         for fname in self._features:
            count = self._feature_freqdist[e, fname].N()
            if count == 0:
               self._feature_freqdist[e, fname][None] += 1
               self._feature_values[fname].add(None)
               #these next 3 lines are questionable
               self._feature_values[fname].add("yes")
               self._feature_values[fname].add("no")
               self._feature_values[fname].add("other")

      # Create the P(label) distribution
      self._label_probdist =  ELEProbDist(self._label_freqdist)


      # Create the P(fval|label, fname) distribution
      self._feature_probdist = {}
      for ((label, fname), freqdist) in self._feature_freqdist.items():
         probdist = ELEProbDist(freqdist, bins=len(self._feature_values[fname]))
         self._feature_probdist[label,fname] = probdist

   def entities(self):
      return self._labels
   def properties(self):
      return self._features
   def prior(self):
      return self._label_probdist
   def likelihood(self,observation,model):
      pass
   def setPriors(self,label_probdist):
      # it seems like this code is not being used/reached
      # also, based on discussion with Jimmy, it might be
      # doing some smoothing that we didn't know about
      # if not isinstance(label_probdist,ProbDistI):
      #    try:
      #       label_probdist = ELEProbDist(label_probdist)
      #    except:
      #       pass
      self._label_probdist = label_probdist


   def show_most_informative_features(self, n=20):
      # Determine the most relevant features, and display them.
      cpdist = self._feature_probdist
      print('Most Informative Features')

      for (fname, fval) in self.most_informative_features(n):
         def labelprob(l):
            return cpdist[l,fname].prob(fval)
         labels = sorted([l for l in self._labels
                          if fval in cpdist[l,fname].samples()],
                         key=labelprob)
         if len(labels) == 1: continue
         l0 = labels[0]
         l1 = labels[-1]
         if cpdist[l0,fname].prob(fval) == 0:
            ratio = 'INF'
         else:
            ratio = '%8.1f' % (cpdist[l1,fname].prob(fval) /
                               cpdist[l0,fname].prob(fval))
         print ('%24s = %-14r %6s : %-6s = %s : 1.0' %
                (fname, fval, str(l1)[:6], str(l0)[:6], ratio))

   def most_informative_features(self, n=20):
      """
      Return a list of the 'most informative' features used by this
      classifier.  For the purpose of this function, the
      informativeness of a feature C{(fname,fval)} is equal to the
      highest value of P(fname=fval|label), for any label, divided by
      the lowest value of P(fname=fval|label), for any label::

            max[ P(fname=fval|label1) / P(fname=fval|label2) ]
            """
          # The set of (fname, fval) pairs used by this classifier.
      features = set()
      # The max & min probability associated w/ each (fname, fval)
      # pair.  Maps (fname,fval) -> float.
      maxprob = defaultdict(lambda: 0.0)
      minprob = defaultdict(lambda: 1.0)

      for (label, fname), probdist in self._feature_probdist.items():
         for fval in probdist.samples():
            feature = (fname, fval)
            features.add( feature )
            p = probdist.prob(fval)
            #print label,feature,p
            maxprob[feature] = max(p, maxprob[feature])
            minprob[feature] = min(p, minprob[feature])
            if minprob[feature] == 0:
               features.discard(feature)

      # Convert features to a list, & sort it by how informative
      # features are.
      features = sorted(features,
                        key=lambda feature: minprob[feature]/maxprob[feature])
      return features[:n]




if __name__ == "__main__":
   k = SemanticKnowledge()
   print(k.entities())
   print(len(k.entities()))
   print(k.show_most_informative_features(20))
