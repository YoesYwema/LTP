#!/usr/bin/env python3
import spacy, sys, requests, re
from datetime import datetime
nlp = spacy.load('en')
apiurl = 'https://www.wikidata.org/w/api.php'
url = 'https://query.wikidata.org/sparql'
params = {'action':'wbsearchentities','language':'en','format':'json'}
paramsprop = {'action':'wbsearchentities','language':'en','format':'json', 'type':'property'}

oldexamples = ["Who were the husbands of Yoko Ono?", "What is the birthdate of Jimi Hendrix?",
			"what were the pseudonyms of David Bowie", "What is the date of death of Prince?",
			"what is the number of children of Adele", "what were the causes of death of Michael Jackson?",
			"what is the birthname of Lady Gaga?", "what are the genres of the White Stripes?",
			"What is the highest note of a piano?", "Who were the members of The Beatles"]
			
newexamples = ["Who were the husbands of Yoko Ono?", "When was Jimi Hendrix born?",
			"which were the pseudonyms of David Bowie", "When did Prince die?",
			"How many children does Adele have?", "How did Michael Jackson die?",
			"what is Lady Gaga's birth name?", "what are the genres of The White Stripes?",
			"What is the highest note of a piano?", "Who were the members of The Beatles"]

moreexamples = ["Where was Mozart born?", "How long is Bohemian Rhapsody?"]

'''With these examples, my program finds the correct property and entity, 
but there is no information on that property of that entity on Wikidata, 
or the property does not exist. In the future I could upgrade my program
to get the length of or first entity in a list of spouses/children/etc, 
and subtract the year of birth from the year of death.'''
noinfoexamples = ["How many husbands did Yoko Ono have?", "How old was Ella Fitzgerald when she died? ", 
				"Who was the first wife of John Lennon?", "Who was the oldest child of Mozart?"]

errormsg = "no data found. Try paraphrasing the question (e.g. Prince becomes TAFKAP)."
qprint = "Please enter a question or quit program by pressing control-D."

print("Hello! Here are ten example questions.")

for index, example in enumerate(newexamples):
	print("("+str(index+1)+") "+example)
print("As you can see, punctuation is optional. Please use whitespaces and type names with capitals, though.")
print(qprint)

def findAnswer(bestent, bestprop):
	'''Weirdquery is a query, e.g. a date, number, or name. The label of the answer is not needed, nor is it present.
	A listquery is a query for a list of e.g. band members.'''
	query="SELECT ?answerLabel WHERE { wd:"+bestent['id']+" wdt:"+bestprop['id']+" ?answer. ?answer rdfs:label ?answerLabel. FILTER(LANG(?answerLabel)='en') }"
	weirdquery="SELECT ?date WHERE { wd:"+bestent['id']+" wdt:"+bestprop['id']+" ?date. }"
	listquery="SELECT DISTINCT ?answerLabel WHERE {wd:"+bestent['id']+" p:P527 ?statement. ?statement ps:P527 ?answer. ?answer rdfs:label ?answerLabel. FILTER(LANG(?answerLabel)='en') }"
	
	#check if answer is text or numeric. If it is a "weirdquery" or "listquery", use the respective appropriate queries.
	data = requests.get(url,params={'query': query, 'format': 'json'}).json()
	if not data['results']['bindings']:
		weirddata = requests.get(url,params={'query': weirdquery, 'format': 'json'}).json()
		if not weirddata['results']['bindings']:
			listdata = requests.get(url,params={'query': listquery, 'format': 'json'}).json()
			return listdata
		else:
			return weirddata
	else:
		return data
		
for line in sys.stdin:
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
					if (token.text == "members"):
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
	print(qprint)
