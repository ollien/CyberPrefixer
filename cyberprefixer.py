# Copyright (c) 2013 Molly White
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import HTMLParser
import re
import tweepy
import urllib2
from secrets import *
from bs4 import BeautifulSoup
from topia.termextract import tag
from time import gmtime, strftime

tagger = tag.Tagger()
tagger.initialize()
hparser = HTMLParser.HTMLParser()

offensive = re.compile(r"\b(deaths?|dead(ly)?|dies?|hurts?|injur(e|i?es|ed|y)|"
                       r"kill(ing|ed|er|s)?|fatal(ly|ity)?|shoo?t(s|ing|er)?|"
                       r"crash(es|ed|ing)?|murder(s|er|ed|ing)?|hostages?|"
                       r"pile-?ups?)\b", flags=re.IGNORECASE)

def get():
    try:
        request = urllib2.Request(
            "http://news.google.com/news?pz=1&cf=all&ned=us&hl=en&output=rss")
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        print e.reason
    else:
        html = BeautifulSoup(response.read())
        items = html.find_all('item')
        for item in items:
            headline = item.title.string
            h_split = headline.split()

            # We don't want to use incomplete headlines
            if "..." in headline:
                continue

            # Try to weed out all-caps headlines
            if count_caps(h_split) >= len(h_split) - 3:
                continue

            # Skip anything too offensive
            if not tact(headline):
                continue

            # Remove attribution string
            if "-" in headline:
                headline = headline.split("-")[:-1]
                headline = ' '.join(headline).strip()

            if process(headline):
                break
            else:
                continue

def process(headline):
    headline = hparser.unescape(headline)
    tagged = tagger(headline)
    for i, word in enumerate(tagged):
        # Avoid having two "cybers" in a row
        if is_replaceable(word) and not is_replaceable(tagged[i-1]):
            headline = headline.replace(" " + word[0], " cyber" + word[0], 1)

    # Don't tweet anything that's too long
    if len(headline) > 140:
        return False

    # Don't tweet anything where a replacement hasn't been made
    if "cyber" not in headline:
        return False
    else:
        return tweet(headline)

def tweet(headline):
    auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
    auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
    api = tweepy.API(auth)
    tweets = api.user_timeline('CyberPrefixer')

    # Check that we haven't tweeted this before
    for tweet in tweets:
        if headline == tweet.text:
            return False

    # Log tweet to file
    f = open("cyberprefixer.log", 'a')
    t = strftime("%d %b %Y %H:%M:%S", gmtime())
    f.write("\n" + t + " " + headline)
    f.close()

    # Post tweet
    api.update_status(headline)
    return True

def tact(headline):
    # Avoid producing particularly tactless tweets
    if re.search(offensive, headline) is None:
        return True
    else:
        return False

def count_caps(headline):
    count = 0
    for word in headline:
        if word[0].isupper():
            count += 1
    return count

def is_replaceable(word):
    # Prefix any noun (singular or plural) that begins with a lowercase letter
    if (word[1] == 'NN' or word[1] == 'NNS') and word[0][0].isalpha \
        and word[0][0].islower():
        return True
    else:
        return False

if __name__ == "__main__":
    get()
