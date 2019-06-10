#!/usr/bin/python3

import sys
import requests
import spacy
from datetime import datetime

sparql_url = 'https://query.wikidata.org/sparql'
wiki_api_url = 'https://www.wikidata.org/w/api.php'

FIRST_TRY = 0
ENTITY = 0
PROPERTY = 1
EMPTY = 0

global quick_find
global slow_find
global not_found

noun_tags = ["NN", "NNS", "NNP", "NNPS"]
things_of = {"When": "date", "Where": "place", "many": "number", "long": "duration", "old":"age", "How": "cause"}
replacements = {"city":"place", "real":"birth",  "member":"has part", "members":"has part", "because":"cause", "P3283":"P463","P1448":"P1477","P436":"P361"}
roots = {"bear":"birth", "die":"death", "come":"origin", "form":"formation"}
date_props = ['P569', 'P570', 'P571', 'P576', 'P577', 'P1191']
location_words = ["Where", "city", "place", "country", "location"]

questions_nog_niet_goed_9_jun = [
    "Name the record labels of John Mayer.",
    "Which country is Queen from?",  # nog steeds queen als in monarch | United Kingdom
    "Who are the members of Metallica?",#Niet het qualified antwoord!
    "In what year was Die Antwoord formed?",  # geeft 1 January  2008, de publication date van een album What Year Will You Have The World?
    "In what year did Prince die",  # geeft 1 January 2008, de publication date van een album What Year Will You Have The World?
    "What year was the song ’1999’ by Prince published?",  # Did prints 1999-01-01T00:00:00Z | 27 October 1982 | Werkt nog niet
    "What does EDM stand for?",  # definition | werkt nog niet
    "What is a kazoo?",  # definition | American musical instrument | werkt niet
    "Did Louis Armstrong influence the Beatles?",  # PROPN + PROPN dobj | NOT DEFINED
    "Was Eminem born in St. Joseph?", # werkt niet | correct answer: Yes
    "Was ABBA formed in 1989?", # goed antwoord maar niet goede manier
    "Was ABBA formed in 1972?" #verkeerd antwoord
    "Is deadmau5 only a composer?",  # PROPN + NOUN attr  (IT ANSWERS CORRECTLY BUT DUNNO WHY HAHA)
    "Did Michael Jackson play in a band?",  # PROPN + NOUN pobj (DOESNT WORK SINCE BAND IS THE MEMBER OF PROPERTY!!!) Replace? Geeft No | correct answer: Yes
    "Do The Fall make indie rock?", # was gegeven door lecturer als The Fals, maar die bestaat niet? Niet in de eerste 250 entries op wikidata iig
    "Do The Fall make punk rock?" , # ziet The Fall als Fall = herfst\
    "Did Michael Jackson play in the Jackson 5?", # Only works with Five | geeft wel Yes
    "Did Prince die?",  # PROPN + VERB ROOT USe is death    #geeft goede antwoord, maar Prince entity verkeerd...
]

