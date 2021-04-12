"""Note: at the moment, these are more of integration tests than
proper unit tests
"""
import pytest
from emo20q.gamedata import (HumanHumanTournament,
                             HumanComputerTournament,
                             HumanComputerCouchJsonTournament)


@pytest.fixture
def hht():
    '''loads data from the human-human emo20q tournaments'''
    return HumanHumanTournament()
@pytest.fixture
def hct():
    '''loads data from the human-computer emo20q tournaments.  this is
    pilot data from before the mturk data collection
    '''
    return HumanComputerTournament()
@pytest.fixture
def hcmt():
    '''loads data from the human-computer emo20q tournaments.  this is
    pilot data from before the mturk data collection
    '''
    return HumanComputerCouchJsonTournament()

def test_humanhumantournament_len(hht):
    '''checks that the number of human-human emo20q games'''
    assert len(hht.matches) == 110

def test_humanhumantournament_match10(hht):
    '''checks the 10th match, a just random check'''
    match10 = hht.matches[10]
    # first turn
    turns = match10.turns
    assert turns[0].q == "is it humorous one?"
    assert turns[0].qgloss == "subset(e,humorous)"
    assert turns[0].a == "no, serious."
    assert turns[0].agloss == "no"
    assert match10.emotion == "thankfulness"
    assert match10.start == "2011-02-14 16:04:52"
    assert int(match10.numquestions) == 9
    assert match10.outcome == "failure/giveup"

def test_humanhumantournament_emotions(hht):
    '''checks the emotions in the dataset

    change this test if more data is collected

    slashes denote when an answerer settled for a synonym
    '''
    attested_emotions = ['admiration',
                         'adoration',
                         'affection',
                         'affection/love',
                         'amusement',
                         'anger',
                         'annoyance',
                         'annoyance/irritated',
                         'anxiety',
                         'apathy/uninterested',
                         'awe',
                         'boredom',
                         'bravery',
                         'calm',
                         'cheerfulness',
                         'confidence',
                         'confusion',
                         'contempt',
                         'contentment',
                         'contentment/calm',
                         'depression',
                         'depression/misery',
                         'devastation',
                         'disappointment',
                         'disgust',
                         'dread/hopelessness',
                         'eagerness/determination',
                         'embarrassment',
                         'enthusiasm',
                         'enthusiasm/eagerness',
                         'envy',
                         'envy/jealousy',
                         'exasperation',
                         'excitement',
                         'exhaustion',
                         'exhilaration/thrill',
                         'fear/distress',
                         'fear/scared',
                         'frustration',
                         'fury',
                         'glee',
                         'gratefulness',
                         'grumpiness',
                         'guilt',
                         'guilt/regret',
                         'happiness',
                         'helpless',
                         'hope',
                         'hope/feelingLucky',
                         'insecurity/shyness',
                         'jealousy',
                         'jealousy/envy',
                         'joy',
                         'loneliness',
                         'love',
                         'mad/anger',
                         'melancholy',
                         'pity/sympathy',
                         'pride',
                         'proud',
                         'regret',
                         'relief',
                         'sadness',
                         'satisfaction',
                         'serenity',
                         'shame',
                         'shock',
                         'shyness',
                         'silly',
                         'soberness',
                         'sorrow/sadness',
                         'stress',
                         'suffering',
                         'surprise',
                         'tense/uncomfortable',
                         'terror',
                         'thankfulness',
                         'thrill',
                         'thrill/entrancement',
                         'tiredness',
                         'wariness',
                         'worry',
                         'worry/anxiety',
                         'worry/scared']
    emotions_in_data = set([m.emotion for m in hht.matches])
    for e in attested_emotions:
        assert e in emotions_in_data

    
def test_humancomputertournament_len(hct):
    ''' this one has len 110 too, just coincidence'''
    assert len(hct.matches) == 110

def test_humancomputertournament_match11(hct):
    '''checks the 11th match, a just random check 

    in the pilot data the turns are not structured matches, each match
    just has one turn

    '''
    match11 = hct.matches[11]
    assert len(match11.turns) == 1
    assert match11.emotion == "euphoria"

