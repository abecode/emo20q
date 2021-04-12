#!/usr/bin/python

"""
a generalized pushdown automaton is a pushdown automaton that can look 
at its whole stack.

in the case of the emo20q agent, the stack is it's episodic buffer

This is meant as a control mechanism for an agent.  For stuff like nlp parsing
lots of data, it might be too slow.

"""
from types import *
from collections import defaultdict,OrderedDict
import networkx as nx
import re

class GPDAError(Exception):
    pass

class State():
    neighbors = OrderedDict()
    """ 
    a state in a generalized push down automata 

    """
    def __init__(self,name):
        """ set the state name """
        self.name = name
        

class GPDA(nx.DiGraph):
    """ 
    a generalized push down automata 

    # create the machine
    >>> machine = GPDA()

    # add states...
    >>> machine.add_state("perdition")
    Traceback (most recent call last):
    ...
    TypeError

    # oops, states must be states
    # do it the right way
    >>> s = State("salvation")
    >>> machine.add_state(s)
    >>> p = State("perdition")
    >>> machine.add_state(p)

    # add transitions
    >>> machine.add_transition(s,p,
    ...   test=lambda x: True if x=="TV" or x=="high fructose corn syrup" else False,
    ...   function=lambda x: "%s makes your brain rot. you are going to hell."%str(x) )

                               
    # set state
    >>> machine.set_state(s)

    # give input "TV" and print the output:
    >>> print machine("TV")
    TV makes your brain rot. you are going to hell.
    >>> print machine.state.name
    perdition

    # the new state doesn't accept the same inputs as the old state
    >>> print machine("TV")
    Traceback (most recent call last):
    ...
    GPDAError: no valid transition using this input, given current state perdition

    # get back into shape
    >>> machine.add_transition(p,s,
    ...   test=lambda x: True if (x=="carrots" or x=="exercise") and len(machine.stack)>5 else False,
    ...   function=lambda x: "congratulations, you attained salvation")
    >>> def getInShape(x):
    ...   machine.stack.append(x)
    ...   return "that helps but it's not enough"
    >>> machine.add_transition(p,p,
    ...   test=lambda x: True if (x=="carrots" or x=="exercise") and len(machine.stack)<=5 else False,
    ...   function=getInShape)
    >>> print machine("carrots")    # one
    that helps but it's not enough
    >>> print machine("carrots")    # two
    that helps but it's not enough
    >>> print machine("exercise")   # three
    that helps but it's not enough
    >>> print machine("carrots")    # four
    that helps but it's not enough
    >>> print machine("carrots")    # five
    that helps but it's not enough
    >>> print machine("carrots")
    that helps but it's not enough
    >>> print machine("carrots")
    congratulations, you attained salvation
    
    # we don't want to be too healthy
    >>> print machine("carrots")
    Traceback (most recent call last):
    ...
    GPDAError: no valid transition using this input, given current state salvation

    # oops, need a valid transition
    >>> machine.add_transition(s,s,
    ...   test=lambda x: True if x=="carrots" or x=="exercise"  else False,
    ...   function=lambda x: "don't overdo it")
    >>> print machine("carrots")
    don't overdo it
    
                               
    """
    stack = []
    def __call__(self,input):
        #catch special commands here
        self.processGlobalCommands(input)
        for n in self[self.state]:   #check neighbor states
            if self[self.state][n]['test'](input):
                output = self[self.state][n]['function'](input)
                self.set_state(n)
                return output
        raise GPDAError("no valid transition using this input, given current state %s"%self.state.name)
    
    def processGlobalCommands(self,input):
        pass
    def __init__(self):
        super(GPDA,self).__init__()
    def add_state(self,s):
        if not isinstance(s,State):
            raise TypeError()
        self.add_node(s)
    def add_transition(self,s1,s2,
                       test=lambda *args:True,
                       function=lambda *args:"",
                       weight=1.0):
        if not isinstance(s1,State):
            raise TypeError()
        if not isinstance(s2,State):
            raise TypeError()
        self.add_edge(s1,s2,test=test,function=function)
    def set_state(self,s):
        if s not in self.nodes():
            raise GPDAError()
        self.state = s




if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