example_queries = [
    # What-questions
    "What was the cause of death of Mozart?", #streptococcal pharyngitis
    "What were the causes of death of Michael Jackson?", #combined drug intoxication, myocardial infarction
    "What is the gender of Conchita Wurst?", #male
    "What is the highest note of a piano?",  # defined, answer = Eighth octave C
    "What is the record label of The Clash", #Sony Music
    "What is the real name of Eminem?", #Marshall Bruce Mathers III
    "What is the website of Mumford and Sons?",  #http://mumfordandsons.com/
    "What is the birth date of Elvis Presley?", #8 January 1935

    # Who-questions
    "Who was the composer of The Four Seasons?", #Antonio Vivaldi
    "Who was the father of Michael Jackson?", #Joe Jackson
    "Who is the stepparent of Neneh Cherry", #Don Cherry

    # Qualified statement questions
    "Who are the members of Metallica?",#Lars Ulrich, Dave Mustaine, Cliff Burton, Robert Trujillo, Jason Newsted, Ron McGovney,Kirk Hammett, James Hetfield, Lloyd Grant | Niet het qualified antwoord!
    "Who is the wife of John Mayer?",  # niet heel qualified, feel free to add | Heeft geen vrouw

    # List questions
    "Name the record labels of John Mayer.", # zoekt naar name; "record label" werkt bij The Clash wel
    "Name the partners of Bruce Springsteen.", #Patti Scialfa, Julianne Phillips | zoekt niet naar name
    "what are the genres of the White Stripes?", #Alternative rock, blues rock, garage rock, post-punk revival, punk blues. 
    "Who were in Queen?", #Freddie Mercury, Brian May, Roger Taylor, John Deacon | werkt, maar parafrase waarschijnlijk niet
    "Who were the members of The Beatles", #John Lennon, Paul McCartney, Ringo Starr, George Harrison
    "Who are the children of Phill Collins?", #Lily Collins, Joely Collins
    "which were the pseudonyms of David Bowie", #Ziggy Stardust, Thin White Duke, David Bowie

    # Rewritten What-questions
    "Where is the birthplace of Bob Marley?", #Nine Mile
    "Where was the origin of Coldplay?", #London
    "When is the deathdate of John Lennon?", #8 December 1980
    "When is the date of death of John Lennon?", #8 December 1980
    "When was Jimi Hendrix born?", #27 November 1942
    "When did Prince die?", #21 April 2016
    "How did Michael Jackson die?",  # combined drug intoxication, myocardial infarction
    "How did Tupac Shakur die?",  # Drive-by shoorting
    "what is the birth name of Lady Gaga?", #Stefani Joanne Angelina Germanotta
    "Which country is Queen from?",  # nog steeds queen als in monarch | United Kingdom
    "What year was the song ’1999’ by Prince published?",  # Did prints 1999-01-01T00:00:00Z | 27 October 1982 | Werkt nog niet 
    "What is the genre of ABBA?", #pop music, glam rock, dance music, pop rock, Europop, Euro disco
    "What does EDM stand for?",  # definition | werkt nog niet 
    "What is a kazoo?",  # definition | American musical instrument | werkt niet
    "How long is Bohemian Rhapsody?", #134 seconds
    "How old is The Dark Side Of The Moon?", #43 years old
    "How long is The Dark Side Of The Moon?", #2579 seconds

    # in what city/country/place/year/band
    "In what city was Die Antwoord formed?", # Cape Town
    "In what city was Eminem born",  # St. Joseph
    "In what year was Die Antwoord formed?",  # geeft 1 January  2008, de publication date van een album What Year Will You Have The World?
    "In what year did Prince die",  # geeft 1 January 2008, de publication date van een album What Year Will You Have The World?

    # count questions
    "How many members does Nirvana have?", #werkt nog niet in quick find, wel in slow find
    "How many children does Adele have?",  # defined | werkt nog niet in quickfind, wel slow find
    "How many strings does a violin usually have?", #DOES NOT WORK AT ALL (ws niet gevraagd)
    # feel free to add

    # age questions (eerste drie werken)
    "How old was Ella Fitzgerald when she died?", #79 years old
    "How old is Eminem?",  # also qualified | 46 years old
    "What is the age of Eminem",  # also qualified | 46 years old

    # yes/no questions
    "Is Michael Jackson dead?", #yes
    "Does Michael Jackson still live?", #no
    "Is Michael Jackson alive?", #no
    "Has Michael Jackson died?", #yes
    "Did Prince die?",  # PROPN + VERB ROOT USe is death    #geeft goede antwoord, maar Prince entity verkeerd...
    "Did Michael Jackson play in the Jackson 5?", # Only works with Five | geeft wel Yes
    "Did Michael Jackson play in the Jackson Five?", #Yes
    "Did Michael Jackson play in a band?",  # PROPN + NOUN pobj (DOESNT WORK SINCE BAND IS THE MEMBER OF PROPERTY!!!) Replace? Geeft No | correct answer: Yes
    "Do The Fall make indie rock?", # was gegeven door lecturer als The Fals, maar die bestaat niet? Niet in de eerste 250 entries op wikidata iig
    "Do The Fall make punk rock?" , # ziet The Fall als Fall = herfst
    "Does Green Day make alternative rock?",  # NOUN nsubj + NN amod # Yes
    "Is Michael Jackson male?",  # PROPN + NN attr # Yes
    "Is Miley Cyrus the daughter of Billy Ray Cyrus?",  # PROPN + compound PROPN (only last word cyrus is pobj) | Yes
    "Is Miley Cyrus the father of Billy Ray Cyrus?", # No
    "Does deadmau5 make house music?",  # NOUN + NOUN compound (" ".join((ent_name2.lemma_, ent_name2.head.lemma_))) | Yes
    "Does Felix Jaehn come from Hamburg?",  # PROPN + PROPN npadvmod | Yes
    "Does Felix Jaehn come from Berlin?",  # PROPN + PROPN npadvmod | No
    "Is deadmau5 only a composer?",  # PROPN + NOUN attr  (IT ANSWERS CORRECTLY BUT DUNNO WHY HAHA)
    "Is deadmau5 a composer?",  # Yes | werkt
    "Did Louis Armstrong influence the Beatles?",  # PROPN + PROPN dobj | NOT DEFINED
    "Was Eminem born in St. Joseph?", # werkt niet | correct answer: Yes
    "Was ABBA formed in 1989?", # goed antwoord maar niet goede manier
    "Was ABBA formed in 1972?" #verkeerd antwoord
]