def test_humancomputertournament_emotions(hct):
    '''checks the emotions in the dataset

    change this test if more data is collected

    slashes denote when an answerer settled for a synonym
    '''
    attested_emotions = ['acting',
                         'agitation',
                         'anger',
                         'annoyed',
                         'apathy',
                         'cheerfulness',
                         'confusion',
                         'depression',
                         'disappointment',
                         'disgust',
                         'dissatisfied',
                         'dumbfounded',
                         'elation',
                         'embarrassment',
                         'envy',
                         'euphoria',
                         'excited',
                         'excitement',
                         'fear',
                         'frustration',
                         'fury',
                         'happiness',
                         'hatred',
                         'hope',
                         'hostility',
                         'jealousy',
                         'jilted',
                         'let down',
                         'love',
                         'lust',
                         'nervousness',
                         'nostalgia',
                         'nothing',
                         'obsession',
                         'pride',
                         'proud',
                         'regret',
                         'relaxation',
                         'remorse',
                         'resentment',
                         'sadness',
                         'sarcasm',
                         'sorrow',
                         'surprise',
                         'suspicion',
                         'thankfulness/gratefulness',
                         'tiredness']

    emotions_in_data = set([m.emotion for m in hct.matches])
    for e in attested_emotions:
        assert e in emotions_in_data

def test_humancomputercouchjsontournament_len(hcmt):
    ''' this one has len 110 too, just coincidence'''
    assert len(hcmt.matches) == 349

def test_humancomputercouchjsontournament_match10(hcmt):
    '''checks the 10th match, a just random check 

    in the pilot data the turns are not structured matches, each match
    just has one turn

    '''
    match = hcmt.matches[10]
    assert len(match.turns) == 20
    assert match.emotion == "melancholy"
    assert match.turns[1].q == "ok is it a negative emotion?"
    assert match.turns[1].qgloss == "e.valence==negative"
    assert match.turns[1].a == "yes"
    assert match.turns[1].agloss == "yes"
    
    

def test_humancomputercouchjsontournament_emotions(hcmt):
    '''checks the emotions in the dataset

    change this test if more data is collected

    '''
    attested_emotions = ['accepting', 'aggravation', 'agitation',
                         'alienation', 'ambiguity', 'ambivalence',
                         'anger', 'angry', 'annoyance', 'anxiety',
                         'apathy', 'astounded', 'avarice', 'aversion',
                         'being appalled', 'boredom', 'bravery',
                         'caring', 'coldness', 'concern',
                         'conflicted', 'confusion', 'content',
                         'contentment', 'courage', 'curiosity',
                         'delight', 'delirium', 'depression',
                         'despise', 'disappointment',
                         'discontentment', 'disgust',
                         'disillusionment', 'dissatisfied',
                         'distress', 'downcast', 'downtrodden',
                         'ecstasy', 'educated', 'elation',
                         'embarrassment', 'empathy', 'enamored',
                         'energetic', 'enjoyment', 'envy', 'euphoria',
                         'excitement', 'exhaustion', 'exotic',
                         'exuberance', 'failure', 'fear',
                         'frustration', 'fury', 'happiness', 'hate',
                         'hatred', 'hope', 'hostility', 'hunger',
                         'indifference', 'infuriation',
                         'inquisitiveness', 'inspiration',
                         'introspection', 'irritation', 'jealousy',
                         'joy', 'joyfulness', 'jubilance',
                         'loneliness', 'love', 'loved', 'lust', 'mad',
                         'mania', 'maniacal', 'maudlin', 'melancholy',
                         'mischievous', 'misery', 'morose',
                         'nervousness', 'nostalgia', 'outrage',
                         'overwhelmed', 'patience', 'perplexity',
                         'pessimism', 'pity', 'playfulness',
                         'pleasure', 'quixotic', 'relaxation',
                         'remorse', 'resentment', 'respect',
                         'sadness', 'satisfaction', 'serenity',
                         'shame', 'sleepiness', 'stress', 'stupor',
                         'suffering', 'suicidal', 'surprise',
                         'thrill', 'tiredness', 'unsure', 'upset',
                         'worry']



    emotions_in_data = set([m.emotion for m in hcmt.matches])
    for e in attested_emotions:
        assert e in emotions_in_data
        
