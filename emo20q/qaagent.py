#!/usr/bin/env python3

"""A questioner agent based on the notion of a generalized pushdown
automaton, which is just a pushdown automaton that can look at his/her
whole stack
"""
from collections import defaultdict
import doctest
import math
import random
import re
import nltk

from emo20q import nlphelper
from emo20q.gpda import GPDA, State, GPDAError
from emo20q.semanticknowledge import SemanticKnowledge
from emo20q.lexicalaccess import LexicalAccess
from emo20q.episodicbufferqa import (EpisodicBuffer, AgentAskingTurn,
                                     AgentUtt, UserUtt, AgentQuestion,
                                     UserAnswer, IllocutionaryAct)
from emo20q.qa import answer_emotion_question

# tensorflow stuff for question answerer
# for tensorflow/bert
import numpy as np
import tensorflow as tf
# !pip install -q tf-models-official==2.4.0
from official.nlp import bert
import official.nlp.bert.tokenization

# 
tough_emotions = set(["silly", "feelingLucky", "stupor", "wariness", "exotic", "exasperation",
                     "devastation", "soberness", "uninterested", "ambiguity", "quixotic", "educated",
                     "nothing", "perplexity", "introspection", "maniacal", "suicidal", "alienation",
                      "pessimism", "failure", "coldness", "despise", "avarice", "caring", "infuriation"])


