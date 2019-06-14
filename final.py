# !/usr/bin/python3

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

error_msg = "No data found. Try paraphrasing the question."
user_msg = "Please enter a question or quit program by pressing control-D."

noun_tags = ["NN", "NNS", "NNP", "NNPS"]
things_of = {"When": "date", "Where": "place", "many": "number", "long": "duration", "old": "age", "How": "cause"}
replacements = {"city": "place", "real": "birth", "member": "has part", "members": "has part", "because": "cause",
                "P3283": "P463", "P1448": "P1477", "P436": "P361"}
roots = {"bear": "birth", "die": "death", "come": "origin", "form": "formation"}
date_props = ['P569', 'P570', 'P571', 'P576', 'P577', 'P1191']
location_words = ["Where", "city", "place", "location"]
yes_no_words = ["do", "Do", "be", "Be", "have", "Have"]
example_queries = [
    # What-questions
    "What was the cause of death of Mozart?",  # streptococcal pharyngitis
    "What were the causes of death of Michael Jackson?",  # combined drug intoxication, myocardial infarction
    "What is the gender of Conchita Wurst?",  # male
    "What is the highest note of a piano?",  # defined, answer = Eighth octave C
    "What is the record label of The Clash",  # Sony Music
    "What is the real name of Eminem?",  # Marshall Bruce Mathers III
    "What is the website of Mumford and Sons?",  # http://mumfordandsons.com/
    "What is the birth date of Elvis Presley?",  # 8 January 1935
    "What are the record labels of Green Day?",  # ANSWER: Reprise Records, Epitaph Records. works now
    "Which country is Queen from?",
    # Who-questions
    "Who was the composer of The Four Seasons?",  # Antonio Vivaldi
    "Who was the father of Michael Jackson?",  # Joe Jackson
    "Who is the stepparent of Neneh Cherry",  # Don Cherry
    "Who are the members of Metallica?",  # Lars Ulrich, Dave Mustaine, Cliff Burton, Robert Trujillo, Jason Newsted,
    "Who are the members of Metallica?",  # Ron McGovney,Kirk Hammett, James Hetfield, Lloyd Grant
    "Who is the wife of John Mayer?",  # Heeft geen vrouw
    # List questions
    "Name the record labels of John Mayer.",  # zoekt naar name; "record label" werkt bij The Clash wel
    "Name the partners of Bruce Springsteen.",  # Patti Scialfa, Julianne Phillips | zoekt niet naar name
    "what are the genres of the White Stripes?",
    # Alternative rock, blues rock, garage rock, post-punk revival, punk blues.
    "Who were in Queen?",  # Freddie Mercury, Brian May, Roger Taylor, John Deacon
    "Who were the members of The Beatles",  # John Lennon, Paul McCartney, Ringo Starr, George Harrison
    "Who are the children of Phill Collins?",  # Lily Collins, Joely Collins
    "which were the pseudonyms of David Bowie",  # Ziggy Stardust, Thin White Duke, David Bowie
    # Rewritten What-questions
    "Where is the birthplace of Bob Marley?",  # Nine Mile
    "Where was the origin of Coldplay?",  # London
    "When is the deathdate of John Lennon?",  # 8 December 1980
    "When is the date of death of John Lennon?",  # 8 December 1980
    "When was Jimi Hendrix born?",  # 27 November 1942
    "When did Prince die?",  # 21 April 2016
    "How did Michael Jackson die?",  # combined drug intoxication, myocardial infarction
    "How did Tupac Shakur die?",  # Drive-by shoorting
    "what is the birth name of Lady Gaga?",  # Stefani Joanne Angelina Germanotta
    "Which country is Queen from?",  # nog steeds queen als in monarch | United Kingdom
    "What year was the song ’1999’ by Prince published?",
    "What is the genre of ABBA?",  # pop music, glam rock, dance music, pop rock, Europop, Euro disco
    "What does EDM stand for?",  # definition | werkt nog niet
    "What is a kazoo?",  # definition | American musical instrument | werkt niet
    "How long is Bohemian Rhapsody?",  # 134 seconds
    "How old is The Dark Side Of The Moon?",  # 43 years old
    "How long is The Dark Side Of The Moon?",  # 2579 seconds
    # In what city/country/place/year/band
    "In what city was Die Antwoord formed?",  # Cape Town
    "In what city was Eminem born",  # St. Joseph
    "In what year was Die Antwoord formed?",
    "In what year did Prince die",
    "In what year was ABBA formed?",
    "In what year did Prince die",
    # Count questions
    "How many members does Nirvana have?",  # werkt nog niet in quick find, wel in slow find
    "How many children does Adele have?",  # defined | werkt nog niet in quickfind, wel slow find
    "How many strings does a violin usually have?",  # DOES NOT WORK AT ALL (ws niet gevraagd)
    # Age questions (eerste drie werken)
    "How old was Ella Fitzgerald when she died?",  # 79 years old
    "How old is Eminem?",  # also qualified | 46 years old
    "What is the age of Eminem",  # also qualified | 46 years old
    # Yes/no questions
    "Is Michael Jackson dead?",  # yes
    "Does Michael Jackson still live?",  # no
    "Is Michael Jackson alive?",  # no
    "Has Michael Jackson died?",  # yes
    "Did Michael Jackson pass away?",
    "Did Prince die?",  # PROPN + VERB ROOT USe is death    #geeft goede antwoord, maar Prince entity verkeerd...
    "Did Michael Jackson play in the Jackson Five?",  # Yes
    "Did Michael Jackson play in the Jackson 5?",
    "Is Green Day's record label Epitaph Records?",
    "Did Prince die?",
    "Is Michael Jackson male?",  # PROPN + NN attr # Yes
    "Is Miley Cyrus the daughter of Billy Ray Cyrus?",  # PROPN + compound PROPN (only last word cyrus is pobj) | Yes
    "Is Miley Cyrus the father of Billy Ray Cyrus?",  # No
    "Is Miley Cyrus' father Billy Ray Cyrus?",
    "Is Michael Jackson's nickname Bambi?",
    "Does deadmau5 make house music?",
    "Does Michael Jackson have a nickname?",  # only entity and propery. We need to check if ent + prop has an answer
    "Does Felix Jaehn come from Hamburg?",  # PROPN + PROPN npadvmod | Yes
    "Does Felix Jaehn come from Berlin?",  # PROPN + PROPN npadvmod | No
    "Is deadmau5 only a composer?",  # PROPN + NOUN attr  (IT ANSWERS CORRECTLY BUT DUNNO WHY HAHA)
    "Is deadmau5 a composer?",  # Yes | werkt
    "Did Louis Armstrong influence the Beatles?",  # PROPN + PROPN dobj | NOT DEFINED
    "Was Eminem born in St. Joseph?",  # werkt niet | correct answer: Yes
    "Was ABBA formed in 1972?",  # verkeerd antwoord
    # Definition questions
    "What does EDM stand for?",  # definition | werkt nog niet
    "What is a kazoo?",  # definition | American musical instrument | werkt niet
    "Did Louis Armstrong influence the Beatles?",  # PROPN + PROPN dobj | NOT DEFINED
    "Was Eminem born in St. Joseph?",  # werkt niet | correct answer: Yes
    "Does Greenday make alternative rock?",
    # Statements instead of questions
    "Name the record labels of John Mayer."
]

