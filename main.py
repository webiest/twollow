#!/usr/bin/env python

import wsgiref.handlers

from google.appengine.api import urlfetch 
from google.appengine.ext import webapp
import feedparser, base64, settings
from django.utils import simplejson

POST = urlfetch.POST
GET = urlfetch.GET

search_url = "http://search.twitter.com/search.atom?q=" + settings.search_string
followers_url = "http://twitter.com/followers/ids.json?screen_name=" + settings.twitter_username
friends_url = "http://twitter.com/friends/ids.json?screen_name=" + settings.twitter_username
friend_create_url = "http://twitter.com/friendships/create/%s.xml"
friend_destroy_url = "http://twitter.com/friendships/destroy/%s.xml"

base64string = base64.encodestring('%s:%s' % (
    settings.twitter_username, 
    settings.twitter_password))[:-1]
headers = {'Authorization': "Basic %s" % base64string} 

class MainHandler(webapp.RequestHandler):
    def get(self):
        ''' perform search and add friends '''
        result = urlfetch.fetch(search_url)
        print ""
        print "--result--"
        if result.status_code == 200:
            encoded = unicode(result.content, errors='ignore')
            feed = feedparser.parse(encoded)
            for entry in feed['entries']:
                result2 = request(POST, friend_create_url % entry['author'].split(" ")[0])
                print result2.content


class UnfollowHandler(webapp.RequestHandler):
    def get(self):
        ''' unfollow all who are not following back '''
        reload = None
        friends = simplejson.loads(request(GET, friends_url).content)
        followers = simplejson.loads(request(GET, followers_url).content)

        for friend in friends:
            if not friend in followers:
                response = request(POST, friend_destroy_url % friend)
                reload = True

        if reload:
            # this needs to be refined
            #urlfetch.fetch('/unfollow/')
            pass


def request(method, url):
    return urlfetch.fetch(url, payload=None, method=method, headers=headers)

def main():
  application = webapp.WSGIApplication(
    [('/', MainHandler),
     ('/unfollow/', UnfollowHandler)],
    debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
