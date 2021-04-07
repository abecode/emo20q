#!/usr/bin/env python3

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
        if isinstance(input_, Question):
            input_.talker = "agent"
            self.append(input_)
        elif isinstance(input_, Answer):
            input_.talker = "user"
            q = self.pop()
            if isinstance(q, Question):
                t = Turn(q, input_)
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
        else:
            raise EpisodicBufferError("Stack content error")
    def newMatch(self):
        del self[:]
    def numTurns(self):
        turns = list(filter(lambda x: isinstance(x, Turn) or isinstance(x, Question), self))
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
        turns = list(filter(lambda x: isinstance(x, Turn), self))
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
            print(jsondata)
        

    
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
    def __init__(self, text, gloss=None):
        self.text = text
        self.gloss = gloss
class AgentUtt(Utterance):
    pass
class UserUtt(Utterance):
    pass
class Question(AgentUtt):
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

class Answer(UserUtt):
    pass
    
class Turn(object):
    def __init__(self, q, a):
        self.q = q
        self.a = a

        
def match2JsonEncoder(x):
    out = {}
    if isinstance(x, Turn):
        out['type'] = 'Turn'
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

    
