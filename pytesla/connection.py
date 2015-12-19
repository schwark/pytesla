import json
import urllib2
import urllib
from vehicle import Vehicle
import os

class Session:
    def __init__(self):
        pass

    def read_url(self, url, post_data = None):
        """
        Gets the url URL. Posts post_data.
        """
        req = urllib2.build_opener()

        if 'access_token' in self.state:
            req.addheaders = [('Authorization',
                               'Bearer ' + str(self.state['access_token']))]

        if post_data.__class__ == dict:
            post = urllib.urlencode(post_data)
        else:
            post = post_data
        f = None
        try:
            f = req.open(self._encode(url), data=post)
        except urllib2.HTTPError, e:
            if e.code == 401 and e.reason == "Unauthorized" \
               and 'access_token' in self.state:
                del self.state['access_token']

            raise e

        return f

    def read_json(self, url, post_data = None):
        f = self.read_url( url, post_data )
        data = f.read()
        f.close()
        return json.loads( data )

    def _encode(self, value):
        if isinstance(value, unicode):
            value = value.encode("utf-8")
        return value

_ENDPOINT = 'https://owner-api.teslamotors.com/'
_STATE_PATH = os.path.expanduser("~/.tesla-session")

class Connection(Session):
    def __init__(self, email, passwd):
        Session.__init__(self)
        self.load_state()

        self.email = email
        self.passwd = passwd

        if not 'access_token' in self.state:
            self.login()

    def login(self):
        cred = {}

        with open(os.path.expanduser("~/.pytesla"), "r") as f:
            cred = json.load(f)

        r = self.read_json(_ENDPOINT + 'oauth/token',
                           {'grant_type': 'password',
                            'client_id': cred['client_id'],
                            'client_secret': cred['client_secret'],
                            'email' : self.email,
                            'password' : self.passwd } )

        if 'access_token' in r:
            self.state['access_token'] = r['access_token']

            self.save_state()

    def load_state(self):
        self.state = {}
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH, "r") as f:
                self.state = json.load(f)

    def save_state(self):
        with open(_STATE_PATH, 'w') as f:
            json.dump(self.state, f, indent=4)

    def read_json_path(self, path, post_data = None):
        return Session.read_json(self, _ENDPOINT + path, post_data)

    def vehicle(self, vin):
        return Vehicle(vin, self)

    def vehicles(self):
        payload = self.read_json_path('vehicles')
        v = []
        for p in payload:
            v.append( Vehicle( p['vin'], self, p) )
        return v
