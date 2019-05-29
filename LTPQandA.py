#!/usr/bin/python3

import sys
import requests
import spacy
from datetime import datetime

url = 'https://query.wikidata.org/sparql'

FIRST_TRY = 0
ENTITY = 0
PROPERTY = 1
EMPTY = 0

nountags = ["NN", "NNS", "NNP", "NNPS"]
thingsOf = {"When": "date", "Where": "place", "many": "number", "long": "duration", "old": "age", "How": "cause"}

# "Name the record labels of John Mayer .",
# "When is the birthdate of Eminem ?",
# "Where is the birthplace of Bob Marley ?",
# "Who are the children of Phill Collins ?",
# "Where was the origin of Coldplay ?",
# "What was the cause of death of Mozart ?",
# "When is the deathdate of John Lennon ?",
# "Who was the father of Michael Jackson ?",
# "What is the gender of Conchita Wurst ?",
# "Name the partners of Bruce Springsteen .",
# "Who were the husbands of Yoko Ono?",
# "What is the birthdate of Jimi Hendrix?",
# "what were the pseudonyms of David Bowie",
# "What is the date of death of Prince?",
# "what is the number of children of Adele",
# "what were the causes of death of Michael Jackson?",
# "what is the birthname of Lady Gaga?",
# "what are the genres of the White Stripes?",
# "What is the highest note of a piano?",
# "Who were the members of The Beatles"
# "Who were the husbands of Yoko Ono?",
# "What is the birthdate of Jimi Hendrix?",
# "what were the pseudonyms of David Bowie",
# "What is the date of death of Prince?",
# "what is the number of children of Adele",
# "what were the causes of death of Michael Jackson?",
# "what is the birthname of Lady Gaga?",
# "what are the genres of the White Stripes?",
# "Who were the members of The Beatles",
# "What is the highest note of a piano?",
example_queries = '''
    "Name the record labels of John Mayer .",
    "When is the birthdate of Eminem ?",
    "Where is the birthplace of Bob Marley ?",
    "Who are the children of Phill Collins ?",
    "Where was the origin of Coldplay ?",
    "What was the cause of death of Mozart ?",
    "When is the deathdate of John Lennon ?",
    "Who was the father of Michael Jackson ?",
    "What is the gender of Conchita Wurst ?",
    "Name the partners of Bruce Springsteen .",
    "Who were the husbands of Yoko Ono?", 
    "When was Jimi Hendrix born?",
    "which were the pseudonyms of David Bowie", 
    "When did Prince die?",
    "How many children does Adele have?", 
    "How did Michael Jackson die?",
    "what is Lady Gaga's birth name?", 
    "what are the genres of The White Stripes?",
    "What is the highest note of a piano?", 
    "Who were the members of The Beatles"
    Who is the stepparent of Neneh Cherry
    What is the record label of The Clash
    How many members does Nirvana have?
    Which country is Queen from?
    What is the birth place of B. B. King?
    Who are the members of Metallica?
    What is the birth name of Eminem?
    What is the website of Mumford and Sons ?
    Who was the composer of The Four Seasons?
    What is the birth date of Elvis Presley?
    Who is the father of Miley Cyrus?
    '''

def print_example_queries():
    example_queries = '''
    "Name the record labels of John Mayer .",
    "When is the birthdate of Eminem ?",
    "Where is the birthplace of Bob Marley ?",
    "Who are the children of Phill Collins ?",
    "Where was the origin of Coldplay ?",
    "What was the cause of death of Mozart ?",
    "When is the deathdate of John Lennon ?",
    "Who was the father of Michael Jackson ?",
    "What is the gender of Conchita Wurst ?",
    "Name the partners of Bruce Springsteen .",
    "Who were the husbands of Yoko Ono?",
    "What is the birthdate of Jimi Hendrix?",
    "what were the pseudonyms of David Bowie",
    "What is the date of death of Prince?",
    "what is the number of children of Adele",
    "what were the causes of death of Michael Jackson?",
    "what is the birthname of Lady Gaga?",
    "what are the genres of the White Stripes?",
    "What is the highest note of a piano?",
    "Who were the members of The Beatles"
    "Who were the husbands of Yoko Ono?",
    "What is the birthdate of Jimi Hendrix?",
    "what were the pseudonyms of David Bowie",
    "What is the date of death of Prince?",
    "what is the number of children of Adele",
    "what were the causes of death of Michael Jackson?",
    "what is the birthname of Lady Gaga?",
    "what are the genres of the White Stripes?",
    "Who were the members of The Beatles",
    "What is the highest note of a piano?",
    Who is the stepparent of Neneh Cherry
    What is the record label of The Clash
    How many members does Nirvana have?
    Which country is Queen from?
    What is the birth place of B. B. King?
    Who are the members of Metallica?
    What is the birth name of Eminem?
    What is the website of Mumford and Sons ?
    Who was the composer of The Four Seasons?
    What is the birth date of Elvis Presley?
    Who is the father of Miley Cyrus?
    '''
    for questions in example_queries.splitlines():
        print(questions)
        create_and_fire_query(questions)