'''This function prints the examples above and runs the search for answers on them one line at a time '''
def print_example_queries():
    for index, example in enumerate(example_queries):
        print("(" + str(index + 1) + ") " + example)
        create_and_fire_query(example)


'''Prints the explanation for abbreviations. It actually just prints the label of the entity.'''
def stands_for(entity):
    query = '''
            SELECT ?label WHERE {
                wd:%s rdfs:label ?label.
                FILTER(lang(?label) = "en" )
            } ''' % entity

    description = requests.get(sparql_url,
                               params={'query': query, 'format': 'json'}).json()
    if len(description['results']['bindings']) == EMPTY:
        return EMPTY
    for item in description['results']['bindings']:
        for var in item:
            print(item[var]['value'])
            return True
    return False


'''Gives as answer the description of the first entity.'''
def give_description(entity):
    query = '''
            SELECT ?description WHERE {
                wd:%s schema:description ?description.
                FILTER(lang(?description) = "en" )
            } ''' % entity

    description = requests.get(sparql_url,
                               params={'query': query, 'format': 'json'}).json()
    if len(description['results']['bindings']) == EMPTY:
        return EMPTY
    for item in description['results']['bindings']:
        for var in item:
            print( item[var]['value'])


'''Function that returns whether someone is still alive. 
   If the person is dead, the function returns the date that someone died.'''
