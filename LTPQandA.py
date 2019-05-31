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

nountags = ["NN", "NNS", "NNP", "NNPS"]
things_of = {"When": "date", "Where": "place", "many": "number", "long": "duration", "old": "age", "How": "cause"}

example_queries = [
    # What-questions
    "What was the cause of death of Mozart?",
    "What were the causes of death of Michael Jackson?",
    "What is the gender of Conchita Wurst?",
    "What is the highest note of a piano?",  # defined
    "What is the record label of The Clash",
    "What is the real name of Eminem?",  # real name ipv birth name, werkt dat? Miss try_disambiquation in quick find?
    "What is the website of Mumford and Sons?",  # Mumford & Sons?
    "What is the birth date of Elvis Presley?",

    # Who-questions
    "Who was the composer of The Four Seasons?",
    "Who was the father of Michael Jackson?",
    "Who is the stepparent of Neneh Cherry",

    # Qualified statement questions
    "Who are the members of Metallica?",
    "Who is the wife of John Mayer?",  # niet heel qualified, feel free to add

    # List questions
    "Name the record labels of John Mayer.",
    "Name the partners of Bruce Springsteen.",
    "what are the genres of the White Stripes?",
    "Who were in Queen?",
    "Who were the members of The Beatles",
    "Who are the children of Phill Collins?",
    "which were the pseudonyms of David Bowie",

    # Rewritten What-questions
    "Where is the birthplace of Bob Marley?",
    "Where was the origin of Coldplay?",
    "When is the deathdate of John Lennon?",
    "When was Jimi Hendrix born?",
    "When did Prince die?",
    "How did Michael Jackson die?",  # meerdere oorzaken
    "How did Tupac Shakur die?",  # een oorzaak
    "what is Lady Gaga's birth name?",
    "Which country is Queen from?",
    "How long is Bohemian Rhapsody?",
    "In what city was Die Antwoord formed?",
    "What year was the song ’1999’ by Prince published?",  # prints 1999-01-01T00:00:00Z
    "For what genre are music duo The Upbeats best known?",
    "What does EDM stand for?",  # definition
    "What is a kazoo?",  # definition

    # count questions
    "How many members does Nirvana have?",
    "How many children does Adele have?",  # defined
    # feel free to add

    # yes/no questions
    "Did Prince die?",  # ent+prop
    "Did Michael Jackson play in a band?",  # ent + prop (?)
    "Do The Fals make indie rock?",  # 2x entity (?)
    "Is Michael Jackson male?",  # 2x entity
    "Is Miley Cyrus the daughter of Billy Ray Cyrus?",  # 2x entity
    "Does deadmau5 make house music?",  # 2x entity
]

# questions to test extra things on
''', "How old was Ella Fitzgerald when she died?",
"How old is Eminem?", #also qualified
"What is the age of Eminem", #also qualified
"Who was the first husband of Yoko Ono?"
"Who was Mozarts oldest child?",
"To which musical genre(s) can The White Stripes be assigned?"'''

error_msg = "No data found. Try paraphrasing the question (e.g. Prince becomes TAFKAP)."
user_msg = "Please enter a question or quit program by pressing control-D."


'''This function print the examples above and runs the search for answers on them one line at a time '''
def print_example_queries():
    for index, example in enumerate(example_queries):
        print("(" + str(index + 1) + ") " + example)
        create_and_fire_query(example)
    # Op dit moment vindt quick find 24 and slow find 11 antwoorden
    print("quick finds = " + str(quick_find) + " slow finds = " + str(slow_find) + " not founds = " + str(not_found))
    print(user_msg)