def print_answer(property, entity, is_count):
    date = False
    # Is the property a birth date, death, disappeared, inception, abolished, publication, first performance  ?
    if (property == 'P569') | (property == 'P570') | (property == 'P571') | (property == 'P576') | \
            (property == 'P577') | (property == 'P1191'):
        date = True

    if is_count:
        query = '''
        SELECT distinct (count(?albums) AS ?number) WHERE {
            wd:%s wdt:%s ?albums .
        } ''' % (entity, property)
        # if is count didn't yield anything try implementing something that tries without count (string of guitar case)
    else:
        query = '''
        SELECT ?property WHERE { 
            wd:%s wdt:%s ?prop.
            SERVICE wikibase:label {
                bd:serviceParam wikibase:language "en".
                ?prop rdfs:label ?property
            }
        }''' % (entity, property)

    data = requests.get(url,
                        params={'query': query, 'format': 'json'}).json()
    if len(data['results']['bindings']) == EMPTY:
        return EMPTY
    for item in data['results']['bindings']:
        for var in item:
            # if property == "duration":
            #     print(" seconds", end="")
            if date:
                date = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
                print(date.day, date.strftime("%B"), date.year)
            if not date:
                if is_count and item[var]['value'] == '0':  # only print counts higher than 0 (else it didn't find one)
                    return False
                print(item[var]['value'])
    return True


# This function tries different entity property disambiguations
def try_disambiguation(query_property, query_entity, is_count, found_result):
    index_entities = 0
    entity = reduce_ambiguity(query_entity, ENTITY, index_entities)
    while not found_result and index_entities < 2:  # look through 2 different entities
        index_properties = 0
        while not found_result and index_properties < 7:  # look though 7 different properties
            property = reduce_ambiguity(query_property, PROPERTY, index_properties)
            if property == "empty":
                break
            found_result = print_answer(property, entity, is_count)
            index_properties += 1
        index_entities += 1
        entity = reduce_ambiguity(query_entity, ENTITY, index_entities)
        if entity == "empty":
            break
    return found_result


