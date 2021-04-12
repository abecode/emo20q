import pytest
from emo20q.lexicalaccess import LexicalAccess


@pytest.fixture
def la():
    '''lexical access object'''
    return LexicalAccess()

def test_lexicalaccess(la):
    '''test all the realizations of one example gloss:
    directed(e,otherPerson)
    '''

    attested = ['Is it directed at another person?',
                'is it something that is directed towards someone?',
                'is the emotion directed towards another person?',
                '3: is it an emotion that is directed at another person?',
                'is it an emotion that is directed at another person',
                'is it an emotion that can be directed at another person?',
                "is it an emotion that's directed at another person?",
                'can the emotion be directed at another person?',
                'is it directed at some other person?',
                '3) is it directed towards another person?',
                'is it something you feel towards someone else?',
                'is it towards some other person',
                'can it be directed at another person?',
                '7) is it directed at another person?',
                '11) is it directed toward another person?',
                '3)is it directed towards another person?',
                'can it also be directed at another person?',
                'do you feel it toward another person',
                'is it an emotion toward someone else?',
                'is it the other person that the emotion is directed at?',
                'is it directed at someone else?']

    realizations = set([realization for
                    realization in
                    la._dictionary['directed(e,otherPerson)']])

    for a in attested:
        assert a in realizations

    
