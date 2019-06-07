import spacy
import sys

# if prop.pos_ == 'ADJ' and prop.dep_ == 'amod' and found_result == FALSE:
#     query_property = " ".join((prop.lemma_, prop.head.lemma_))
#     property = reduce_ambiguity(query_property, PROP, FIRST_TRY)
#     print('query_prop3: ' + str(query_property) + ' property3: ' + str(property))
#     found_result = print_answer(property, entity, is_count)
#     if found_result == FALSE:
#         found_result = try_disambiguation(query_property, query_entity, is_count, found_result)

# if prop.dep_ == 'dobj':  # for count question
#     query_property = prop.text
#     if 'member' in query_property:  # change member in part of since that is how it is referenced in WikiData
#         query_property = 'has part'
#
#     property = reduce_ambiguity(query_property, PROP, FIRST_TRY)
#     print('query_prop5: ' + str(query_property) + ' property5: ' + str(property))
#     found_result = print_answer(property, entity, is_count)
#     if found_result == FALSE:
#         found_result = try_disambiguation(query_property, query_entity, is_count, found_result)

# if prop.dep_ == 'ROOT' and found_result == FALSE:
#     query_property = prop.head.lemma_
#     property = reduce_ambiguity(query_property, PROP, FIRST_TRY)
#     print('query_prop4: ' + str(query_property) + ' property4: ' + str(property))
#     found_result = print_answer(property, entity, is_count)
#     if found_result == FALSE:
#         found_result = try_disambiguation(query_property, query_entity, is_count, found_result)

# What is the real name of Eminem?
# Who is the partner of Jay Z?
# Who is the spouse of Kanye West?
# Where was B.B.King born?
#
# What is the genre of Dio's music?
# What is the gender of Sting

nlp = spacy.load('en')
result = nlp("Who are in Nirvana?")
'''
for w in result:
    print("{} {} {}".format(w.lemma_, w.dep_, w.head.lemma_))
for w in result:
    print(w.text, w.ent_type_)
for w in result:
    print(w.text, w.ent_type_, w.ent_iob_)
for ent in result.ents:
    print("hi")
    print(ent.lemma_, ent.label_)

for w in result:
    if w.dep_ == "nsubj":
        subject=[]
        for d in w.subtree:
            subject.append(d.text)
        print(" ".join(subject))
for token in result:
    print("\t".join((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.lemma_)))
    if token.dep_ == 'compound' and token.tag_ == 'NN':
        property = " ".join((token.lemma_, token.head.lemma_))
        print(property)
'''

for q in sys.stdin :
    parse = nlp(q.strip())
    for token in parse:
        print("\t".join((token.text, token.lemma_, token.pos_, token.tag_, token.dep_, token.head.lemma_)))

    # death = False
    # query = '''
    #         SELECT ?property WHERE {
    #             wd:%s wdt:%s ?prop.
    #             SERVICE wikibase:label {
    #                 bd:serviceParam wikibase:language "en".
    #                 ?prop rdfs:label ?property
    #             }
    #         }''' % (entity, "P570")  # P570 = date of death
    # death_date = requests.get(sparql_url,
    #                    params={'query': query, 'format': 'json'}).json()
    #
    # for item in death_date['results']['bindings']:
    #     for var in item:
    #         date_end = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
    #
    #         year_of_death = int(str(date_end.strftime("%Y")), 10)
    #         month_of_death = int(str(date_end.strftime("%m")), 10)
    #         date_of_death = int(str(date_end.strftime("%d")), 10)
    #         death = True