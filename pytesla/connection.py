import json
import urllib
from http.client import HTTPSConnection, HTTPException
from . import vehicle
import os

class Session:
    def __init__(self):
        self.open()

    def open(self):
        self._httpconn = HTTPSConnection('owner-api.teslamotors.com')

    def read_url(self, url, post_data = None):
        """
        Gets the url URL. Posts post_data.
        """

        headers = {}

        if 'access_token' in self.state:
            headers['Authorization'] = 'Bearer {}' \
                                       .format(str(self.state['access_token']))

        if post_data.__class__ == dict:
            post = urllib.parse.urlencode(post_data)
        else:
            post = post_data

        self._httpconn.request("GET" if post is None else "POST",
                               url, post, headers)
        response = self._httpconn.getresponse()

        if response.status == 401 and response.reason == "Unauthorized" \
           and 'access_token' in self.state:
            del self.state['access_token']

        if response.status != 200:
            raise HTTPException(response.status, response.reason)

        return response

    def read_json(self, url, post_data = None):
        f = self.read_url(url, post_data)
        data = f.read().decode('utf-8')
        f.close()
        return json.loads(data)

_STATE_PATH = os.path.expanduser("~/.tesla-session")

class Connection(Session):
    def __init__(self, email, passwd):
        Session.__init__(self)
        self.load_state()
        self._vehicles = {}

        self._email = email
        self._passwd = passwd

        if not 'access_token' in self.state:
            self.login()

        try:
            self.vehicles()
        except HTTPException as e:
            if e.args == (401, "Unauthorized"):
                self.login(True)

    def login(self, unauthorized = False):
        if unauthorized:
            self._httpconn.close()
            self.open()

        passwd = self._passwd
        if type(passwd) != str:
            # We were not given a password as a string, assuming it's
            # a function that'll return the password.
            passwd = self._passwd()

        cred = {}

        with open(os.path.expanduser("~/.pytesla"), "r") as f:
            cred = json.load(f)

        r = self.read_json('/oauth/token',
                           {'grant_type': 'password',
                            'client_id': cred['client_id'],
                            'client_secret': cred['client_secret'],
                            'email' : self._email,
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

    def vehicles(self, refresh = False):
        if refresh or not 'vehicles' in self.state:
            d = self.read_json_path('/api/1/vehicles')
            self.state['vehicles'] = d['response']
            self.save_state()

        for v in self.state['vehicles']:
            vin = v['vin']

            if vin in self._vehicles:
                self._vehicles[vin]._data = v
            else:
                self._vehicles[vin] = vehicle.Vehicle(vin, self, v)

        return self._vehicles
