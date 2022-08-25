#!/usr/bin/env python3

"""The question answering role (user asks questions, agent picks the
emotion and answers questions) required some refactoring of the
EpisodicBuffer class as well as Turn, UserUtt, AgentUtt, etc.  This is
because the previous scenario only had the agent as the question
asker, so all questions were always agent utterances and all answers
were user utterances. I considered doing something more clever
(e.g. subclassing EpisodicBuffer) but I desided against it because of
the other classes involved.

The qa role was actually using the original EpisodicBuffer class, but
it wasn't saving the turns in the episodic buffer.  When I tried to
save the data, I realized it was not possible because Turns would need
to have questions asked by the user.

"""

from datetime import datetime as dt
import json
import os
import re
import sys
import time
from emo20q import nlphelper

DIRNAME = os.path.dirname(os.path.realpath(__file__))

SAVEPARAMS =  {'experiment': "uncontrolled",
               'wave': "n/a",
               'provenance': ['notebook', 'text', 'gpdaquestioner',
                              'human-computer', ],
} 


class EpisodicBufferError(Exception):
    pass

class EpisodicBuffer(list):
    def __init__(self):
        super(list, self).__init__()
    def add(self, input_, semantics=None):
        input_.semantics = semantics
        if isinstance(input_, AgentQuestion):
            input_.talker = "agent"
            self.append(input_)
        elif isinstance(input_, UserAnswer):
            input_.talker = "user"
            q = self.pop()
            if isinstance(q, AgentQuestion):
                t = AgentAskingTurn(q, input_)
                self.append(t)
            elif isinstance(q, AgentUtt):
                self.append(q)
                self.append(input_)
            else:
                raise EpisodicBufferError("Stack content error")
        elif isinstance(input_, AgentUtt):
            input_.talker = "agent"
            self.append(input_)
        elif isinstance(input_, UserUtt):
            input_.talker = "user"
            self.append(input_)
        elif isinstance(input_, IllocutionaryAct):
            self.append(input_)
        else:
            raise EpisodicBufferError("Stack content error")
    def newMatch(self):
        del self[:]
    def numTurns(self):
        turns = list(filter(lambda x: isinstance(x, AgentAskingTurn) or isinstance(x, AgentQuestion), self))
        return len(turns)
    def getFeature(self,q,a):
        if(not q.gloss): 
            raise EpisodicBufferException("no gloss")
        answer = None
        if nlphelper.classifyYN(a.text) == 1 : answer = "yes"
        elif nlphelper.classifyYN(a.text) == -1  : answer = "no"
        else : answer = "other"
        return (q.gloss,answer)
    def getFeatures(self):
        turns = list(filter(lambda x: isinstance(x, AgentAskingTurn), self))
        features = {}
        for x in turns:
            f = self.getFeature(x.q, x.a)
            features[f[0]] = f[1]
        return features

    def save(self):
        m = {}
        m['type'] = 'Dialog'
        ts = "%s-%s-%s %s:%s:%s"%tuple( map(lambda x: getattr(time.gmtime(), x),
                                            ['tm_year','tm_mon','tm_mday', 'tm_hour', 'tm_min',
                                             'tm_sec'])) #this line is a bit terse, sorry
        
        m['param'] = SAVEPARAMS
        m['param']['date'] = ts
        m['container'] = [x for x in self]

        timestamp = dt.utcnow().strftime("%Y%m%dT%H%M%S")
        jsondata = json.dumps(m, sort_keys=True, indent=2, default=match2JsonEncoder)

        LOGDIR = os.getenv("EMO20Q_LOGDIR")
        if LOGDIR:
            with open(os.path.join(DIRNAME, LOGDIR, f"dialog-{timestamp}.json"), "w") as f:
                print(jsondata, file=f)
        else:
            #print(jsondata)
            pass

    
    def saveCouchDB(self,db="couchdb"):
        import couchdb
        import time
        import json
        import sys #only used for debugging
        # -maybe check if there is an identifier, to sync/updata 
        #  rather than creating a new document
        # - save agent state info?
        #return {}

        m = {}
        m['type']='Dialog'
        m['param']= {
            'exp': "uncontrolled",
            'wave':"000",
            'provenance': ['http','text','web','gpdaquestioner','human-computer','mturk'],
            'date': "%s-%s-%s %s:%s:%s"% tuple( map(lambda x: getattr(time.gmtime(), x), ['tm_year','tm_mon','tm_mday', 'tm_hour', 'tm_min', 'tm_sec'])) #this line is a bit terse, sorry
            } 
        m['container'] =[ x for x in self]
        #create empty dialog in couch
        print(json.dumps(m,sys.stdout,sort_keys=True, indent=2, default=match2JsonEncoder))
        #db = couchdb.client.Database("http://ark.usc.edu:5984/emo20q_webdata")
        #db = couchdb.client.Database("https://emo20q.iriscouch.com:6984/emo20q_webdata")
        db = couchdb.client.Database("http://localhost:5984/emo20q_webdata")
        doc_id, doc_rev = db.save(json.loads(json.dumps(m,sys.stdout,default=match2JsonEncoder,sort_keys=False, indent=2)))
        print(doc_id, doc_rev)

# TODO: these classes somewhat duplicate the classes in gamedata. The
# Turn, Question, Answer in that library deal with reading saved data,
# and these are for writing it.  Consider combining them.

class Utterance():
    def __init__(self, text, gloss=None, is_agent=False):
        self.text = text
        self.gloss = gloss
        self.is_agent = is_agent
    def __str__(self):
        d = {"text": self.text,
             "gloss": self.gloss,
             "is_agent": self.is_agent}
        return f"Utterance({d})"
class AgentUtt(Utterance):
    def __init__(self, text, gloss=None):
        super().__init__(text, gloss, is_agent=True)
class UserUtt(Utterance):
    def __init__(self, text, gloss=None):
        super().__init__(text, gloss, is_agent=False)
class AgentQuestion(AgentUtt):
    def isIdentityQuestion(self):
        if re.search(r'^e==(.+)$', self.gloss):
            return True
        else:
            return False
    def isSimilarityQuestion(self):
        if re.search(r'^similar(e,.+)$', self.gloss):
            return True
        else:
            return False
class UserAnswer(UserUtt):
    pass
    
class AgentAskingTurn():
    def __init__(self, q, a):
        self.q = q
        self.a = a
    def __str__(self):
        return f"AgentAskingTurn({self.q}, {self.a})"

class IllocutionaryAct():
    def __init__(self, type, **args):
        self.type = type
        self.args = args
    def __str__(self):
        return f"IllocutionaryAct({self.type}, {self.args})"
        
def match2JsonEncoder(x):
    out = {}
    if isinstance(x, AgentAskingTurn):
        out['type'] = 'AgentAskingTurn'
        out['container'] = [{'type':'Question',
                             'param':{'text':x.q.text,
                                      'gloss':x.q.gloss}},
                            {'type':'Answer',
                             'param':{'text':x.a.text,
                                      'gloss':x.a.gloss}}]
        return out
    if isinstance(x, UserUtt):
        out['type'] = 'UserUtt'
        out['param'] = {'text':x.text}
        return out
    if isinstance(x, AgentUtt):
        out['type'] = 'AgentUtt'
        out['param'] = {'text':x.text}
        return out
    if isinstance(x, IllocutionaryAct):
        out['type'] = x.type
        out['param'] = x.args


