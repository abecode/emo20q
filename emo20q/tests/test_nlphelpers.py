from emo20q.nlphelper import (isReady, classifyYN, isAffirmative,
                              isQuestion, splitCommaList,
                              GenerateDeclarative)


def test_isready():
    '''tests for answers to the question "are you ready to play"'''
    assert any([isReady("go"), isReady("ready"), isReady("yea"),
                isReady("sure"), isReady("ok")])

def test_classifyyn():
    '''classify whether yes/1 or no/-1 or other/0 '''
    assert classifyYN("aye") == 1
    assert classifyYN("fasdfasdf") == 0
    assert classifyYN("nope") == -1

def test_isaffirmative():
    assert isAffirmative("aye") == True
    assert isAffirmative("fasdfasdf") == False
    assert isAffirmative("nope") == False

def test_isquestion():
    assert isQuestion("Everything is fine.") == False
    assert isQuestion("Is everything fine?") == True

def test_splitcommalist():
    l = splitCommaList("one, two, buckle my shoe, three, and four")
    assert l == ['one', 'two', 'buckle my shoe', 'three', 'four']
    
def test_declarative_generator():
    ''' work in progress '''
    gd = GenerateDeclarative()
    assert gd.generate('directed(e,otherPerson)') == \
        "it is directed at another person"

    attested = ['{e:it} is an emotion that you feel at least once every one or two days',
                '{e:it} is an everyday occurring emotion',
                '{e:it} is something you feel often',
                '{e:it} is a common everyday emotion to experience',
                '{e:it} is a common emotion that people would feel on a fairly regular basis',
                '{e:it} is an emotion people experience every day',
                '{e:it} is an emotion that you feel regularly']
    templates = set(gd.allTemplates('e.frequency==regularly'))

    for a in attested:
        assert a in templates

    assert gd.__call__("e.valence==positive", "yes")  == "it is positive"
    # the following is the same as __call__
    assert gd("e.valence==positive", "no")  == "it is not a good feeling"
    assert gd("e.valence==positive", "xxx")  == "maybe it is positive"

    
