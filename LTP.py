#!/usr/bin/env python3
import spacy, sys, requests, re
from datetime import datetime
nlp = spacy.load('en')
apiurl = 'https://www.wikidata.org/w/api.php'
url = 'https://query.wikidata.org/sparql'
params = {'action':'wbsearchentities','language':'en','format':'json'}
paramsprop = {'action':'wbsearchentities','language':'en','format':'json', 'type':'property'}

examples = [
	#What-questions
	"What was the cause of death of Mozart?",
	"What were the causes of death of Michael Jackson?",
    "What is the gender of Conchita Wurst?",
    "What is the highest note of a piano?", #defined
    "What is the record label of The Clash",
    "What is the real name of Eminem?", #real name ipv birth name, werkt dat? 
    "What is the website of Mumford and Sons?", #Mumford & Sons?
    "What is the birth date of Elvis Presley?",
    
    #Who-questions
    "Who was the composer of The Four Seasons?",
    "Who was the father of Michael Jackson?",
    "Who is the stepparent of Neneh Cherry",
    
    #Qualified statement questions
    "Who are the members of Metallica?",
    "Who is the wife of John Mayer?", #niet heel qualified, feel free to add
    
    #List questions
    "Name the record labels of John Mayer.",
	"Name the partners of Bruce Springsteen.",
	"what are the genres of the White Stripes?",
	"Who were in Queen?",
	"Who were the members of The Beatles",
	"Who are the children of Phill Collins?",
	"which were the pseudonyms of David Bowie",
	
    #Rewritten What-questions
    "Where is the birthplace of Bob Marley?",
    "Where was the origin of Coldplay?",
    "When is the deathdate of John Lennon?",
    "When was Jimi Hendrix born?",
    "When did Prince die?",
    "How did Michael Jackson die?", #meerdere oorzaken
    "How did Tupac Shakur die?", #een oorzaak
    "what is Lady Gaga's birth name?", 
    "Which country is Queen from?",
    "How long is Bohemian Rhapsody?"
    "In what city was Die Antwoord formed?",
    "What year was the song ’1999’ by Prince published?",
    "For what genre are music duo The Upbeats best known?",
    "What does EDM stand for?", #definition
    "What is a kazoo?",	#definition
    
    #count questions
    "How many members does Nirvana have?",
    "How many children does Adele have?", #defined
    #feel free to add
    
    #yes/no questions
    "Did Prince die?", #ent+prop
    "Did Michael Jackson play in a band?", #ent + prop (?)
    "Do The Fals make indie rock?", #2x entity (?)
    "Is Michael Jackson male?", #2x entity
    "Is Miley Cyrus the daughter of Billy Ray Cyrus?" #2x entity
    "Does deadmau5 make house music?" #2x entity
    
    #extra things
    ''', "How old was Ella Fitzgerald when she died?",
    "How old is Eminem?", #also qualified
    "What is the age of Eminem", #also qualified
    "Who was the first husband of Yoko Ono?"
    "Who was Mozarts oldest child?",
    "To which musical genre(s) can The White Stripes be assigned?"'''
    ]

errormsg = "no data found. Try paraphrasing the question (e.g. Prince becomes TAFKAP)."
qprint = "Please enter a question or quit program by pressing control-D."

print("Hello! Here are ten example questions.")

for index, example in enumerate(examples):
	print("("+str(index+1)+") "+example)
print("As you can see, punctuation is optional. Please use whitespaces and type names with capitals, though.")
print(qprint)

def printAnswer(data):
	#Print the answer(s)
	print("Answer:", end = " ")
	if 'boolean' in data:
		if data['boolean']:
			print("Yes.")
		else:
			print("No.")
	else:
		answerCount = len(data['results']['bindings'])
		for item in data['results']['bindings']:
			for var in item:
				'''Filter out dates from datetime strings; check for both colons and hyphens to ensure it's not 
				a term/name with a hyphen (e.g. Jean-Luc, post-punk) or some non-datetime string with a colon.'''
				if (item[var]['value'].find(':')>=0) and (item[var]['value'].find('-')>=0):
					date = datetime.strptime(item[var]['value'], '%Y-%m-%dT%H:%M:%SZ')
					print(date.day, date.strftime("%B"), date.year, end = "")
				else:
					print(item[var]['value'], end = "")
					#Duration of a song should be in seconds. 
					if (prop == "duration"):
						print(" seconds", end = "")
				answerCount=answerCount-1
				if answerCount>0:
					print(",", end = " ")
				else:
					print(" ")

def chooseQuery(entity, entity2, property):
	''' Choose between "regular", list, number-of(count), yes/no, or qualified-statement'''
	#regular: when the answer is an entity
	query = "SELECT ?answerLabel WHERE { wd:%s wdt:%s ?answer. ?answer rdfs:label ?answerLabel. FILTER(LANG(?answerLabel)='en') }" % (entity, property)
	
	#regular: when the answer is not an entity (name/date/defined-number-of)
	query = "SELECT ?answer WHERE { wd:%s wdt:%s ?answer. }" % (entity, property)
	
	#count (pas gebruiken als er geen number-of gedefinieerd is!)
	query = "SELECT distinct (count(?albums) AS ?number) WHERE { wd:%s wdt:%s ?albums . }" % (entity, property)
	
	#list
	query="SELECT DISTINCT ?answerLabel WHERE {wd:%s p:P527 ?statement. ?statement ps:P527 ?answer. ?answer rdfs:label ?answerLabel. FILTER(LANG(?answerLabel)='en') }" % (entity)
	
	#yes/no met ofwel ent+prop ofwel twee ents
	#query = 
	
	#qualified statement
	#query = 
	
	return query

def findAnswer(bestent, bestprop):
	data = requests.get(url,params={'query': chooseQuery(bestent, bestent, bestprop), 'format': 'json'}).json()
	if not data['results']['bindings']:
		print("HELP")
		return "empty"
	return data
		
for line in examples:
	nountags = ["NN", "NNS", "NNP", "NNPS"]
	thingsOf = {"When":"date", "Where":"place", "many":"number", "long":"duration", "old":"age", "How":"cause"}
	
	ent = ""
	prop = ""
	parse = nlp(line.strip())
	
	print(parse.text)
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
	
	paramsprop['search'] = prop
	jsonprop = requests.get(apiurl,paramsprop).json()
	if not jsonprop['search']:
		print(errormsg)
		print(qprint)
		continue;
	bestprop = jsonprop['search'][0]
	
	params['search'] = ent
	json = requests.get(apiurl,params).json()
	if not json['search']:
		print(errormsg)
		print(qprint)
		continue;
	bestent = json['search'][0]
	
	data = findAnswer(bestent,bestprop)
	if not data['results']['bindings']:
		print(errormsg)
		print(qprint)
		continue;
	
	printAnswer(data)
	print(qprint)