def is_dead(entity_name, entity_tag, is_yes_no):
    death = False
    is_ent_human = instance_of(entity_tag, False)
    if is_ent_human != 'place of birth':  # 'place of birth' is what the function returns for 'humans'
        if entity_name:
            entity_tag = find_tag(entity_name, ENTITY, 1, False, '',
                                  False)  # Find the second entity (which is likely human)
    query = '''
            SELECT ?property WHERE { 
                wd:%s wdt:%s ?prop.
                SERVICE wikibase:label {
                    bd:serviceParam wikibase:language "en".
                    ?prop rdfs:label ?property
                }
            }''' % (entity_tag, "P570")  # P570 = date of death
    death_date = requests.get(sparql_url,
                              params={'query': query, 'format': 'json'}).json()

    if not death_date['results']['bindings']:
        return False, 0, 0, 0
    for item in death_date['results']['bindings']:
        for var in item:
            date_end = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')

            year_of_death = int(str(date_end.strftime("%Y")), 10)
            month_of_death = int(str(date_end.strftime("%m")), 10)
            date_of_death = int(str(date_end.strftime("%d")), 10)
            death = True
    if is_yes_no:
        return death, 0, 0, 0
    else:
        if death:
            return death, year_of_death, month_of_death, date_of_death


'''Function that prints the age of a person. 
   When that person appeared to be dead, the age of that person when he died is printed.'''
def find_age(entity, date_begin):
    death, year_of_death, month_of_death, date_of_death = is_dead('', entity, False)

    year_of_birth = int(str(date_begin.strftime("%Y")), 10)
    month_of_birth = int(str(date_begin.strftime("%m")), 10)
    date_of_birth = int(str(date_begin.strftime("%d")), 10)

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
    answerCount = len(data['results']['bindings'])
    for item in data['results']['bindings']:
        for var in item:
            if property == 'P2047':  # = Duration
                print(item[var]['value'] + " seconds")
            else:
                if date:
                    date = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
                    if is_age:
                        find_age(entity, date)
                    else:
                        print(str(date.day), str(date.strftime("%B")), str(date.year))
                if not date:
                    # Only print counts higher than 0 (else it didn't find one and the list is empty)
                    if is_count and item[var]['value'] == '0':
                        return False
                    print(item[var]['value'], end = "")
                    answerCount = answerCount - 1
                    if answerCount > 0:
                        print(", ", end = "")
                    else:
                        print(" ")
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
    # Query with entity and instance of (P31)
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
                if is_age:
                    name = 'date of birth'
                else:  # i.e. location
                    name = 'place of birth'
            elif item[var]['value'] == "band":
                if is_age:
                    name = 'inception'
                else:  # i.e. location
                    name = 'place of formation'
    return name


''' Find a property or entity tag from the WikiData API given the current property/entity name
    The index indicates which tag in the API's list of tags needs to be returned'''
def find_tag(name, ent_or_prop, index, is_age, ent_tag, is_location):
    if ent_or_prop == ENTITY:  # Currently looking for the most referenced entity
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    if ent_or_prop == PROPERTY:  # Currently looking for the most referenced property
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
        if is_age or is_location and "death" not in name:
            name = instance_of(ent_tag, is_age)
    params['search'] = name
    json = requests.get(wiki_api_url, params).json()
    for iteration, result in enumerate(json['search'], start=0):
        if index == FIRST_TRY:  # return only the first result, since that is the most referenced one
            return result['id']
        if iteration == index:  # if the first result didn't give an answer when the query fired
            return result['id']
    return "empty"  # at the end of the API list, return empty so no redundant empty statements are evaluated


