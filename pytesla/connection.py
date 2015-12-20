import json
import urllib
import httplib
from vehicle import Vehicle
import os

class Session:
    def __init__(self):
        self.open()

    def open(self):
        self.conn = httplib.HTTPSConnection('owner-api.teslamotors.com')

    def read_url(self, url, post_data = None):
        """
        Gets the url URL. Posts post_data.
        """

        headers = {}

        if 'access_token' in self.state:
            headers['Authorization'] = 'Bearer {}' \
                                       .format(str(self.state['access_token']))

        if post_data.__class__ == dict:
            post = urllib.urlencode(post_data)
        else:
            post = post_data

        self.conn.request("GET" if post is None else "POST",
                          url, post, headers)
        response = self.conn.getresponse()

        if response.status == 401 and response.reason == "Unauthorized" \
           and 'access_token' in self.state:
            del self.state['access_token']

        if response.status != 200:
            raise httplib.HTTPException(response.status, response.reason)

        return response

    def read_json(self, url, post_data = None):
        f = self.read_url(url, post_data)
        data = f.read()
        f.close()
        return json.loads(data)

_STATE_PATH = os.path.expanduser("~/.tesla-session")

class Connection(Session):
    def __init__(self, email, passwd):
        Session.__init__(self)
        self.load_state()

        self.email = email
        self.passwd = passwd

        if not 'access_token' in self.state:
            self.login()

        try:
            self.vehicles()
        except httplib.HTTPException, e:
            if e.args == (401, "Unauthorized"):
                self.login(True)

    def login(self, unauthorized = False):
        if unauthorized:
            self.conn.close()
            self.open()

        passwd = self.passwd
        if type(passwd) != str:
            # We were not given a password as a string, assuming it's
            # a function that'll return the password.
            passwd = self.passwd()

        cred = {}

        with open(os.path.expanduser("~/.pytesla"), "r") as f:
            cred = json.load(f)

        r = self.read_json('/oauth/token',
                           {'grant_type': 'password',
                            'client_id': cred['client_id'],
                            'client_secret': cred['client_secret'],
                            'email' : self.email,
                            'password' : passwd })

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
        return Session.read_json(self, path, post_data)

    def vehicle(self, vin):
        return self.vehicles()[vin]

    def vehicles(self):
        if not 'vehicles' in self.state:
            d = self.read_json_path('/api/1/vehicles')
            self.state['vehicles'] = d['response']
            self.save_state()

        vehicles = {}
        for v in self.state['vehicles']:
            vehicles[v['vin']] = Vehicle(v['vin'], self, v)

        return vehicles