# questions to test extra things on
'''"Who was the first husband of Yoko Ono?",
"Who was Mozarts oldest child?",
"To which musical genre(s) can The White Stripes be assigned?"'''

error_msg = "No data found. Try paraphrasing the question."
user_msg = "Please enter a question or quit program by pressing control-D."

'''This function prints the examples above and runs the search for answers on them one line at a time '''
def print_example_queries():
    for index, example in enumerate(example_queries):
        print("(" + str(index + 1) + ") " + example)
        # create_and_fire_query(example)
    # Op dit moment vindt quick find 35 and slow find 8 antwoorden, 4 antwoorden niet gevonden
    # Niet al deze antwoorden zijn correct!
    print("Quick finds = " + str(quick_find) + " Slow finds = " + str(slow_find) + " Not founds = " + str(not_found))

def is_dead(entity, is_yes_no):
    death = False
    query = '''
            SELECT ?property WHERE { 
                wd:%s wdt:%s ?prop.
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en".
                    ?prop rdfs:label ?property
                }
            }''' % (entity, "P570")  # P570 = date of death
    death_date = requests.get(sparql_url,
                       params={'query': query, 'format': 'json'}).json()

    if not death_date['results']['bindings']:
        print("not dead")
        return False, 0, 0, 0

    print(entity)
    for item in death_date['results']['bindings']:
        for var in item:
            date_end = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')

            year_of_death = int(str(date_end.strftime("%Y")), 10)
            month_of_death = int(str(date_end.strftime("%m")), 10)
            date_of_death = int(str(date_end.strftime("%d")), 10)
            death = True
    if is_yes_no:
        print(death)
        return death, 0, 0, 0
    else:  # DOES THIS NOT FAIL WHEN NO DEATH IS FOUND?
        if death:
            return death, year_of_death, month_of_death, date_of_death


def find_age(entity, date_begin):
    death, year_of_death, month_of_death, date_of_death = is_dead(entity, False)

    year_of_birth = int(str(date_begin.strftime("%Y")), 10)
    month_of_birth = int(str(date_begin.strftime("%m")), 10)
    date_of_birth = int(str(date_begin.strftime("%d")), 10)

    print("\t\t\t\t\t\t\t\t\t   ANSWER: ", end='')
    if not death:
        dot = datetime.today()
        year_today = int(str(dot.strftime("%Y")), 10)
        month_today = int(str(dot.strftime("%m")), 10)
        date_today = int(str(dot.strftime("%d")), 10)
        year = year_today - year_of_birth
        if month_today < month_of_birth:
            year = year - 1
        if month_today == month_of_birth:
            if date_today < date_of_birth:
                year = year + 1

    else:
        print("This person died at ", end='')
        # Is this not going to give errors when there's no death date recorded?
        year = year_of_death - year_of_birth
        if month_of_death < month_of_birth:
            year = year - 1
        if month_of_death == month_of_birth:
            if date_of_death < date_of_birth:
                year = year + 1
    print(str(year) + " years old")