'''Finds the answer for a yes/no question once it is defined as such.
   Also makes sure that the answer is printed in the right format(yes/no instead of true/false).'''
def answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2, entity_name2):
    answer_ent = find_property_answer(parse, entity_tag, entity_name, entity_tag2, entity_name2)
    dead_or_alive = death_in_yes_no(parse)
    if dead_or_alive:
        if dead_or_alive == 'died':
            if is_dead(entity_name, entity_tag, is_yes_no):
                print("Yes")
            else:
                print("No")
            found_result = True
        if dead_or_alive == 'lives':
            if is_dead(entity_name, entity_tag, is_yes_no):
                print("No")
            else:
                print("Yes")
            found_result = True
    if not found_result:
        if answer_ent == "Entity_corresponds":
            print("Yes")
            found_result = True
        if answer_ent == "Entity_different":
            print("No")
            found_result = True
        if answer_ent == "No_property_in_sentence":
            found_result = yes_no_query(entity_tag, entity_tag2, entity_name2)
    return found_result


'''Loops over a sentence to find words like dead and lives'''
def death_in_yes_no(parse):
    dead_or_alive = ''
    for counter, death_prop in enumerate(parse, 0):
        if death_prop.dep_ == 'ROOT' or death_prop.dep_ == 'acomp':
            if death_prop.lemma_ == 'alive' or death_prop.lemma_ == 'live':
                dead_or_alive = 'lives'
            if death_prop.lemma_ == 'dead' or death_prop.lemma_ == 'die':
                dead_or_alive = 'died'
            if death_prop.lemma_ == 'pass':
                if parse[counter + 1].lemma_ == 'away':
                    dead_or_alive = 'died'
    return dead_or_alive


'''Performs a query for yes/no questions in which two entities are given, 
   when a connection between the entities exists the function returns 'TRUE'.'''
def yes_no_query(entity, entity2, entity_name2):
    query = '''
            ASK WHERE {wd:%s ?prop wd:%s}
            ''' % (entity, entity2)
    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()
    if data['boolean']:
        print("Yes")
    else:
        # Try the second best entity
        entity2 = find_tag(entity_name2, ENTITY, 1, False, '', False)
        query = '''
                ASK WHERE {wd:%s ?prop wd:%s}
                ''' % (entity, entity2)
        data = requests.get(sparql_url,
                            params={'query': query, 'format': 'json'}).json()
        if data['boolean']:
            print("Yes")
        else:
            # Also try to read the entity name as a property? e.g. Does Michael Jackson have a nickname?
            property_tag = find_tag(entity_name2, PROPERTY, FIRST_TRY, False, '', False)
            answer_ent_as_prop = ent_prop_answer(property_tag, entity, '')
            if answer_ent_as_prop:
                print("Yes")
            else:
                print("No")
    return True


'''This function looks if an entity property combination gives an answer, e.g. Does Michael Jackson have a nickname?'''
def ent_prop_answer(prop_tag, entity_tag, entity_name2):
    query = '''
         SELECT ?property WHERE {
             wd:%s wdt:%s ?prop.
             SERVICE wikibase:label {
                 bd:serviceParam wikibase:language "en".
                 ?prop rdfs:label ?property
             }
         }''' % (entity_tag, prop_tag)
    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()

    # If no answer is found return empty
    if data['results']['bindings']:
        return True
    else:
        return False