class QAAgent(GPDA):
    """this class combines the QuestionerAgent (older sequential
    bayes/GPDA agent) with an answerer agent (newer, uses 6T5,
    currently doesn't have much state)

    >>> agent = QAAgent()

    # start in startState
    >>> agent.state.name
    'startState'

    # fire up this ol' automaton
    >>> print(agent(""))
    [Agent enters the universe of discourse]
    Welcome to EMO20Q
    I'm going to try to guess the emotion that you are thinking of
    it needn't be the emotion you are currently feeling
    Let me know when you are ready...

    # test him out
    >>> agent("fasdfadsf")
    'Let me know when you are ready... (some people get stuck here... try typing something into the box to let me know whether you are ready, or not)'

    >>> print(agent("ok fine")) #doctest: +ELLIPSIS
    Ok, let me see here...
    ...

    # this just tests that the dialog will go to 20 questions, make a guess, and log the dialog
    
    >>> print(agent("no")) #doctest: +ELLIPSIS
    1
    ...
    >>> print(agent("no")) #doctest: +ELLIPSIS
    2
    ...
    >>> print(agent("no")) #doctest: +ELLIPSIS
    3
    ...
    >>> print(agent("no")) #doctest: +ELLIPSIS
    4
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    5
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    6
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    7
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    8
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    9
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    10
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    11
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    12
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    13
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    14
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    15
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    16
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    17
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    18
    ...

    >>> print(agent("no")) #doctest: +ELLIPSIS
    19
    ...

    >>> agent("yes") #doctest: +ELLIPSIS
    20
    'so did I get it right?'

    >>> print(agent("yes")) #doctest: +ELLIPSIS
    Awesome!
    Now let's switch roles.  I'll pick the emotion and you ask the questions.

    >>> print(agent("ok"))
    Okay, I'm ready for questions

    >>> print(agent("Is it an emotion?")) #doctest: +ELLIPSIS
    maybe...

    >>> agent.episodicBuffer.chosen_emotion = "sadness" 

    >>> print(agent("Is it a positive emotion?")) #doctest: +ELLIPSIS
    no...

    >>> print(agent("Is it a negative emotion?")) #doctest: +ELLIPSIS
    yes...

    >>> print(agent("Is it sadness?")) #doctest: +ELLIPSIS
    yes, I picked sadness.  Good job!

    >>> print(agent("what now?")) #doctest: +ELLIPSIS
    Thank you for playing
    ...

    # test end state:
    >>> agent = QAAgent()

    >>> QAAgent("")  #doctest: +ELLIPSIS
    <qaagent.QAAgent object ...

    >>> print(agent("ready")) #doctest: +ELLIPSIS
    [Agent enters the universe of discourse]
    ...

    >>> print(agent("yes")) #doctest: +ELLIPSIS
    Ok, let me see here...
    ...

    >>> print(agent("yes")) #doctest: +ELLIPSIS
    1
    ...
    >>> agent("yes") #doctest: +ELLIPSIS
    2
    ...
    >>> agent("yes") #doctest: +ELLIPSIS
    3
    ...

    >>> agent("yes") #doctest: +ELLIPSIS
    4
    ...

    >>> agent("yes") #doctest: +ELLIPSIS
    5
    ...

    >>> agent("yes") #doctest: +ELLIPSIS
    Awesome!\nNow let's switch roles.  I'll pick the emotion and you ask the questions.


    >>> agent("is it a positive emotion?") #doctest: +ELLIPSIS
    no
    ..
    
    """

    startState = State("startState")
    welcomeState = State("welcomeState")
    askingState = State("askingState")
    confirmingState = State("confirmingState")
    reviewingState = State("reviewingState")
    betweenMatchesState = State("betweenMatchesState")
    answeringState = State("answeringState")
    answeringFeedbackState = State("answeringFeedbackState")
    lastQuestionToAnswer = State("lastQuestionToAnswer")
    endState = State("endState")



    def __init__(self,
                 episodicBuffer=EpisodicBuffer(),
                 semanticKnowledge=SemanticKnowledge(),
                 lexicalAccess=LexicalAccess() ):
        super(QAAgent,self).__init__()
        self.episodicBuffer = episodicBuffer
        self.semanticKnowledge = semanticKnowledge
        self.lexicalAccess = lexicalAccess
        self.stack = self.episodicBuffer


        self.belief =  nltk.probability.UniformProbDist(self.semanticKnowledge.entities())
        # to welcome message from startState
        self.add_transition(self.startState,self.welcomeState,
                            test=lambda x: True, #transition on any input
                            function=self.welcomeMessage)
        # reprompt til ready (loop in welcomeState)
        self.add_transition(self.welcomeState,self.welcomeState,
                            test=lambda x: not nlphelper.isReady(x),
                            function=lambda x: "Let me know when you are ready... (some people get stuck here... try typing something into the box to let me know whether you are ready, or not)",
                            )
        #start match, to asking state from welcomeState
        self.add_transition(self.welcomeState,self.askingState,
                            test=nlphelper.isReady,
                            function=self.beginPlaying)
        #main asking loop
        self.add_transition(self.askingState,self.askingState,
                            test=self.shouldIAsk,
                            function=self.evaluateQuestionAnswer)
        self.add_transition(self.askingState,self.confirmingState,
                            test=lambda x: nlphelper.isAffirmative(x) and self.episodicBuffer[-1].isIdentityQuestion(),
                            function=self.confirmAnswer)
        #sucess! to betweenMatchesState from confirmingState
        self.add_transition(self.confirmingState,self.betweenMatchesState,
                            test=nlphelper.isAffirmative,
                            function=lambda x: self.doYouWantToPlayAgain(x,outcome="success"))
        #a failed guess w/ <20 questions, to askingState from confirmingState
        self.add_transition(self.confirmingState,self.askingState,
                            test=lambda x: not nlphelper.isAffirmative(x) and self.shouldIAsk(x),
                            function=self.evaluateQuestionAnswer)
        #a failed guess, >20 questions, to reviewingState
        self.add_transition(self.confirmingState,self.reviewingState,
                            test=lambda x: not nlphelper.isAffirmative(x) and self.episodicBuffer.numTurns()>=20,
                            function=self.reviewAnswerAfterDisconfirm)
        #ran out of questions, ask what the emotion was, to reviewingState
        self.add_transition(self.askingState,self.reviewingState,
                            test=self.shouldIReview,
                            function=self.reviewAnswer)
        #failed match, but try again, to betweenMatchesState from reviewingState
        self.add_transition(self.reviewingState,self.betweenMatchesState,
                            test=lambda x: True,
                            function=lambda x: self.doYouWantToPlayAgain(x,outcome="failure"))
        #switch to answering
        self.add_transition(self.betweenMatchesState,self.answeringState,
                            test=nlphelper.isQuestion,
                            function=lambda q: self.answerQuestion(q))
        #if we get a non question in the between answering state
        self.add_transition(self.betweenMatchesState,self.betweenMatchesState,
                            test=lambda x: not nlphelper.isQuestion(x),
                            function=lambda x: "Okay, I'm ready for questions")
        #question answering loop
        self.add_transition(self.answeringState, self.answeringState,
                            test=self.keepAnswering,
                            function=lambda q: self.answerQuestion(q))
        # if we get a non-question
        self.add_transition(self.answeringState, self.answeringFeedbackState,
                            test=lambda x: not self.keepAnswering(x) and not self.episodicBuffer.user_guessed_correctly and not self.episodicBuffer.question_number==20,
                            function=lambda q: self.giveQAFeedback(q))
        # if we get another non-question
        self.add_transition(self.answeringFeedbackState, self.answeringFeedbackState,
                            test=lambda x: not self.keepAnswering(x) and not self.episodicBuffer.user_guessed_correctly,
                            function=lambda q: self.giveQAFeedback(q))
        # back to the loop
        self.add_transition(self.answeringFeedbackState, self.answeringState,
                            test=self.keepAnswering,
                            function=lambda q: self.answerQuestion(q))
        #last question
        self.add_transition(self.answeringState, self.lastQuestionToAnswer,
                            test=lambda x: self.episodicBuffer.question_number>=19,
                            function=lambda q: self.twentiethQuestion(q))
        # end
        self.add_transition(self.answeringState,self.endState,
                            test=lambda x: self.episodicBuffer.user_guessed_correctly,
                            function=self.goodbyeMessage)
        self.add_transition(self.answeringFeedbackState, self.endState,
                            test=lambda x: self.episodicBuffer.question_number>=20,
                            function=lambda q: self.answerQuestion(q))


        self.state = self.startState
    def processGlobalCommands(self,input):
        if re.match(r':quit',input):
            raise GPDAError("endState via :quit")
    def welcomeMessage(self,input):
        output = "[Agent enters the universe of discourse]\n"
        output += "Welcome to EMO20Q\n"
        output += "I'm going to try to guess the emotion that you are thinking of\n"
        output += "it needn't be the emotion you are currently feeling\n"
        output += "Let me know when you are ready..."
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def replayMessage(self,input):
        self.episodicBuffer.newMatch()
        self.episodicBuffer.add(UserUtt(input))
        output = "Cool.  Let me know when you think of another emotion...\n"
        output += "Let me know when you are ready..."
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def goodbyeMessage(self,input):
        self.episodicBuffer.add(UserUtt(input))
        output = "Thank you for playing"
        output += "\nif you have any questions or comments please email (anonymized for review)"
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def beginPlaying(self,input):
        self.episodicBuffer.add(UserUtt(input))
        output = "Ok, let me see here... \n"
        nextQ = self.pickNextQuestion()
        output += self.lexicalAccess.lookUp(nextQ)
        self.episodicBuffer.add(AgentQuestion(output,gloss=nextQ))
        return output
    def evaluateQuestionAnswer(self,input):
        self.episodicBuffer.add(UserAnswer(input))
        if self.episodicBuffer.numTurns() >= 20:
            raise GPDAError("shouldn't be asking with 20 or more questions")
        #output = "ok, I see.  Number %s. Is it a bla bla bla?"%str(self.episodicBuffer.numTurns()+1)
        ##############################
        #update belief: key part!
        ##############################
        features = self.episodicBuffer.getFeatures()
        self.semanticKnowledge.setPriors(self.belief)
        post = self.semanticKnowledge.prob_classify(features)

        # if last question was an identity question (guess), then zero out that emotion
        if isinstance(self.episodicBuffer[-1],AgentAskingTurn) and \
                hasattr(self.episodicBuffer[-1].q, "isIdentityQuestion") and \
                self.episodicBuffer[-1].q.isIdentityQuestion():
            match = re.search(r'^e==(.+)$', self.episodicBuffer[-1].q.gloss)
            tmpDict = dict((key, post.prob(key)) for key in post.samples())
            tmpDict[match.group(1)] = 0
            #print sorted([key for key in tmpDict], key=tmpDict.__getitem__,reverse=True)
            post = nltk.probability.DictionaryProbDist(tmpDict,normalize=True)
        # if last question was an identity question (guess), then zero out that emotion
        # slightly messy having reduplication here: to deal with a disconfirmed confirmation
        if isinstance(self.episodicBuffer[-3],AgentAskingTurn) and \
                hasattr(self.episodicBuffer[-3].q, "isIdentityQuestion") and \
                self.episodicBuffer[-3].q.isIdentityQuestion():
            match = re.search(r'^e==(.+)$', self.episodicBuffer[-3].q.gloss)
            tmpDict = dict((key, post.prob(key)) for key in post.samples())
            tmpDict[match.group(1)] = 0
            #print sorted([key for key in tmpDict], key=tmpDict.__getitem__,reverse=True)
            post = nltk.probability.DictionaryProbDist(tmpDict,normalize=True)

        #deal with similarity questions
        if isinstance(self.episodicBuffer[-1],AgentAskingTurn) and \
                hasattr(self.episodicBuffer[-1].q, "isSimilarityQuestion") and \
                self.episodicBuffer[-1].q.isSimilarityQuestion() and \
                nlphelper.classifyYN(self.episodicBuffer[-1].a.text)==-1:
            match = re.search(r'^similar(e,.+)$', self.episodicBuffer[-1].q.gloss)
            tmpDict = dict((key, post.prob(key)) for key in post.samples())
            tmpDict[match.group(1)] = 0
            #print sorted([key for key in tmpDict], key=tmpDict.__getitem__,reverse=True)
            post = nltk.probability.DictionaryProbDist(tmpDict,normalize=True)

        self.belief = post
        b = Belief(self.belief)
        #print(sorted(self.belief.samples, key=self.belief.prob))
        print(b)
        print(b.entropy())
        #smoothing
        if b.entropy() < .9:
            tmpDict = {}
            for key in post.samples():
                if post.prob(key) > 0:
                    tmpDict[key] = post.prob(key) + 0.1
                else:
                    tmpDict[key] = 0.0
            post = nltk.probability.DictionaryProbDist(tmpDict,normalize=True)
        self.belief = post
        b = Belief(self.belief)
        print(b.entropy())

        #self.episodicBuffer.add(Belief(self.belief))
        nextQ = self.pickNextQuestion()
        output = self.lexicalAccess.lookUp(nextQ)
        self.episodicBuffer.add(AgentQuestion(output,gloss=nextQ))
        #for x in self.stack:
        #    print x
        return output
    def shouldIAsk(self,input):
        print(self.episodicBuffer.numTurns())
        if hasattr(self.episodicBuffer[-1],'isIdentityQuestion') and \
           self.episodicBuffer[-1].isIdentityQuestion() and \
           nlphelper.isAffirmative(input):
            return False
        if self.episodicBuffer.numTurns() < 20:
            return True
        return False
    def shouldIReview(self,input):
        if self.episodicBuffer.numTurns() >= 20 and \
           not (self.episodicBuffer[-1].isIdentityQuestion() and \
                nlphelper.isAffirmative(input)):
            return True
        return False
    def confirmAnswer(self,input):
        self.episodicBuffer.add(UserAnswer(input))
        output = "so did I get it right?"
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def reviewAnswer(self,input):
        self.episodicBuffer.add(UserAnswer(input))
        output = "Dammit, that is disappointing... \n"
        output += "Well, what was the emotion that you picked?"
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def reviewAnswerAfterDisconfirm(self,input):
        self.episodicBuffer.add(UserUtt(input))
        output = "Dammit, that is disappointing... \n"
        output += "Well, what was the emotion that you picked?"
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def doYouWantToPlayAgain(self,input,outcome=None):
        """ this is currently not used in the acii 2022 demo system"""
        #########################################################
        # This is where serialization to couchdb should happen
        #########################################################
        self.episodicBuffer.save()
        self.episodicBuffer.add(UserUtt(input))
        self.belief = nltk.probability.UniformProbDist(self.semanticKnowledge.entities())
        
        output = str()
        if outcome == "success":
            output = "Awesome!\n"
        output += "Now let's switch roles.  I'll pick the emotion and you ask the questions."
        self.episodicBuffer.add(AgentUtt(output))
        return output
    def pickNextQuestion(self,randomize=False):
        #sort the question/features by probability of being != None
        #self.send("starting to pick next question based on the following features in my episodic buffer: %s" % str(features))
        features = self.episodicBuffer.getFeatures()
        def sumNotNone(probdist):
            return sum([probdist.prob(x) for x in ("yes","no","other")])
        def sumYes(probdist):
            return probdist.prob("yes")
        probYes = defaultdict(float)

        for ((label, fname), probdist) in self.semanticKnowledge._feature_probdist.items():
            #probNotNone[fname] += sumNotNone(probdist)*self.semanticKnowledge._label_probdist.prob(label)
            #probYes[fname] += sumYes(probdist)*self.semanticKnowledge._label_probdist.prob(label)
            probYes[fname] += sumYes(probdist)*self.belief.prob(label)
        #we pick the question that is the maximum probability of being yes
        #among the questions not asked already
        if not randomize:
            result = max([x for x in probYes if x not in features],key=probYes.__getitem__)
        else:
            result = max([x for x in probYes if x not in features if not x.startswith("e==")],
                         key=lambda x: probYes[x]*random.random())
        match = re.search(r'^e==(.+)$', result)
        # if identity question or turnCount==20, choose from belief vector
        #if  match or self.episodicBuffer.numTurns()>=18 or Belief(self.belief).entropy()<2:  #choose an ID question (guess)
        if  match or self.episodicBuffer.numTurns()>=18 or Belief(self.belief).entropy()<2.4:  #choose an ID question (guess)
            if True:
                guess = sorted(self.semanticKnowledge._label_probdist.samples(),key=self.belief.prob,reverse=True)[0]
            else:
                guess = sorted(self.semanticKnowledge._label_probdist.samples(),
                               key= lambda x: self.belief.prob(x)*random.random(),reverse=True)[0]
            return "e==%s" % guess
        else:
            return result
    def printTopQuestions(self,n=10,wrs=False):
        #sort the question/features by probability of being != None
        #self.send("starting to pick next question based on the following features in my episodic buffer: %s" % str(features))
        features = self.episodicBuffer.getFeatures()
        def sumNotNone(probdist):
            return sum([probdist.prob(x) for x in ("yes","no","other")])
        def sumYes(probdist):
            return probdist.prob("yes")
        probYes = defaultdict(float)

        for ((label, fname), probdist) in self.semanticKnowledge._feature_probdist.items():
            #probNotNone[fname] += sumNotNone(probdist)*self.semanticKnowledge._label_probdist.prob(label)
            probYes[fname] += sumYes(probdist)*self.semanticKnowledge._label_probdist.prob(label)
        #we pick the question that is the maximum probability of being yes
        #among the questions not asked already
        if wrs:
            result = sorted([x for x in probYes if x not in features],key=lambda x:probYes[x]*random.random(), reverse=True)
        else:
            result = sorted([x for x in probYes if x not in features],key=probYes.__getitem__, reverse=True)
        return result[0:n]
    def emotions(self):
        """returns a list of emotions that the agent knows about 

        this is the start of the new functions added for the acii 2022
        demo agent
        """
        return list(self.semanticKnowledge._labels)
    def pickEmotion(self):
        """ picks a random emotion from the set of emotions
        used for the question answering role
        """
        self.episodicBuffer.chosen_emotion = random.choice(list(set(self.emotions())-tough_emotions)) # set the chosen emotion
        self.episodicBuffer.add(IllocutionaryAct(type="ChooseEmotion",
                                                 emotion=self.episodicBuffer.chosen_emotion))
        self.episodicBuffer.question_number = 1  # set the question number
        self.episodicBuffer.user_guessed_correctly = False
        return self.episodicBuffer.chosen_emotion
    def answerQuestion(self, question):
        """ answer questions and respond to guesses"""
        # for first turn
        if not getattr(self.episodicBuffer, "chosen_emotion", None):
            self.pickEmotion()
        self.episodicBuffer.add(UserUtt(question))
        #print(self.episodicBuffer.chosen_emotion, self.episodicBuffer.question_number)
        # a correct guess
        if self.episodicBuffer.chosen_emotion.lower() in question.lower():
            reply = f"yes, I picked {self.episodicBuffer.chosen_emotion}.  Good job!"
            self.episodicBuffer.user_guessed_correctly = True
            return reply
        # a correct guess, but maybe a synonym
        answer = answer_emotion_question(self.episodicBuffer.chosen_emotion, question)
        if answer == "yes" and self.isGuess(question):
            reply = "yes, but that's not the exactly what I picked"
            return reply
        # a question
        reply = f"{answer} (that was question {self.episodicBuffer.question_number})"
        self.episodicBuffer.question_number += 1
        self.episodicBuffer.add(AgentUtt(reply))
        return reply
    def keepAnswering(self, input_):
        if self.episodicBuffer.user_guessed_correctly:
            return False
        if nlphelper.isQuestion(input_) and self.episodicBuffer.question_number <= 19:
            return True
        return False
    def twentiethQuestion(self, question):
        """ last question"""
        print(self.episodicBuffer.chosen_emotion, self.episodicBuffer.question_number)
        # a correct guess
        if self.episodicBuffer.chosen_emotion.lower() in question.lower():
            reply = f"yes, I picked {self.episodicBuffer.chosen_emotion}.  Good job!"
            self.episodicBuffer.user_guessed_correctly = True
            return reply
        # a correct guess, but maybe a synonym
        answer = answer_emotion_question(self.episodicBuffer.chosen_emotion, question)
        if answer == "yes":
            reply = f"yes, that's not the exactly what I picked, {self.episodicBuffer.chosen_emotion}, but I'll say it's close enough."
            self.episodicBuffer.user_guessed_correctly = True
            return reply
        # a question
        reply = f"Doh! That was the last question... the emotion I picked is {self.episodicBuffer.chosen_emotion}"
        self.episodicBuffer.question_number += 1
        return reply
    def giveQAFeedback(self, input_):
        reply = "Sorry, I'm not a human so I need input formatted as a question or I'll get confused"
        reply += f"(you are on question number {self.episodicBuffer.question_number}"
        return reply
    def isGuess(self, input_):
        m = re.search(r" *is it (.*)\??", input_)
        if m and m.groups(0) in self.emotions():
            return True
        m = re.search(r" *(.*)\??", input_)
        if m and m.groups(0) in self.emotions():
            return True
    
