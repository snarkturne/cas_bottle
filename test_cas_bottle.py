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
auth=CAS_bottle.CASAuth(cas_server="https://your.cas.server/cas", #<= Your CAS server
                        service_url="http://localhost:8080/login")
bottle.install(auth)
# Some callbacks require auth, some dont.
# use apply=[auth] as a @route parameter to force CAS authentification
# Any callback can get the username (None if user is not authentified)

@route(['/index','/'])
def index() :
    stri="""
    Index page
    <ul>
    <li> <a href='authornot'>You can access this page wether you are logged in or not</a></li>
    <li> <a href='authforced'>You must log in to access this page</a></<li>
    <li> <a href='login'>Log in (if you are not) and go back to index</a></li>
    <li> <a href='logout'>Log out</a></li>
    </ul>
    """
    return stri 

@route('/authornot') 
def authornot() :
    username=auth.username()
    stri="You accessed this page with login : {}.".format(username)
    if not username : stri+=" Anonymous access"
    return stri

@route('/authforced') 
def authforced() :
    username=auth.username()
    stri="You accessed this page with login : {}.".format(username)
    return stri


@route('/logout')
def logout() :
    auth.logout()
    return ""

@route('/login')
def login() :
    bottle.redirect('/index')

bottle.run(app, host='localhost', port=8080,debug= True, reloader=True)
