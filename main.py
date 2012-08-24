# -*- coding: utf-8 -*-
from xml.dom.minidom import parseString
from google.appengine.api import urlfetch
from google.appengine.ext import db
from xml.parsers.expat import ExpatError

from oauth2 import *

import os
import jinja2
import urllib
import urlparse
import json
import webapp2

site = {'douban':{'appID':   '',
                  'appKey':  '',
                  'code_url':'https://www.douban.com/service/auth2/auth',
                  'acc_url': 'https://www.douban.com/service/auth2/token',
                  'acc_method':'POST',
                  'me_url':  'https://api.douban.com/people/%40me'},
        'weibo': {'appID':'',
                  'appKey':'',
                  'code_url':'https://api.weibo.com/oauth2/authorize',
                  'acc_url':'https://api.weibo.com/oauth2/access_token',
                  'acc_method':'POST',
                  'me_url':'https://api.weibo.com/2/users/show.json'},
        'qq':    {'appID':'',
                  'appKey':'',
                  'code_url':'https://graph.qq.com/oauth2.0/authorize',
                  'acc_url':'https://graph.qq.com/oauth2.0/token',
                  'acc_method':'GET',
                  'me_url':'https://graph.qq.com/user/get_user_info'}}

HOST_ADDR = "http://www.example.com"
rootpath = os.path.dirname(__file__)
jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(rootpath))

class get_authorization(webapp2.RequestHandler):
    def get(self,typ):
        if typ in site.keys():
            redirect_uri = HOST_ADDR+'/getinfo/'+typ
            url = OAuth2().get_authorization(site[typ]['appID'],site[typ]['code_url'],redirect_uri)
            self.redirect(url)
class get_access(webapp2.RequestHandler):
    def get(self,typ):

        access_token = ''
        uid = 0

        if typ in site.keys():
            code = self.request.get('code')
            data = OAuth2().get_access(site[typ]['appID'], site[typ]['appKey'],
                                       site[typ]['acc_method'],code,
                                       site[typ]['acc_url'],HOST_ADDR+'/getinfo/'+typ)
            if typ == 'douban':
                """redirect_uri?error=denied"""
                error = self.request.get('error')
                if code == '' and error :
                    self.response.write(error)
                    return                
                """{"access_token":"","douban_user_id":"","expires_in":}"""
                json_obj = json.loads(data)                    
                if json_obj.has_key('access_token'):
                    access_token = json_obj['access_token']
                    uid = json_obj['douban_user_id']
                else:
                    """{"code":,"msg":"","request":""}"""
                    self.response.write(json_obj['msg'])
                    return
            if typ == 'qq':
                """code=&msg="""
                msg = self.request.get('msg')
                if code == '' and msg :
                    self.response.write(msg)
                    return                
                """access_token=&expires_in="""
                params = urlparse.parse_qs(data,True)
                if 'access_token' in params.keys():
                    access_token = params['access_token'][0]
                    #QQ return the access_token ,expire_in but it didn't contain openid
                    #the openid need request it separately
                    try:
                        req_url = 'https://graph.qq.com/oauth2.0/me?access_token='+access_token
                        """callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} );"""
                        content = urlfetch.fetch(req_url).content
                        json_obj = content.split(' ')[1]
                        uid = json.loads(json_obj)['openid']                        
                    except urlfetch.Error:
                        self.response.write('urlfetch.Error')
                        return 
                    except ValueError:
                        self.response.write('ValueError')
                        return 
            if typ == 'weibo':
                """redirect_uri?error_uri=&error=&error_description=&error_code="""
                error_description = self.request.get('error_description')
                if error_description and code == '':
                    self.response.write(error_description)
                    return

                """{"access_token": "", "expires_in":,"remind_in":"","uid":""}"""
                json_obj = json.loads(data)
                if json_obj.has_key('access_token'):
                    access_token = json_obj['access_token']
                    uid = json_obj['uid']
                else:
                    """{"error":"","error_code":,"error_description":""}"""
                    self.response.write(json_obj['error_description'])
                    return
            if (not check_exist_user(typ,access_token,uid)):
                #access_token save to Token Table and return the record ID
                Token(xid=uid,
                      xaccToken=access_token,
                      xorigin=typ).put()
                self.response.write("Come on~")
                return
        else:
            self.response.write('URL error')
            return
	
def check_exist_user(typ,access_token,uid):
    #exit the user and update the access_token
    tokens = db.GqlQuery("SELECT * FROM Token WHERE xid=:1 and xorigin=:2",uid,typ)
    token = tokens.get()
    if token != None:
        token.xaccToken = access_token
        token.put()
        return True
    return False
class Token(db.Model):
    xid = db.StringProperty(default='')
    xorigin = db.StringProperty(default='site')
    xaccToken = db.StringProperty(default='')
class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('view/index.html')
        self.response.write(template.render({}))

app = webapp2.WSGIApplication([('/', MainHandler),
                               ('/login/(.*)',get_authorization),
                               ('/getinfo/(.*)',get_access)],
                              debug=True)
