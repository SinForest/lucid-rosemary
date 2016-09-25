#!/usr/bin/python3

from twython import Twython
import records
import sys, re

APP_KEY = 'v973Pwa2v9xTsr2SPIcK4MZkR'
APP_SECRET = 'wBMBFYM3NDRuSMMfeZr07ZnhhMQDsz5a1PD0NS0V0pjNLuR0VQ'
ACC_KEY = '735813797349326848-Mc5l8W6hPt16j1gUHlB3hEPZF7Hlm0e'
ACC_SECRET = 'ep2bvx2jtnOdxnkAosSC3P3ZRAINeiEYc5CnEd1nStlXC'

def initialize():
	global twitter
	twitter = Twython(APP_KEY, APP_SECRET, ACC_KEY, ACC_SECRET)
	global db
	db = records.Database('postgres://localhost/test?user=user&password=p4ssw9rd')
	global emoji_rx
	emoji_rx = re.compile("["
		"\U0001F600-\U0001F64F"  # emoticons
		"\U0001F300-\U0001F5FF"  # symbols & pictographs
		"\U0001F680-\U0001F6FF"  # transport & map symbols
		"\U0001F1E0-\U0001F1FF"  # flags (iOS)
		"]+", flags=re.UNICODE)

def divide_tweet(status):
	tweet = status["text"]
	#clear from RT annotations
	match = re.match("RT @[A-Za-z_]*: (.*)", tweet)
	if match:
		tweet = match.group(1)
	#TODO: URL-Killing via API
	try:
		urls = status["entities"]["urls"]
	except:
		urls = []
	for url in urls:
		#print("Orig: " + tweet)
		crop_url = url["url"]
		tweet = tweet.replace(crop_url, "")
		#print("New: " + tweet)

	return #!! code below broken

	#remove hashtags in the end and # from other hashtags
	#remove emoji
	last_words = True
	for i in reversed(range(0,len(tweet))):
		emoji_rx.sub("", tweet[i]) #kill emoji
		if tweet[i][0] == '#': #word is hashtag
			if last_words: #hashtag is in the end of tweet
				tweet.pop(i) #remove hashtag
				continue
			else:
				tweet[i] = tweet[i][1:] #remove '#' from hashtag
		else:
			last_words = False

	#TODO: NaturalLanguage Tweet-Tokenize

	return tweet


def long_search(query, count, func): #search-wrapper for multiple searches
	max_id = None
	for i in range(0,count): #sucht manchmal noch mehrmals bis zur selben ID
		if max_id == None:
			search_results = twitter.search(q=query, count=100)
		else:
			search_results = twitter.search(q=query, count=100, max_id=max_id)
		func(search_results)
		print("=" * 100)
		if not search_results["statuses"]:
			break
		max_id = str(search_results["statuses"][-1]["id"] - 1)

#-----------PROCESSING-FUNCTIONS-------------------------

#processing-function for long_search; writes valid hashtags in database
def collect_hashtags(input):
	for status in input["statuses"]:
		for hashtag in status["entities"]["hashtags"]:
			hashtag = hashtag["text"].lower()
			if len(hashtag) > 14:
				continue
			is_valid = True
			for char in hashtag:
				if char not in "abcdefghijklmnopqrstuvwxyz1234567890_":
					is_valid = False
					break
			if is_valid:
				print(hashtag.ljust(15) + "|")
				db.query("INSERT INTO hashtags (hashtag) SELECT '{0}' WHERE NOT EXISTS (SELECT * FROM hashtags WHERE hashtag = '{0}')".format(hashtag))

#processing-function for long_search;
def collect_tweets(input):
	for status in input["statuses"]:
		#print(status["id_str"] + ": " + status["text"])
		divide_tweet(status) #!! testing divide_tweet()

#--------------QUERYS-----------------------------

#called from main, when argument "tweets" is given
def query_hashtags():
	result = db.query("SELECT word FROM words ORDER BY random() LIMIT 3")
	search_query = " OR ".join(map(lambda x: x.word,result)) + " lang:en"
	long_search(search_query, 10, collect_hashtags)

#called from main, when argument "tweets" is given
def query_tweets():
	result = db.query("SELECT hashtag FROM hashtags ORDER BY random() LIMIT 1")
	print(result[0].hashtag)
	long_search("#" + result[0].hashtag, 10, collect_tweets)

#--------------MAIN-----------------------------

#main-function: called on startup
def main():
	if len(sys.argv) < 2:
		print("error: no arguments given")
		print("try 'hashtags' or 'tweets'")
		exit()
	initialize()
	if sys.argv[1] == "hashtags":
		query_hashtags()
	elif sys.argv[1] == "tweets":
		query_tweets()
	else:
		print("error: wrong argument")
		print("try 'hashtags' or 'tweets'")


main()