'''This function first looks for entities and properties given the line'''
def create_and_fire_query(line):
    nlp = spacy.load('en')
    parse = nlp(line.strip())
    entity_name = entity_tag = 'None'
    entity_name2 = ''  # SET THIS TO EMPTY (line 594)
    found_result = is_count = is_age = is_location = is_yes_no = False

    '''YES/NO QUESTIONS'''
    # If the first word is a form of to be or to do it is a Yes/No question
    if parse:  # if parse is not null
        # The capital letters are added for the simple forms since these don't get converted to lowercase somehow
        if parse[0].lemma_ in yes_no_words:
            is_yes_no = True
            entity_tag2 = 'None'

    for token in parse:
        if token.text == "age" or token.text == "old":  # if the question contains age or old, the user request an age
            is_age = True
        if token.text in location_words:  # sentences starting with "where" are about locations
            is_location = True

    '''Look for entity'''
    i = 0
    for ent_name in parse.ents:  # Try to find the entity with the entity method first
        if i == 0:
            if ent_name.label_ != 'LOC' and ent_name.label_ != 'DATE':
                entity_name = ent_name.lemma_.replace("'s", "").replace("'", "")
                entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY, is_age, '', is_location)
                i += 1
        # Try finding a second standard entity here
        else:
            entity_name2 = ent_name.lemma_.replace("'s", "").replace("'", "")
            entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
            if is_yes_no:
                found_result = answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2,
                                             entity_name2)

    if entity_name == 'None':  # If no entity was found use the proper noun or object method to find entity
        for ent_name in parse:
            # Seems dangerous to look for pobj here because you're most often looking for the subject of the sentence?
            if ent_name.pos_ == 'PROPN' or ent_name.dep_ == 'pobj' or ent_name.dep_ == 'nsubj':
                if ent_name.dep_ == 'compound':
                    if ent_name.pos_ == 'PROPN':  # and ent_name.head.lemma_ != ent_name.head.text:  # WAAROM ZOU JE DIT DOEN? DEZE DINGEN ZIJN (VRIJWEL) ALTIJD HETZELFDE!
                        entity_name = " ".join((ent_name.text, ent_name.head.text))  # IF compound !!!
                        break  # A proper noun compound is most likely the entity of interest e.g. Green Day
                    else:
                        entity_name = " ".join((ent_name.lemma_, ent_name.head.lemma_))
                else:
                    entity_name = ent_name.lemma_.replace("'s", "").replace("'", "")
                entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY, is_age, '', is_location)

    if is_yes_no and not found_result:
        # The loop always continues until the last word in the sentence, which is nice, since English (yes/no)
        # is structured according to Subject Verb Object, and we need object
        for counter, word in enumerate(parse, 0):
            if word.dep_ == 'compound' or word.dep_ == 'amod':
                entity_name2 = " ".join((word.lemma_, word.head.lemma_))
                if entity_name == entity_name2:  # When the entity found is the same as entity 1, go to next word
                    continue
                entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
                if entity_tag2 == 'empty':
                    continue
                else:
                    break

            if word.dep_ == 'attr' or word.dep_ == 'npadvmod' or word.dep_ == 'dobj' \
                    or word.dep_ == 'pobj' or word.dep_ == 'ROOT' or word.dep_ == 'nsubj':
                if counter + 1 < len(parse):
                    # If the next word is a numerical modifier, add it to entity e.g. Jackson 5
                    if parse[counter + 1].dep_ == 'nummod':
                        entity_name2 = word.lemma_ + ' ' + parse[counter + 1].lemma_
                    else:
                        entity_name2 = word.lemma_
                # If it found the same name find another one or it's a ROOT 'be'
                if entity_name == entity_name2 or entity_name2 == 'be':
                    continue
                entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY, is_age, '', is_location)
                # if subject of the sentence if found, switch subject and object around AND the found
                # string is not a substring of the first entity (because substrings are different,
                # but sometimes classified as 'nsubj')
                if word.dep_ == 'nsubj' and entity_name2 not in entity_name2:
                    entity_tag, entity_tag2 = entity_tag2, entity_tag
                    entity_name, entity_name2 = entity_name2, entity_name
                if entity_tag2 == 'empty':
                    continue
        # if entity 2 is not empty find a yes/no answer
        if entity_tag2 != 'None':
            found_result = answer_yes_no(parse, entity_tag, entity_name, is_yes_no, found_result, entity_tag2,
                                         entity_name2)
    if not found_result:
        '''QUICK FIND'''
        prop_name = ""

        for token in parse:
            if token.pos_ == "ADJ":
                if "st" in token.text:
                    prop_name = prop_name + token.text + " "

            elif token.dep_ == "advmod":
                if token.text in things_of:
                    if token.head.lemma_ in things_of:
                        prop_name = prop_name + things_of[token.head.lemma_]
                    else:
                        prop_name = prop_name + things_of[token.text]
                    if token.head.lemma_ != "long" and token.head.lemma_ != "old":
                        prop_name = prop_name + " of "

            elif token.dep_ == "ROOT" or token.dep_ == "advcl":
                if token.lemma_ in roots:
                    if "of" not in prop_name:
                        prop_name = prop_name + " of "
                    prop_name = prop_name + roots[token.lemma_]
                else:
                    if token.lemma_ == 'stand' and entity_tag:
                        found_result = stands_for(entity_tag)

            elif token.tag_ in noun_tags:
                # If P is in the token tag, then its token text is an entity
                if "P" not in token.tag_:
                    if prop_name in things_of.values() and not token.lemma_ in things_of.values() and prop_name != "duration" and prop_name != "age":
                        prop_name = prop_name + " of " + replace(token.lemma_)
                    elif token.dep_ == "compound":
                        prop_name = prop_name + replace(token.lemma_) + " " + replace(token.head.lemma_)
                    elif token.dep_ != "pobj" and ((not prop_name) or ("st" in prop_name)):
                        prop_name = prop_name + replace(token.lemma_)
                if not prop_name and token.head.lemma_ == "in":
                    prop_name = "has part"
                    break

        if prop_name != "" and not found_result:
            ent_tag = find_tag(entity_name, ENTITY, FIRST_TRY, is_age, '', is_location)
            prop_name = prop_name.replace("year of ", "")  # simply stays the same if "year of" is not in there

            prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY, is_age, ent_tag, is_location)
            found_result = print_answer(prop_tag, ent_tag, is_count, is_age)
            # If it didn't find anything, then try disambiguating result
            if not found_result:
                found_result = try_disambiguation(prop_name, entity_name, is_count, found_result, is_age, is_location)
                if entity_name2:
                    found_result = try_disambiguation(prop_name, entity_name2, is_count, found_result, is_age,
                                                      is_location)

    '''SLOW FIND'''
    if not found_result:
        '''Look for property'''
        property_name = ""
        for prop_name in parse:
            # Uses the word 'many' to indicate counting
            if prop_name.pos_ == 'ADJ' and prop_name.lemma_ == 'many':
                is_count = True

            # If the property consists of multiple words join them together
            if not found_result:
                if (prop_name.dep_ == 'compound' and prop_name.tag_ == 'NN') or \
                        (prop_name.pos_ == 'ADJ' and prop_name.dep_ == 'amod'):
                    # Dit prop.text instead of prop,lemma_ because you want the full adjective e.g. highest (note)
                    property_name = " ".join((replace(prop_name.text), replace(prop_name.head.lemma_)))
                # This fires (mostly) for NOUNS (some entities as well if the not condition is omitted)
                if prop_name.dep_ != 'compound' and (
                        prop_name.dep_ == 'nsubj' or prop_name.dep_ == 'attr' or prop_name.tag_ == 'NN') and \
                        not found_result and entity_name != prop_name.lemma_:
                    property_name = replace(prop_name.lemma_)

                if prop_name.dep_ == 'acl' or prop_name.dep_ == 'dobj' and not found_result:  # The dobj is mainly for count questions
                    property_name = replace(prop_name.text)

                if prop_name.dep_ == 'ROOT' and not found_result:
                    property_name = replace(prop_name.head.lemma_)
                # If the root is 'to be' don't look up property (irrelevant to do, and gives erroneous results)
                if property_name and not property_name == 'be':
                    property_tag, found_result = find_answer(property_name, entity_name, entity_tag, is_count, is_age,
                                                             is_location)
                    if not found_result:  # If you don't find a result don't try again with the same name
                        maybe_ent = property_name
                        property_name = ""

        '''Print how the program did'''
        if not found_result and line:  # 'and line' means the line is not empty
            # Property empty so probably asking for a description
            # For what is ... questions
            if entity_tag != 'None':
                give_description(entity_tag)
            else:
                if maybe_ent:
                    entity_tag = find_tag(maybe_ent, ENTITY, FIRST_TRY, False, '', False)
                    give_description(entity_tag)
                else:
                    print(error_msg)


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
def find_property_answer(parse, entity_tag, entity_name, entity_tag2, entity_name2):
    prop_name = ''
    prop_tag = ''
    for counter, token in enumerate(parse, 0):
        if token.dep_ == 'compound':  # compound property
            if parse[counter + 1].dep_ == 'attr' or parse[counter + 1].dep_ == 'appos':
                prop_name = token.lemma_ + ' ' + token.head.lemma_
                break
        if token.dep_ == 'appos' or token.dep_ == 'attr':
            if token.lemma_ != entity_name2 and token.lemma_ != entity_name:  # For example 'male' would be found as entity2 and property
                prop_name = token.lemma_
        # The question uses possesive form, therefore entities need to be switched: # if it's possesively written e.g. Is Michael Jackson's nickname Bambi? then switch entities
        # We use check if the possesive word was already in the first entity as well, in case we found entities the wrong way around
        if token.dep_ == 'poss' and token.lemma_ in entity_name:
            entity_tag, entity_tag2 = entity_tag2, entity_tag
            entity_name, entity_name2 = entity_name2, entity_name

    if prop_name:
        prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY, False, entity_tag2, False)
        if prop_tag == 'empty':  # If no tag has been found we try adding 'of' to the property since lots of properties are defined that way e.g. instance of, part of, father/daughter of
            prop_name = prop_name + " of"
            prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY, False, entity_tag2, False)

    if prop_tag == EMPTY or not prop_tag or entity_name == 'None' or prop_tag == 'empty':  # Else property tag is empty, so we assume no property has been found
        return "No_property_in_sentence"  # return that the answer of the yes/no entity query should be respected
    else:
        same_result = compare_answer(prop_tag, entity_tag2, entity_name)
        # If the entity name answer using a property is the same as the second entity in the question
        if same_result:
            return "Entity_corresponds"
        # The entity and the answer don't correspond (e.g. asking if Billy is the Wife of Miley Cyrus)
        else:
            return "Entity_different"


