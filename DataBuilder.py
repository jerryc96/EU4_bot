import re
import glob
import ClauseWizard
import json

from triggers.trigger import Trigger
from culture.cultureLoader import *

countryDirectory = "./history/countries"
tagFile = './common/country_tags/00_countries.txt'

uniqueIdeasFile = './common/ideas/00_country_ideas.txt'

# for group ideas
groupIdeasFile = './common/ideas/zz_group_ideas.txt'

# for generic ideas
genericIdeasFile = './common/ideas/zzz_default_idea.txt'

# for Eu4 Idea Groups
basicIdeasFile = './common/ideas/00_basic_ideas.txt'

ideasTokens = './idea_tokens.txt'

allTriggers = './data/triggers.json'
nationalTriggerPath = 'data/nat_idea_triggers.json'
groupTriggerPath = 'data/group_idea_triggers.json'

# for idea set that differ substantially from what is displayed by EU4 UI
nameConverterDict = {
    'spy': 'espionage',
    'default': 'generic'
}

# def gen_tag_library():
#     '''
#     Generate the list of country tags in EU4, found in common/country_tags
#     '''
#     tagMap = {}
#
#     with open(tagFile) as t:
#         data = t.readlines()
#         for line in data:
#             # check for comments
#             if '=' in line and line[0] != '#':
#                 tag = line[0:3]
#                 countryNameSearch = re.search('countries/(.*)\.txt', line)
#                 if countryNameSearch:
#                     countryName = countryNameSearch.group(1)
#                     tagMap[tag] = countryName
#             else:
#                 continue
#     return tagMap
def country_to_tag_library():
    '''
    generate a library, matching country name to tags
    '''
    library = {}
    for countryPath in glob.glob(countryDirectory+'/*.txt'):
        country = countryPath.split("/")[-1]
        country = country.split("-")
        tag = country[0].strip()
        countryName = country[1].strip(".txt").strip()
        countryName = countryName.lower()
        countryName = re.sub('empire', '', countryName)
        library[countryName.strip()] = tag
    return library

def gen_tag_library():
    tagMap = {}
    for countryPath in glob.glob(countryDirectory+'/*.txt'):
        # with open(countryFile, 'r', errors='ignore') as t:
        #     country = ClauseWizard.cwparse(t.read())
        #     countjson = ClauseWizard.cwformat(country)
        # all paths are arranged like so:
        # ./history/countries/{TAG} - {COUNTRY_NAME}.txt
        # the code below extracts the TAG and COUNTRY_NAME
        country = countryPath.split("/")[-1]
        country = country.split("-")
        tag = country[0].strip()
        countryName = country[1].strip(".txt").strip()
        tagMap[tag] = countryName.lower()

    return tagMap

def gen_country_ideas_library():
    '''
    Generate a dict of all idea sets

    EU4 stores its idea sets in several different files as of this moment, so we need to grab each file from the
    file location and collect the ideasets
    '''
    # print(tagLib)
    ideasLib = {}
    add_ideas(uniqueIdeasFile, ideasLib)
    add_ideas(groupIdeasFile, ideasLib)
    add_ideas(genericIdeasFile, ideasLib)
    # add_basic_ideas(basicIdeasFile, ideasLib)
    return ideasLib

def gen_non_national_ideas_library():
    '''
    Generate a library consisting only the idea sets that are not National ideas,

    This is used to set up the fuzzy search algorithm in case the query string matches one of these ideas better than
    a potential country tag.

    Since All EU4 ideas are of the string "IDEANAME_ideas", we also need to remove the "_ideas" bit at the end, to
    reduce missed hits on fuzzy search. Certain ideasets are also named differently than the display, so that also need
    to be addressed.
    '''
    nonNatIdeasLib = {}
    add_basic_ideas(groupIdeasFile, nonNatIdeasLib)
    add_basic_ideas(genericIdeasFile, nonNatIdeasLib)
    add_basic_ideas(basicIdeasFile, nonNatIdeasLib)
    return nonNatIdeasLib

def add_ideas(file, dictionary):
    '''
    add the ideasets from an idea group file into the general library.
    '''
    with open(file, 'r') as t:
        clauseIdeas = ClauseWizard.cwparse(t.read())
        ideasJson = ClauseWizard.cwformat(clauseIdeas)
        for ideaName, ideaSet in ideasJson.items():
            dictionary[ideaName] = ideaSet
    return dictionary

def add_generic_ideas(file, dictionary):
    '''
    add the ideasets from either group ideaset or generic ideaset into the ideas library.
    '''
    with open(file, 'r') as t:
        clauseIdeas = ClauseWizard.cwparse(t.read())
        ideasJson = ClauseWizard.cwformat(clauseIdeas)
        for ideaName, ideaSet in ideasJson.items():
            ideaTag = re.search('(.*)_ideas', ideaName)
            dictionary[ideaTag.group(1)] = ideaSet
    return dictionary

def add_basic_ideas(file, dictionary):
    with open(file, 'r') as t:
        clauseIdeas = ClauseWizard.cwparse(t.read())
        ideasJson = ClauseWizard.cwformat(clauseIdeas)
        for ideaName, ideaSet in ideasJson.items():
            ideaTag = re.search('(.*)_ideas', ideaName)
            # if the name needs correction, fetch it.
            if ideaTag.group(1) in nameConverterDict:
                dictionary[nameConverterDict[ideaTag.group(1)]] = ideaSet
            else:
                dictionary[ideaTag.group(1)] = ideaSet
    return dictionary

def store_triggers():
    '''
    Function for collecting and storing triggers for all idea sets in the game, and dumping it into
    their respective trigger files:
    data/nat_idea_triggers.json
    data/group_idea_triggers.json

    Note: ideasets with no triggers are represented with {}
    '''
    nat_triggers = collect_triggers(uniqueIdeasFile, {})
    group_triggers = collect_triggers(groupIdeasFile, {})

    # basic idea groups do not have triggers and are not involved in trigger calcs, so they're ignored.
    with open(nationalTriggerPath, 'w') as nat, open(groupTriggerPath, 'w') as group:
        json.dump(nat_triggers, nat)
        json.dump(group_triggers, group)


def collect_triggers(file, dictionary):
    '''
    helper function for collecting the triggers for all idea sets in a given ideaset file and then returning a
    dictionary.
    '''
    with open(file, 'r') as t:
        clauseIdeas = ClauseWizard.cwparse(t.read())
        ideasJson = ClauseWizard.cwformat(clauseIdeas)
        for ideaName, ideaSet in ideasJson.items():
            if "trigger" in ideaSet:
                dictionary[ideaName] = ideaSet["trigger"]
            else:
                dictionary[ideaName] = {}
    return dictionary

def load_triggers(filepath):
    triggerMap = {}
    with open(filepath) as f:
        triggerJson = json.load(f)
        for ideaName, trigger in triggerJson.items():
            triggerMap[ideaName] = Trigger(trigger)
    return triggerMap

# store_cultures()