# -*- coding: utf-8 -*-
from google.appengine.api import urlfetch

import uuid
import urllib

class OAuth2():
    def get_authorization(self,appid,req_url,redirect_uri):
        req_const = dict(response_type='code',\
                         client_id=appid,\
                         redirect_uri=redirect_uri,\
                         state=uuid.uuid4().hex)
        const = urllib.urlencode(req_const)
        return str(req_url+'?'+const)
    def get_access(self,appid,appkey,method,code,acc_url,redirect_uri):
        acc_const = dict(grant_type='authorization_code',\
                         client_id=appid,\
                         client_secret=appkey,\
                         code=code,\
                         state=uuid.uuid4().hex,\
                         redirect_uri=redirect_uri)
        const = urllib.urlencode(acc_const)
        acc_url = acc_url+'?'
        try:
            if method == 'GET':               
                return urlfetch.fetch(acc_url+const).content
            if method == 'POST':
                return urlfetch.fetch(url=acc_url,
                                      payload= const,
                                      method=urlfetch.POST,
                                      headers={'Content-Type':'application/x-www-form-urlencoded'}).content
        except urlfetch.Error:
            return acc_url