def create_and_fire_query(line):
    nlp = spacy.load('en')
    parse = nlp(line.strip())
    query_entity = 'None'
    entity = 'None'
    found_result = False
    is_count = False
    for ent in parse.ents:  # Try to find the entity with the entity method first
        query_entity = ent.lemma_
        entity = reduce_ambiguity(query_entity, ENTITY, FIRST_TRY)
        # print('query_ent: ' + str(query_entity) + ' entity: ' + str(entity))

    if query_entity == 'None':
        for ent in parse:  # If no entity was found use the proper noun or object method to find entity
            if ent.pos_ == 'PROPN' or ent.dep_ == 'pobj':
                query_entity = ent.lemma_
                entity = reduce_ambiguity(query_entity, ENTITY, FIRST_TRY)
                # print('query_ent2: ' + str(query_entity) + ' entity2: ' + str(entity))

    ent = ""
    prop = ""

    for token in parse:
        if (token.pos_ == "ADJ"):
            if ("st" in token.text):
                prop = prop + token.text + " "

        elif (token.dep_ == "advmod"):
            if (token.text in thingsOf):
                if (token.head.lemma_ in thingsOf):
                    prop = prop + thingsOf[token.head.lemma_]
                else:
                    prop = prop + thingsOf[token.text]
                if (token.head.lemma_ != "long"):
                    prop = prop + " of "

        elif ((token.dep_ == "ROOT") or (token.dep_ == "advcl")):
            if (token.text == "born"):
                prop = prop + "birth"
            elif (token.lemma_ == "die"):
                prop = prop + "death"
            elif (token.lemma_ == "come"):
                prop = prop + "origin"

        elif token.tag_ in nountags:
            if (not "P" in token.tag_):
                if (prop in thingsOf.values()):
                    prop = prop + " of " + token.lemma_
                elif ((token.dep_ != "pobj")):
                    if (token.text == "members") or not  ("S" in token.tag_):
                        prop = prop + token.text
                    else:
                        prop = prop + token.lemma_
                else:
                    ent = ent + token.text + " "
            else:
                ent = ent + token.text + " "

    if not prop == "" and not ent == "":
        prop_query = reduce_ambiguity(prop, PROPERTY, FIRST_TRY)
        ent_query = reduce_ambiguity(ent, ENTITY, FIRST_TRY)
        found_result = print_answer(prop_query, ent_query, is_count)

    if not found_result:
        for prop in parse:
            if prop.pos_ == 'ADJ' and prop.lemma_ == 'many':  # Uses the word 'many' to indicate counting (maybe also use 'number of'?)
                is_count = True

            # If the property consists of multiple words join them together
            if not found_result and (prop.dep_ == 'compound' and prop.tag_ == 'NN') or \
                    (prop.pos_ == 'ADJ' and prop.dep_ == 'amod'):
                # Dit verandert naar prop.text ipv prop,lemma_ omdat je het volledige bijv naamwoord wilt (e.g. highest note)
                query_property = " ".join((prop.text, prop.head.lemma_))
                property = reduce_ambiguity(query_property, PROPERTY, FIRST_TRY)
                found_result = print_answer(property, entity, is_count)
                # print('query_prop2: ' + str(query_property) + ' property2: ' + str(property))
                if not found_result:
                    found_result = try_disambiguation(query_property, query_entity, is_count, found_result)
            # This fires (mostly) for NOUNS (some entities as well if the not condition is omitted)
            if prop.dep_ != 'compound' and (prop.dep_ == 'nsubj' or prop.dep_ == 'attr' or prop.tag_ == 'NN') and \
                    not found_result and query_entity != prop.lemma_:
                query_property = prop.lemma_
                if ('member' or 'members') in query_property:  # change member in part of since that is how it is referenced in WikiData
                    query_property = 'has part'

                property = reduce_ambiguity(query_property, PROPERTY, FIRST_TRY)
                found_result = print_answer(property, entity, is_count)
                if not found_result:
                    found_result = try_disambiguation(query_property, query_entity, is_count, found_result)

            if prop.dep_ == 'acl' or prop.dep_ == 'dobj' and not found_result:  # The dobj is mainly for count questions
                query_property = prop.text
                property = reduce_ambiguity(query_property, PROPERTY, FIRST_TRY)
                # print('query_prop3: ' + str(query_property) + ' property3: ' + str(property))
                if ('member' or 'members') in query_property:  # change member in 'has part' of since that is how it is referenced in WikiData
                    query_property = 'has part'

                found_result = print_answer(property, entity, is_count)
                if not found_result:
                    found_result = try_disambiguation(query_property, query_entity, is_count, found_result)

            if prop.dep_ == 'ROOT' and not found_result:
                query_property = prop.head.lemma_
                # If the root is 'to be' don't look up property (irrelevant to do and erroneous results)
                if not query_property == 'be':
                    property = reduce_ambiguity(query_property, PROPERTY, FIRST_TRY)
                    # print('query_prop4: ' + str(query_property) + ' property4: ' + str(property))
                    found_result = print_answer(property, entity, is_count)
                    if not found_result:
                        found_result = try_disambiguation(query_property, query_entity, is_count, found_result)
        if not found_result and line:  # and line means the line is not empty
            print("No answer found. Try paraphrasing the question.")


def reduce_ambiguity(value, ent_prop, index):
    url2 = 'https://www.wikidata.org/w/api.php'
    if ent_prop == ENTITY:  # currently looking for the most referenced entity
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    if ent_prop == PROPERTY:  # currently looking for the most referenced property
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
    params['search'] = value
    json = requests.get(url2, params).json()
    # if not json['search']:
    #     print("help, ent/prop= ", value)
    # if not json['search']:
    #     print("HELP")
    #     return "empty"
    for iteration, result in enumerate(json['search'], start=0):
        if index == FIRST_TRY:  # return only the first result, since that is the most referenced one
            return result['id']
        if iteration == index:  # if the first result didn't give an answer
            return result['id']
    return "empty"  # at the end of the ambiguation list, return empty so no redundant empty statements are evaluated


def main(argv):
    print_example_queries()
    for line in sys.stdin:
        # line = example_queries[int(line)-1].rstrip()  # removes newline
        line = line.rstrip()
        create_and_fire_query(line)


# Is this file ran directly from python or is it being imported?
if __name__ == "__main__":
    main(sys.argv)