'''This function print the answers based on their found property and entity tags'''
def print_answer(property, entity, is_count):
    date = False
    # Is the property a birth date, death, disappeared, inception, abolished, publication, first performance  ?
    if (property == 'P569') | (property == 'P570') | (property == 'P571') | (property == 'P576') | \
            (property == 'P577') | (property == 'P1191'):
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
        }''' % (entity, property)

    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()
    # If no answer is found return empty
    if len(data['results']['bindings']) == EMPTY:
        return EMPTY
    for item in data['results']['bindings']:
        for var in item:
            ## Dit werkt nog niet omdat het query_property zou moeten zijn (i.e. de volledige naam)
            # if property == "duration":
            #     print(" seconds", end="")
            if date:
                date = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
                print("   ANSWER: " + str(date.day), str(date.strftime("%B")), str(date.year))
            if not date:
                # Only print counts higher than 0 (else it didn't find one and the list is empty)
                if is_count and item[var]['value'] == '0':
                    return False

                print("   ANSWER: " + item[var]['value'])
    return True


''' This function tries different entity and property disambiguations. It then also tries to find 
    an answer with each of these disambiguated combinations'''
def try_disambiguation(property_name, entity_name, is_count, found_result):
    index_entities = 0
    entity_tag = find_tag(entity_name, ENTITY, index_entities)
    while not found_result and index_entities < 2:  # look through 2 different entities
        index_properties = 0
        while not found_result and index_properties < 7:  # look though 7 different properties
            property_tag = find_tag(property_name, PROPERTY, index_properties)
            # If no more results can be found by ambiguation stop the loop
            if property_tag == "empty":
                break
            found_result = print_answer(property_tag, entity_tag, is_count)
            index_properties += 1
        index_entities += 1
        entity_tag = find_tag(entity_name, ENTITY, index_entities)
        if entity_tag == "empty":
            break
    return found_result


''' Find a property or entity tag from the WikiData API given the current property/entity name
    The index indicates which tag in the API's list of tags needs to be returned'''
def find_tag(name, ent_or_prop, index):
    if ent_or_prop == ENTITY:  # Currently looking for the most referenced entity
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json'}
    if ent_or_prop == PROPERTY:  # Currently looking for the most referenced property
        params = {'action': 'wbsearchentities', 'language': 'en', 'format': 'json', 'type': 'property'}
    params['search'] = name
    json = requests.get(wiki_api_url, params).json()
    for iteration, result in enumerate(json['search'], start=0):
        if index == FIRST_TRY:  # return only the first result, since that is the most referenced one
            return result['id']
        if iteration == index:  # if the first result didn't give an answer when the query fired
            return result['id']
    return "empty"  # at the end of the API list, return empty so no redundant empty statements are evaluated


def yes_no_query(entity, entity2):
    query = '''
            ASK WHERE {wd:%s ?prop wd:%s}
            ''' % (entity, entity2)
    data = requests.get(sparql_url,
                        params={'query': query, 'format': 'json'}).json()
    if data['boolean']:
        print("    ANSWER: Yes")
    else:
        print("    ANSWER: No")
    return True