'''This function prints the answers based on their found property and entity tags'''
def print_answer(property, entity, is_count, is_age):
    date = False
    # Is the property a birth date, death, disappeared, inception, abolished, publication, first performance  ?
    if property in date_props:
        date = True
    # If it's a count, try count query
    if is_count:
        query = '''
        SELECT distinct (count(?albums) AS ?number) WHERE {
            wd:%s wdt:%s ?albums .
        } ''' % (entity, property)

        # IMPLEMENT SOMETHING THAT ALSO TRIES THE COUNT WITH A STANDARD QUERY (for string of guitar case)
    else:  # standard query
        query = '''
        SELECT ?property WHERE { 
            wd:%s wdt:%s ?prop.
            SERVICE wikibase:label {
                bd:serviceParam wikibase:language "en".
                ?prop rdfs:label ?property
            }
        }''' % (entity, replace(property))

    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()

    # If no answer is found return empty
    if len(data['results']['bindings']) == EMPTY:
        return EMPTY
    for item in data['results']['bindings']:
        for var in item:
            if property == 'P2047':  # = Duration
                print("\t\t\t\t\t\t\t\t\t   ANSWER: " + item[var]['value'] + " seconds")
            else:
                if date:
                    date = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
                    if is_age:
                        find_age(entity, date)
                    else:
                        print(" \t\t\t\t\t\t\t\t\t  ANSWER: " + str(date.day), str(date.strftime("%B")), str(date.year))
                if not date:
                    # Only print counts higher than 0 (else it didn't find one and the list is empty)
                    if is_count and item[var]['value'] == '0':
                        return False
                    print(" \t\t\t\t\t\t\t\t\t  ANSWER: " + item[var]['value'])
    return True


'''This function replaces a word if it should be (real/city/member) -> (birth/place/has part)'''
def replace(word):
    if word in replacements:
        return replacements[word]
    else:
        return word


''' This function tries different entity and property disambiguations. It then also tries to find 
    an answer with each of these disambiguated combinations'''
def try_disambiguation(property_name, entity_name, is_count, found_result, is_age, is_location):
    index_entities = 0
    entity_tag = find_tag(entity_name, ENTITY, index_entities, is_age, '', is_location)
    while not found_result and index_entities < 2:  # look through 2 different entities
        index_properties = 0
        while not found_result and index_properties < 7:  # look though 7 different properties
            property_tag = find_tag(property_name, PROPERTY, index_properties, is_age, entity_tag, is_location)
            print("Tag disambiguation: " + property_tag)
            # If no more results can be found by ambiguation stop the loop
            if property_tag == "empty":
                break
            found_result = print_answer(property_tag, entity_tag, is_count, False)
            index_properties += 1
        index_entities += 1
        entity_tag = find_tag(entity_name, ENTITY, index_entities, is_age, '', is_location)
        if entity_tag == "empty":
            break
    return found_result


'''Find the type of entity: a human or something else'''
def instance_of(ent_tag, is_age):
    query = '''
            SELECT ?instance WHERE {
                wd:%s wdt:P31 ?class.
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en".
                    ?class rdfs:label ?instance
                }
            }''' % ent_tag

    instdata = requests.get(sparql_url, params={'query': query, 'format': 'json'}).json()
    name = 'date of publication'
    for item in instdata['results']['bindings']:
        for var in item:
            if item[var]['value'] == "human":
                if (is_age):
                    name = 'date of birth'
                else: # i.e. location
                    name = 'place of birth'
            elif item[var]['value'] == "band":
                if (is_age):
                    name = 'inception'
                else:  # i.e. location
                    name = 'place of formation'
    return name


''' Find a property or entity tag from the WikiData API given the current property/entity name
    The index indicates which tag in the API's list of tags needs to be returned'''
def find_tag(name, ent_or_prop, index, is_age, ent_tag, is_location):
    # print("hi! name = ",name)
    if ent_or_prop == ENTITY:  # Currently looking for the most referenced entity
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    if ent_or_prop == PROPERTY:  # Currently looking for the most referenced property
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
        if is_age or is_location:
            name = instance_of(ent_tag, is_age)
    params['search'] = name
    json = requests.get(wiki_api_url, params).json()
    for iteration, result in enumerate(json['search'], start=0):
        if index == FIRST_TRY:  # return only the first result, since that is the most referenced one
            return result['id']
        if iteration == index:  # if the first result didn't give an answer when the query fired
            return result['id']
    return "empty"  # at the end of the API list, return empty so no redundant empty statements are evaluated


def answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2, entity_name2):
    print("Y/N Entity2: " + entity_name2 + " " + entity_tag)
    answer_ent = find_property_answer(parse, entity_tag2, entity_name, entity_name2)
    print("Answer using property: " + str(answer_ent))
    dead_or_alive = death_in_yes_no(parse)
    if dead_or_alive:
        if dead_or_alive == 'died':
            if is_dead(entity_tag, is_yes_no):
                print(" \t\t\t\t\t\t\t\t\t   ANSWER: Yes")
            else:
                print(" \t\t\t\t\t\t\t\t\t   ANSWER: No")
            found_result = True
        if dead_or_alive == 'lives':
            if is_dead(entity_tag, is_yes_no):
                print(" \t\t\t\t\t\t\t\t\t   ANSWER: No")
            else:
                print(" \t\t\t\t\t\t\t\t\t   ANSWER: Yes")
            found_result = True
    if not found_result:
        if answer_ent == "Entity_corresponds":
            print(" \t\t\t\t\t\t\t\t\t   ANSWER: Yes")
            found_result = True
        if answer_ent == "Entity_different":
            print(" \t\t\t\t\t\t\t\t\t   ANSWER: No")
            found_result = True
        if answer_ent == "No_property_in_sentence":
            found_result = yes_no_query(entity_tag, entity_tag2, entity_name2)
    return found_result


def death_in_yes_no(parse):
    dead_or_alive = ''
    for death_prop in parse:
        if death_prop.dep_ == 'ROOT' or death_prop.dep_ == 'acomp':
            if death_prop.lemma_ == 'alive' or death_prop.lemma_ == 'live':
                dead_or_alive = 'lives'
            if death_prop.lemma_ == 'dead' or death_prop.lemma_ == 'die':
                dead_or_alive = 'died'
    return dead_or_alive


def yes_no_query(entity, entity2, entity_name2):
    query = '''
            ASK WHERE {wd:%s ?prop wd:%s}
            ''' % (entity, entity2)
    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()
    if data['boolean']:
        print(" \t\t\t\t\t\t\t\t\t   ANSWER: Yes")
    else:
        # Try the second best entity
        entity2 = find_tag(entity_name2, ENTITY, 1, False, '', False)
        query = '''
                ASK WHERE {wd:%s ?prop wd:%s}
                ''' % (entity, entity2)
        data = requests.get(sparql_url,
                            params={'query': query, 'format': 'json'}).json()
        if data['boolean']:
            print(" \t\t\t\t\t\t\t\t\t   ANSWER: Yes")
        else:
            print(" \t\t\t\t\t\t\t\t\t   ANSWER: No")
    return True