'''This function is for yes/no questions. It queries the database to see if it finds the second entity in 
   the sentence, after which it compares the queried and sentence entity. 
   Finally, it returns the answer to find_property_answer'''
def compare_answer(prop_tag, entity_tag, entity_name2):
    query = '''
         SELECT ?property WHERE {
             wd:%s wdt:%s ?prop.
             SERVICE wikibase:label {
                 bd:serviceParam wikibase:language "en".
                 ?prop rdfs:label ?property
             }
         }''' % (entity_tag, prop_tag)
    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()

    # If no answer is found return empty
    if len(data['results']['bindings']) == EMPTY:
        return EMPTY
    if len(data['results'][
               'bindings']) > 1:  # Then it is a list. Therefore, just check if the entity in sentence is in the list
        for item in data['results']['bindings']:
            for var in item:
                if str(item[var]['value']) == entity_name2:
                    return True
        return False  # If you go through the entire list without finding an answer, return False
    for item in data['results']['bindings']:
        for var in item:
            if str(item[var]['value']) == entity_name2:
                return True
            else:
                return False

def print_from_file():
    with open('test_questions.txt') as f:
        for i, line in enumerate(f, 1):
            # print(line)
            line = line.rstrip().lstrip(str(i)).lstrip("\t")
            print(str(i), "\t", end="")
            create_and_fire_query(line)

def main(argv):
    # print_example_queries()
    print_from_file()
    for line in sys.stdin:
        print(user_msg)
        line = line.rstrip()
        create_and_fire_query(line)


# Is this file ran directly from python or is it being imported?
if __name__ == "__main__":
    main(sys.argv)