class Belief(dict):
    def __init__(self, probdist):
        """Takes an nltk probdist and returns a dict/multinomial distribution"""
        for key in probdist.samples():
            self[key] = probdist.prob(key)
    def __repr__(self):
        output = "Belief({\n"
        for x in sorted([key for key in self], key=self.__getitem__):
            output += "'%s':'%s'\n"%(x, self[x])
        output += "})"
        return output
    def entropy(self):
        result = 0
        for x in self:
            if self[x] != 0:
                result += self[x]*math.log(self[x],2)
        return -result

if __name__ == "__main__":
    import argparse
    argParser = argparse.ArgumentParser(description="""A generalized pushdown automaton implementation of an EMO20Q questioner agent.  """)
    argParser.add_argument('-t', '--test',
                           action='store_true',
                           help='test using doctest')
    argParser.add_argument('--run',
                           action='store_true',
                           help='run the agent interactively on the commandline')
    args = argParser.parse_args()
    if args.test:
        import doctest
        doctest.testmod()
    #elif args.run:
    else:
        agent = QAAgent()
        input_ = ""
        print(agent(input_))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        print(agent("yes"))
        for x in range(0,19):
            print(agent("is it happy?"))
            
        while True:
            print(agent.state.name)
            print(agent(input_))
            print(agent.state.name)
            input_ = input("> ")