'''This function first looks for entities and properties given the line'''
def create_and_fire_query(line):
    nlp = spacy.load('en')
    parse = nlp(line.strip())
    entity_name = entity_tag = 'None'
    found_result = is_count = is_age = is_location = is_yes_no = False

    '''YES/NO QUESTIONS'''
    # If the first word is a form of to be or to do it is a Yes/No question
    if parse:  # if parse is not null
        # The capital letters are added for the simple forms since these don't get converted to lowercase somehow
        if parse[0].lemma_ == 'do' or parse[0].lemma_ == 'Do' or parse[0].lemma_ == 'be' or parse[0].lemma_ == 'have' or parse[0].lemma_ == 'Have':
            print("This is a YES/NO question")
            is_yes_no = True
            entity_tag2 = 'None'

    for token in parse:
        if token.text == "age" or token.text == "old":  # if the question contains age or old, the user request an age
            print("AGE QUESTION")
            is_age = True
        if token.text in location_words:  # sentences starting with "where" are about locations
            is_location = True

    '''Look for entity'''
    i = 0
    for ent_name in parse.ents:  # Try to find the entity with the entity method first
        if i == 0:
            # print("ent_name text ", ent_name.text, "dep: ", ent_name.dep_)
            if ent_name.label_ != 'LOC':
                entity_name = ent_name.lemma_.replace("'s", "").replace("'", "")
                entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY, is_age, '', is_location)
                print('Found slow entity in parse.ents. Entity_tag: -' + str(entity_name) + '- entity: -' + str(
                    entity_tag) + "-")
                #print("ent_name text ", entity_name.text, "dep: ", ent_name.dep_)
                i += 1

        # Try finding a second standard entity here
        else:
            entity_name2 = ent_name.lemma_.replace("'s", "").replace("'", "")
            entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
            print('Found slow entity2 in parse.ents. Entity_tag: -' + str(entity_name2) + '- entity: -' + str(entity_tag2) + "-")
            if is_yes_no:
                found_result = answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2, entity_name2)

    if entity_name == 'None':  # If no entity was found use the proper noun or object method to find entity
        for ent_name in parse:
            # Seems dangerous to look for pobj here because you're most often looking for the subject of the sentence?
            if ent_name.pos_ == 'PROPN' or ent_name.dep_ == 'pobj' or ent_name.dep_ == 'nsubj':
                # IF compound !!!
                entity_name = ent_name.lemma_.replace("'s", "").replace("'", "")
                entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY, is_age, '', is_location)
                print('Found slow entity as proper noun or pobj. Query_ent: -' + str(entity_name) + '- entity: -' + str(entity_tag) + "-")

    if is_yes_no and not found_result:
        # The loop always continues until the last word in the sentence, which is nice, since English (yes/no) is structured according to Subject Verb Object, and we need object
        for word in parse:
            if word.dep_ == 'compound' or word.dep_ == 'amod':
                entity_name2 = " ".join((word.lemma_, word.head.lemma_))
                if entity_name == entity_name2:  # When the entity found is the same as entity 1, go to next word
                    continue
                entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
                print('Found slow entity3 in parse. Entity_name2: -' + str(entity_name2) + '- entity_tag2: -' + str(entity_tag2) + "-")
                if entity_tag2 == 'empty':
                    continue
                else:
                    break

            if word.dep_ == 'attr' or word.dep_ == 'npadvmod' or word.dep_ == 'dobj' \
                    or word.dep_ == 'pobj' or word.dep_ == 'ROOT' or word.dep_ == 'nsubj':
                entity_name2 = word.lemma_
                if entity_name == entity_name2 or entity_name2 == 'be':  # If it found the same name find another one or it's a ROOT 'be'
                    continue
                entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
                print('Found slow entity4 in parse. Entity_tag: -' + str(entity_name2) + '- entity: -' + str(
                    entity_tag2) + "-")
                # if subject of the sentence if found, switch subject and object around and the found string is not a substring of the first entity (because substrings are different, but sometimes classified as nsubj
                if word.dep_ == 'nsubj' and entity_name2 not in entity_name2:
                    print("swapper")  # This is shorter, but needs to be tested to be sure
                    entity_tag, entity_tag2 = entity_tag2, entity_tag
                    entity_name, entity_name2 = entity_name2, entity_name
                    # switcher = entity_tag
                    # entity_tag = entity_tag2
                    # entity_tag2 = switcher
                    # switcher = entity_name
                    # entity_name = entity_name2
                    # entity_name2 = switcher
                if entity_tag2 == 'empty':
                    continue
                # else:  # probably better to not break here since this finds things like 'make' as well as normal entities
                #     break

        if entity_tag2 != 'None':  # if entity 2 is not empty find a yes/no answer
            found_result = answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2, entity_name2)

    if not found_result:
        '''QUICK FIND'''
        ent_name = ""
        prop_name = ""

        for token in parse:
            if token.pos_ == "ADJ":
                if "st" in token.text:
                    print("ADJective property: -" + prop_name + token.text + "-")
                    prop_name = prop_name + token.text + " "

            elif token.dep_ == "advmod":
                if token.text in things_of:
                    if token.head.lemma_ in things_of:
                        prop_name = prop_name + things_of[token.head.lemma_]
                        print("Property: -" + prop_name + "- Token head lemma of Adverbial modifier (advmod)")
                    else:
                        prop_name = prop_name + things_of[token.text]
                        print("Property: -" + prop_name + "- Token text of Adverbial modifier (advmod)")

            elif token.dep_ == "ROOT" or token.dep_ == "advcl":
                if (token.lemma_ in roots):
                    prop_name = prop_name + " of " + roots[token.lemma_]
                    print(
                        "Property: -" + prop_name + "- ROOT or adverbial clause modifier (advcl). It's birth, death, origin or formation")
                else:
                    print("token lemma " + token.lemma_ + " not in roots")

            elif token.tag_ in noun_tags:
                # If P is in the token tag, then its token text is an entity
                if not "P" in token.tag_:
                    if prop_name in things_of.values() and not token.lemma_ in things_of.values() and prop_name != "duration" and prop_name != "age":
                        prop_name = prop_name + " of " + replace(token.lemma_)
                        print("Property: -" + prop_name + "- P is not in token tag. In things_of found")
                    elif (token.dep_ != "pobj" or "of" in prop_name) and not replace(token.lemma_) in prop_name and prop_name != "duration" and prop_name != "age":
                        prop_name = prop_name + replace(token.lemma_)
                        print("Property: -" + prop_name + "- Compound property (e.g. highest note)")
                    else:
                        ent_name = ent_name + token.text + " "
                        print("Entity: -" + ent_name + "- P is not in token tag and prop is not in things_of.")
                        if not prop_name and token.head.lemma_ == "in":
                            print("who are in?")
                            prop_name = "has part"

                else:
                    # Adds every entity in the phrase together
                    ent_name = ent_name + token.text + " "
                    print("Entity: -" + ent_name + "- P is in token tag")
                    if not prop_name and token.head.lemma_ == "in":
                        print("who are in?")
                        prop_name = "has part"

        print(prop_name, "ent =", ent_name)
        if entity_name:
            ent_name = entity_name
        else:
            # In de meeste gevallen is dit niet nodig, omdat entity method goed gaat.
            # Bij bijvoorbeeld the Foo Fighters echter geeft de entity method de verkeerde maar wel met een antwoord.
            print("WHY ALWAYS USE THE ENTITY FOUND FIRST? DOES PROGRAM EVER NOT FIND entity_name?")
        print("now " + prop_name, "ent =", ent_name)

        if prop_name != "":
            if not ent_name:
                ent_name = entity_name
            # print("now " + prop_name, "ent =", ent_name)
            ent_tag = find_tag(ent_name, ENTITY, FIRST_TRY, is_age, '', is_location)
            prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY, is_age, ent_tag, is_location)
            found_result = print_answer(prop_tag, ent_tag, is_count, is_age)
            print(
                "   QUICK FIND FOUND entity: -" + ent_tag + " " + ent_name + "- and property: -" + prop_tag + " " + prop_name + "-")
            # If it didn't find anything, then try disambiguating result
            if not found_result:
                print("DISAMBIGUATION phase quick find")
                found_result = try_disambiguation(prop_name, ent_name, is_count, found_result, is_age, is_location)
            if found_result:
                global quick_find
                quick_find += 1
    print("Quick find count = " + str(quick_find))

    '''SLOW FIND'''
    if not found_result:
        print("---> GOING TO SLOW FIND")
        '''Look for property'''
        property_name = ""
        for prop_name in parse:
            # Uses the word 'many' to indicate counting (maybe also use 'number of' or 'amount of'?)
            if prop_name.pos_ == 'ADJ' and prop_name.lemma_ == 'many':
                print("Seeing this as a COUNT question")
                is_count = True

            # If the property consists of multiple words join them together
            if not found_result:
                if (prop_name.dep_ == 'compound' and prop_name.tag_ == 'NN') or \
                        (prop_name.pos_ == 'ADJ' and prop_name.dep_ == 'amod'):
                    # Dit verandert naar prop.text ipv prop,lemma_ omdat je het volledige bijv naamwoord wilt (e.g. highest note)
                    property_name = " ".join((replace(prop_name.text), replace(prop_name.head.lemma_)))
                    print("Trying property: -" + property_name + "-, as compound or as adjectival modifier (amod)")
                # This fires (mostly) for NOUNS (some entities as well if the not condition is omitted)
                if prop_name.dep_ != 'compound' and (
                        prop_name.dep_ == 'nsubj' or prop_name.dep_ == 'attr' or prop_name.tag_ == 'NN') and \
                        not found_result and entity_name != prop_name.lemma_:
                    property_name = replace(prop_name.lemma_)
                    print("Trying property: -" + property_name + "-, as nominal subject (nsubj), attribute (attr) or common noun (NN)")

                if prop_name.dep_ == 'acl' or prop_name.dep_ == 'dobj' and not found_result:  # The dobj is mainly for count questions
                    property_name = replace(prop_name.text)
                    print("Trying property: -" + property_name + "-, as a clausal modifier of noun (acl) or direct object (dobj)")

                if prop_name.dep_ == 'ROOT' and not found_result:
                    property_name = replace(prop_name.head.lemma_)
                    # If the root is 'to be' don't look up property (irrelevant to do, and gives erroneous results)
                    if not property_name == 'be':
                        print("Trying property: -" + property_name + "-, as root (a word that means something)")

                if property_name and not property_name == 'be':
                    property_tag, found_result = find_answer(property_name, entity_name, entity_tag, is_count, is_age, is_location)
                    if not found_result:  # If you don't find a result don't try again with the same name
                        property_name = ""
                    print("Tag: " + property_tag)

        '''Print how the program did'''
        if not found_result and line:  # and line means the line is not empty
            print(error_msg)
            global not_found
            not_found += 1
        else:
            global slow_find
            slow_find += 1
            if not is_yes_no:
                print(
                        "SLOW FIND FOUND entity: -" + entity_name + " " + entity_tag + "- and property: -" + property_tag + " " + property_name + "-")
            print("Slow find count = " + str(slow_find))


