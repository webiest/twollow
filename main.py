#!/usr/bin/env python

from django.utils import simplejson
from google.appengine.api import urlfetch 
from google.appengine.ext import webapp
from google.appengine.ext import db

import base64, datetime, feedparser, settings, wsgiref.handlers

POST = urlfetch.POST
GET = urlfetch.GET

search_url = "http://search.twitter.com/search.atom?q=" + settings.search_string
followers_url = "http://twitter.com/followers/ids.json?screen_name=" + settings.twitter_username
friends_url = "http://twitter.com/statuses/friends.json?screen_name=" + settings.twitter_username 
friend_create_url = "http://twitter.com/friendships/create/%s.xml"
friend_destroy_url = "http://twitter.com/friendships/destroy/%s.xml"

base64string = base64.encodestring('%s:%s' % (
    settings.twitter_username, 
    settings.twitter_password))[:-1]
headers = {'Authorization': "Basic %s" % base64string} 

class Unfollower(db.Model):
  id = db.IntegerProperty()
  screen_name = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)


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
                screen_name = entry['author'].split(" ")[0]
                unfollowed = db.GqlQuery("SELECT * FROM Unfollower where screen_name='" + screen_name + "'")

                if not unfollowed.count():
                    result2 = request(POST, friend_create_url % screen_name)
                    print result2.content
                    #if result2.content.find("Could not follow user"):
                    #    do_unfollow()


class UnfollowHandler(webapp.RequestHandler):
    def get(self):
        ''' unfollow all who are not following back '''
        print "unfollowing un-mutuals"
        print do_unfollow()

         
def do_unfollow():
    friends = simplejson.loads(request(GET, friends_url).content)
    followers = simplejson.loads(request(GET, followers_url).content)

    deltaDays = datetime.timedelta(days = 5)
    endDate = datetime.datetime.now()
    expireDate = endDate - deltaDays

    for friend in friends:
        tweettime = datetime.datetime.strptime(friend['created_at'], "%a %b %d %H:%M:%S +0000 %Y")
        if expireDate > tweettime:
            if not friend in followers:
                unfollow_friend(friend)

def unfollow_friend(friend):
    response = request(POST, friend_destroy_url % friend['id'])
    unfollowed_user = Unfollower()
    unfollowed_user.id = friend['id']
    unfollowed_user.screen_name = friend['screen_name']
    result = unfollowed_user.put()
    return response

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
