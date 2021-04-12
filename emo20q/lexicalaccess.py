#!/usr/bin/env python3

from .gamedata import HumanHumanTournament
from collections import defaultdict
import re
import random

class LexicalAccess():
   def __init__(self):
      # read in tournament, do some testing, get some stats
      tournament = HumanHumanTournament()

      self._dictionary = defaultdict(list)

      for m in tournament.matches:
         for t in m.turns:
            self._dictionary[t.questionId()].append(t.q)
   def __call__(self,gloss):
      return self.lookUp(qgloss)
   def lookUp(self, qgloss):
       candidates = self._dictionary[qgloss]
       if len(candidates) == 0:
          match = re.search(r'^e==(.+)$', qgloss)
          if match:  #deal with identity questions w/o lexical realizations
             return "is it %s?" % match.group(1)
          else:
             raise Exception("I didn't find a lexical realization for %s" % qgloss)
       return random.choice(candidates)

if __name__ == "__main__":
    l = LexicalAccess()
    qgloss = raw_input("please enter a semantic question representation\n>> ")
    print("This is a randomly selected/generated question text:")
    print(l.lookUp(qgloss))