'''This function finds a property tag, tries to print the answer of the query and tries disambiguation if it didn't 
   find and answer. Then it return the tag and whether it found a result'''
def find_answer(property_name, entity_name, entity_tag, is_count, is_age, is_location):
    property_tag = find_tag(property_name, PROPERTY, FIRST_TRY, is_age, entity_tag, is_location)
    found_result = print_answer(property_tag, entity_tag, is_count, is_age)
    if not found_result:
        found_result = try_disambiguation(property_name, entity_name, is_count, found_result, is_age, is_location)
    return property_tag, found_result


'''This function is for yes/no questions. It evaluates if there's a property in the sentence. Then it queries
   the database with the compare answer function and returns if it found the same (entity) answer as was
   found in the sentence'''
def find_property_answer(parse, entity_tag, entity_name, entity_name2):
    prop_name = ''
    prop_tag = ''

    for token in parse:
        if token.dep_ == 'appos' or token.dep_ == 'attr':
            if token.lemma_ != entity_name2:  # For example 'male' would be found as entity2 and property
                prop_name = token.lemma_
                print(entity_name2)
                print("Y/N Found property name: " + prop_name)
    if prop_name:
        prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY, False, entity_tag, False)
        print("Y/N Found property tag: " + prop_tag)
    if prop_tag == EMPTY or not prop_tag or entity_name == 'None':  # Else property tag is empty, so we assume no property has been found
        return "No_property_in_sentence"  # return that the answer of the yes/no entity query should be respected
    else:
        same_result = compare_answer(prop_tag, entity_tag, entity_name)
        # If the entity name answer using a property is the same as the second entity in the question
        if same_result:
            return "Entity_corresponds"
        else:
            return "Entity_different"  # The entity and the answer don't correspond (e.g. asking if Billy is the Wife of Miley Cyrus)

