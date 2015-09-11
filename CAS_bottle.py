"""
CAS module for bottle 

History : 
   Original module for Cherrypy developped by : James Macdonell and Marc Santoro 
   Bottle Adaptation : SnarkTurne

2013-08-27 : Typos corrections, bug correction in the  TestCASAuth method   
2013-07-16 : Converted to a real bottle plugin
2013-07-08 : Added redirection to the requested URL (steps 1 & 2 in CASAuth)
2013-07-03 : Bottle decorator 
2013-07-02 : Adaptation for bottle (Author Snarkturne) 


This module needs beaker (session).

Try this : 

import bottle
from bottle import route
import CAS_bottle
from beaker.middleware import SessionMiddleware

# Enable beaker sessions 
session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 300,
    'session.auto': True
}
app = SessionMiddleware(bottle.app(), session_opts)

# Create the plugin
auth=CAS_bottle.CASAuth(cas_server="https://your.cas.sever", #<= Your CAS server
                        service_url="http://localhost:8080/login")

# Some callbacks require auth, some dont.
# use apply=[auth] as a @route parameter to force CAS authentification
# Any callback can get the username (None if user is not authentified)

@route(['/index','/'])
def index() :
    stri='''
    Index page
    <ul>
    <li> <a href='authornot'>You can access this page wether you are logged in or not</a></li>
    <li> <a href='authforced'>You must log in to access this page</a></<li>
    <li> <a href='login'>Log in (if you are not) and go back to index</a></li>
    <li> <a href='logout'>Log out</a></li>
    </ul>
    '''
    return stri 

@route('/authornot') 
def authornot() :
    username=auth.username()
    stri="You accessed this page with login : {}.".format(username)
    if not username : stri+=" Anonymous access"
    return stri

@route('/authforced',apply=[auth]) 
def authforced() :
    username=auth.username()
    stri="You accessed this page with login : {}.".format(username)
    return stri


@route('/logout')
def logout() :
    auth.logout()
    return ""

@route('/login',apply=[auth])
def login() :
    bottle.redirect('/index')

bottle.run(app, host='localhost', port=8080,debug= True, reloader=True)


If you just want to use CAS authentification for all pages :
    
auth=CAS_bottle.CASAuth(cas_server="https://your.cas.sever", #<= Your CAS server
                        service_url="http://localhost:8080/login")
bottle.install(auth)

... and you don't need apply=[auth] anymore

Debug mode :
CAS_bottle.debug=True # You will get hints about what's happening on stdout
"""
import bottle
import urllib.request
import xml.etree.ElementTree
from functools import wraps

debug=False
version=1.1

class CASAuth :
    api=2
    name="casauth"
    
    def __init__(self,cas_server,service_url):
        """
        CAS server (typically : cas)
        Service URL of your app (typically : http://myapp/login)
        """ 
        self.cas_server=cas_server
        self.service_url=service_url
        self.testusername=None
    
    def test_with_username(self,username) :
        """ 
        No more CAS Auth. 
        Instead, user is authenticated as : username
        Only use this to test and debug your app
        Call test_with_username(None) to use CAS again
        """
        self.testusername=username
    
    def apply(self,callback,context) :
        """ apply method, Bottle api V2 """
        
        def decorated(*args, **kwargs) : 
            if self.testusername : _TestCASAuth(self.testusername)
            else : _CASAuth(self.cas_server,self.service_url)
            return callback(*args, **kwargs)
        return decorated
        
    def logout(self) :
        """ Call this to log out """
        _CASLogout(self.cas_server,self.service_url)

    def username(self) :
        """ Call this to get the logged user of None if user is not
        authentified
        """
        session = _getsession()
        return session.get("user",None)
    
         
def _pdebug(*kwargs) :
    if debug : print("== CAS ==>",*kwargs)
    
def _getsession() :
    session=bottle.request.environ.get('beaker.session',None)
    if not session : 
        raise  ValueError("No beaker session ? This plugin need beaker session middleware (read the doc)")
    return session

def _TestCASAuth(user) :
    session=_getsession()
    if session.get('user'):
        _pdebug("Test User session",session.get('user'))
        session['validated_by'] = "session attribute"
    else :
        _pdebug("Test User",user)
        session['user'] = user 
    session.save()

    
def _CASLogout(cas_server,service_url):
    session=_getsession()
    cas_logout=cas_server + "/cas/logout?service=" + service_url
    _pdebug("Cas Logout : ",cas_logout,"user=",session.get('user',None))
    session['user']=None
    session.save()
    session.delete()
    bottle.redirect(cas_logout)

def _CASAuth(cas_server,service_url):
    session=_getsession()
    _pdebug(cas_server,service_url)
    _pdebug(bottle.request.params) 
    if session.get('user'):
        # Step 3 : user has been validated
        _pdebug("User session",session.get('user'))
        session['validated_by'] = "session attribute"
        session.save()
    elif 'ticket' in bottle.request.params: 
        # Step 2 : A ticket has been recevived. We have to validate it.
        ticket = bottle.request.params["ticket"]
        _pdebug("Ticket",ticket)
        #generate URL for ticket validation 
        cas_validate = cas_server + "/cas/serviceValidate?ticket=" + ticket + "&service=" + service_url
        _pdebug("Opening : ",cas_validate)
        f_xml_assertion = urllib.request.urlopen(cas_validate)
        if not f_xml_assertion:
            bottle.abort(401, 'Unable to authenticate: trouble retrieving assertion from CAS to validate ticket.')

        #parse CAS XML assertion into a ElementTree
        assertion_tree = xml.etree.ElementTree.parse(f_xml_assertion)
        if not assertion_tree:
            bottle.abort(401, 'Unable to authenticate: trouble parsing XML assertion.')

        user_name=None
        #find <cas:user> in ElementTree
        for e in assertion_tree.iter():
            if e.tag != "{http://www.yale.edu/tp/cas}user":
                continue
            user_name = e.text
        if not user_name:
            #couldn't find <cas:user> in the tree
            bottle.abort(401, 'Unable to validate ticket: could not locate cas:user element.')
    
        #add username to session
        session['user'] = user_name
        session.save()
        _pdebug("Authentificated as: ",user_name)
        #DEBUG: user is validated by initial ticket instance
        session['validated_by'] = "ticket"

        # Redirection to the requested page (cf step 1)
        if 'redirect_url' in session :
            bottle.redirect(session['redirect_url'])
        else :
            bottle.redirect(service_url)
    else:
        #no existing session; no ticket to validate
        #redirect to CAS to retrieve new ticket
        # Step 1 : Go to the login page
        _pdebug("Ask CAS")
        # Save the requested url (used in step 2). First case allows
        # to control redirection from your page's code. 
        if "redirect_url" in bottle.request.params :
            session["redirect_url"]=bottle.request.params["redirect_url"]
        else :
            session["redirect_url"]=bottle.request.url
        session.save()
        bottle.redirect(cas_server + "/cas/login?service=" + service_url)
        