'''This function first looks for entity names in the line, then  '''
def create_and_fire_query(line):
    nlp = spacy.load('en')
    parse = nlp(line.strip())
    entity_name = 'None'
    entity_tag = 'None'
    found_result = False
    is_count = False
    is_yes_no = False
    ent_name = ""
    prop_name = ""

    '''YES/NO QUESTIONS'''
    # If the first word is a form of to be or to do it is a Yes/No question
    if parse: # if parse is not null
        if parse[0].lemma_ == 'do' or parse[0].lemma_ == 'be':
            print("This is a YES/NO question")
            is_yes_no = True
            entity_tag2 = 'None'

    '''Look for entitiy'''
    i = 0
    for ent_name in parse.ents:  # Try to find the entity with the entity method first
        if i == 0:
            entity_name = ent_name.lemma_
            entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY)
            print('Found slow entity in parse.ents. Entity_tag: -' + str(entity_name) + '- entity: -' + str(
                entity_tag) + "-")
            i += 1
        else:
            entity_name2 = ent_name.lemma_
            entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY)
            print('Found slow entity2 in parse.ents. Entity_tag: -' + str(entity_name2) + '- entity: -' + str(
                entity_tag2) + "-")

    if is_yes_no:
        for ent_name2 in parse:
            if ent_name2.pos_ == 'PROPN' and ent_name2.dep_ == 'compound':
                entity_name2 = " ".join((ent_name2.lemma_, ent_name2.head.lemma_))
                entity_tag2 = find_tag(entity_name2, ENTITY, FIRST_TRY)
                print('Found slow entity in parse.ents. Entity_tag: -' + str(entity_name2) + '- entity: -' + str(
                    entity_tag2) + "-")
                break
        if entity_tag2 != 'None':  # if entity 2 is not empty
            found_result = yes_no_query(entity_tag, entity_tag2)

    if entity_name == 'None':  # If no entity was found use the proper noun or object method to find entity
        for ent_name in parse:
            if ent_name.pos_ == 'PROPN' or ent_name.dep_ == 'pobj':
                entity_name = ent_name.lemma_
                entity_tag = find_tag(entity_name, ENTITY, FIRST_TRY)
                print('Found slow entity as proper noun or pobj. Query_ent: -' + str(
                    entity_name) + '- entity: -' + str(entity_tag) + "-")

    if not found_result:
        '''QUICK FIND'''
        for token in parse:
            if token.pos_ == "ADJ":
                if "st" in token.text:
                    print("ADJective property: -" + prop_name + token.text + "-")
                    prop_name = prop_name + token.text + " "

            elif token.dep_ == "advmod":
                if token.text in things_of:
                    if token.head.lemma_ in things_of:
                        print("Property: -" + prop_name + things_of[token.head.lemma_] + "- Token head lemma of Adverbial modifier (advmod)")
                        prop_name = prop_name + things_of[token.head.lemma_]
                    else:
                        print("Property: -" + prop_name + things_of[token.text] + "- Token text of Adverbial modifier (advmod)")
                        prop_name = prop_name + things_of[token.text]
                    if token.head.lemma_ != "long":
                        print("Property: " + prop_name + " of- Long Adverbial modifier (advmod)")
                        prop_name = prop_name + " of "

            elif token.dep_ == "ROOT" or token.dep_ == "advcl":
                if token.text == "born":
                    prop_name = prop_name + "birth"
                elif token.lemma_ == "die":
                    prop_name = prop_name + "death"
                elif token.lemma_ == "come":
                    prop_name = prop_name + "origin"
                print("Property: -" + prop_name + "- ROOT or adverbial clause modifier (advcl). It's birth, death or origin")

            elif token.tag_ in nountags:
                # If P is in the token tag, then its token text is an entity
                if not "P" in token.tag_:  # MOET DIT NIET OMGEKEERD ZIJN if "P" not in???
                    if prop_name in things_of.values():
                        prop_name = prop_name + " of " + token.lemma_
                        print("Property: -" + prop_name + "- P is not in token tag. In things_of found")
                    elif token.dep_ != "pobj":
                        # If 'S' is in the token tag, then it's probably plural (NNS or NNPS). Therefore use token text.
                        if (token.text == "members") or not ("S" in token.tag_):
                            prop_name = prop_name + token.text
                            print("Property: -" + prop_name + "- Not object of a preposition (pobj). No 'S' in token tag")
                        else:
                            prop_name = prop_name + token.lemma_
                            print("Property: -" + prop_name + "- Object of a preposition (pobj)")
                    else:
                        ent_name = ent_name + token.text + " "
                        print("Entity: -" + ent_name + "- P is not in token tag and prop is not in things_of.")
                else:
                    # Adds every entity in the phrase together
                    ent_name = ent_name + token.text + " "
                    print("Entity: -" + ent_name + "- P is in token tag")
        # If slow find found a property and an entity, Try to print an answer
        if not prop_name == "" and not ent_name == "":
            prop_tag = find_tag(prop_name, PROPERTY, FIRST_TRY)
            ent_tag = find_tag(ent_name, ENTITY, FIRST_TRY)
            found_result = print_answer(prop_tag, ent_tag, is_count)
            print("   QUICK FIND FOUND entity: -" + ent_tag + " " + ent_name + "- and property: -" + prop_tag + " " + prop_name + "-")
            # If it didn't find anything, then try disambiguating result
            if not found_result:
                print("DISAMBIGUATION phase quick find")
                found_result = try_disambiguation(prop_name, ent_name, is_count, found_result)
            if found_result:
                global quick_find
                quick_find += 1
                print("Quick find count = " + str(quick_find))

    # the following can be combined with 145-179!!!
    '''SLOW FIND'''
    if not found_result:
        print("---> GOING TO SLOW FIND")
        '''Look for property'''
        for prop_name in parse:
            # Uses the word 'many' to indicate counting (maybe also use 'number of' or 'amount of'?)
            if prop_name.pos_ == 'ADJ' and prop_name.lemma_ == 'many':
                print("Seeing this as a COUNT question")
                is_count = True

            # If the property consists of multiple words join them together
            if not found_result and (prop_name.dep_ == 'compound' and prop_name.tag_ == 'NN') or \
                    (prop_name.pos_ == 'ADJ' and prop_name.dep_ == 'amod'):
                # Dit verandert naar prop.text ipv prop,lemma_ omdat je het volledige bijv naamwoord wilt (e.g. highest note)
                property_name = " ".join((prop_name.text, prop_name.head.lemma_))
                property_tag = find_tag(property_name, PROPERTY, FIRST_TRY)
                print("Trying property: -" + property_name + "-, as compound or as adjectival modifier (amod)")
                found_result = print_answer(property_tag, entity_tag, is_count)
                if not found_result:
                    found_result = try_disambiguation(property_name, entity_name, is_count, found_result)
            # This fires (mostly) for NOUNS (some entities as well if the not condition is omitted)
            if prop_name.dep_ != 'compound' and (prop_name.dep_ == 'nsubj' or prop_name.dep_ == 'attr' or prop_name.tag_ == 'NN') and \
                    not found_result and entity_name != prop_name.lemma_:
                property_name = prop_name.lemma_
                if ('member' or 'members') in property_name:  # Change member(s) in 'part of' since that is how it is referenced in WikiData
                    property_name = 'has part'

                property_tag = find_tag(property_name, PROPERTY, FIRST_TRY)
                print("Trying property: -" + property_name + "-, as nominal subject (nsubj), attribute (attr) or common noun (NN)")
                found_result = print_answer(property_tag, entity_tag, is_count)
                if not found_result:
                    found_result = try_disambiguation(property_name, entity_name, is_count, found_result)

            if prop_name.dep_ == 'acl' or prop_name.dep_ == 'dobj' and not found_result:  # The dobj is mainly for count questions
                property_name = prop_name.text
                property_tag = find_tag(property_name, PROPERTY, FIRST_TRY)
                if ('member' or 'members') in property_name:  # change member in 'has part' of since that is how it is referenced in WikiData
                    property_name = 'has part'

                print("Trying property: -" + property_name + "-, as a clausal modifier of noun (acl) or direct object (dobj)")
                found_result = print_answer(property_tag, entity_tag, is_count)
                if not found_result:
                    found_result = try_disambiguation(property_name, entity_name, is_count, found_result)

            if prop_name.dep_ == 'ROOT' and not found_result:
                property_name = prop_name.head.lemma_
                # If the root is 'to be' don't look up property (irrelevant to do, and erroneous results)
                if not property_name == 'be':
                    property_tag = find_tag(property_name, PROPERTY, FIRST_TRY)
                    print("Trying property: -" + property_name + "-, as root (a word that means something)")
                    found_result = print_answer(property_tag, entity_tag, is_count)
                    if not found_result:
                        found_result = try_disambiguation(property_name, entity_name, is_count, found_result)

        '''Print how the program did'''
        if not found_result and line:  # and line means the line is not empty
            print(error_msg)
            global not_found
            not_found += 1
        else:
            global slow_find
            slow_find += 1
            if not is_yes_no:
                print("SLOW FIND FOUND entity: -" + entity_name + " " + entity_tag + "- and property: -" + property_tag + " " +  property_name + "-")
            print("Slow find count = " + str(slow_find))


def main(argv):
    global quick_find
    global slow_find
    global not_found
    quick_find = 0
    slow_find = 0
    not_found = 0
    # print_example_queries()
    for line in sys.stdin:
        # line = example_queries[int(line)-1].rstrip()
        line = line.rstrip()
        create_and_fire_query(line)


# Is this file ran directly from python or is it being imported?
if __name__ == "__main__":
    main(sys.argv)