'''This function is for yes/no questions. It queries the database to see if it finds the second entity in 
   the sentence, after which it compares the queried and sentence entity. 
   Finally, it returns the answer to find_property_answer'''
def compare_answer(prop_tag, entity_tag, entity_name2):
        print("prop tag: " + prop_tag + " ent tag: " + entity_tag + " ent name 2: " + entity_name2)
        query = '''
         SELECT ?property WHERE {
             wd:%s wdt:%s ?prop.
             SERVICE wikibase:label {
                 bd:serviceParam wikibase:language "en".
                 ?prop rdfs:label ?property
             }
         }''' % (entity_tag, prop_tag)
        print("Using ent_tag: " + entity_tag + " and prop_tag: " + prop_tag + " for comparison query")
        data = requests.get(sparql_url,
                            params={'query': query, 'format': 'json'}).json()

        # If no answer is found return empty
        if len(data['results']['bindings']) == EMPTY:
            print("empty")
            return EMPTY
        for item in data['results']['bindings']:
            for var in item:
                print("found answer: " + item[var]['value'] + ". In text answer was: " + entity_name2)
                if str(item[var]['value']) == entity_name2:
                    return True
                else:
                    return False


def main(argv):
    global quick_find
    global slow_find
    global not_found
    quick_find = slow_find = not_found = 0
    print_example_queries()
    print(user_msg)
    for line in sys.stdin:
        # line = example_queries[int(line)-1].rstrip()
        line = line.rstrip()
        create_and_fire_query(line)
        print(user_msg)


# Is this file ran directly from python or is it being imported?
if __name__ == "__main__":
    main(sys.argv)
