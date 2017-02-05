import json

try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

try:
    from http.client import HTTPSConnection, HTTPException
except ImportError:
    from httplib import HTTPSConnection, HTTPException

from . import vehicle
import os

class NoOpLogger:
    def write(self, str):
        pass
    def debug(self, str):
        pass

class Session:
    def __init__(self, log):
        if log == None:
            log = NoOpLogger()

        self._log = log
        self._in_reauthorization_attempt = False
        self._is_open = False

    def open(self):
        self._httpconn = HTTPSConnection('owner-api.teslamotors.com')
        self._httpconn.set_debuglevel(5)

        self._is_open = True

    def close(self):
        if self._is_open:
            self._httpconn.close()

            self._is_open = False

    def request(self, path, post_data = None):
        """
        Send a request for the path 'path'. Does a POST of post_data if given,
        else a GET of the given path.
        """

        if not self._is_open:
            self.open()

        headers = {}

        if 'access_token' in self.state:
            headers['Authorization'] = 'Bearer {}' \
                                       .format(str(self.state['access_token']))

        if type(post_data) == dict:
            post = urlencode(post_data)
        else:
            post = post_data

        self._httpconn.request("GET" if post is None else "POST",
                               path, post, headers)
        response = self._httpconn.getresponse()

        if response.status != 200:
            # Make sure we read the response body, or we won't be able to
            # re-use the connection for following request.
            response.read()

            if response.status == 401 and response.reason == "Unauthorized":
                if 'access_token' in self.state:
                    del self.state['access_token']
                    self.save_state()

                if not self._in_reauthorization_attempt:
                    ok = False

                    try:
                        self._in_reauthorization_attempt = True
                        ok = self.login(True)

                        if not ok:
                            raise Exception("Authorization failed.")

                        # Authentication successfull, return the request
                        return self.request(path, post_data)
                    except Exception as e:
                        self._log.write("Re-authorization failed: {}" \
                                        .format(str(e)))

                        raise e
                    finally:
                        self._in_reauthorization_attempt = False

            self._log.write("{} request failed: {}: {}" \
                            .format(path, response.status, response.reason))

            raise HTTPException(response.status, response.reason)

        return response


    def read_json(self, path, post_data = None):
        r = self.request(path, post_data)
        return json.loads(r.read().decode('utf-8'))

class Connection(Session):
    def __init__(self, email, passwd, log = None, temp_prefix = "./"):
        Session.__init__(self, log)

        self._temp_prefix = temp_prefix
        self._state_path = os.path.expanduser(self._temp_prefix+"tesla-session")

        self.load_state()
        self._vehicles = {}

        self._email = email
        self._passwd = passwd

        if 'access_token' not in self.state:
            self.login()

    def login(self, unauthorized = False):
        if unauthorized:
            self.close()
            self.open()

        passwd = self._passwd
        if type(passwd) != str:
            # We were not given a password as a string, assuming it's
            # a function that'll return the password.
            passwd = self._passwd()

        cred = {}

        with open(os.path.expanduser(self._temp_prefix+"tesla-creds"), "r") as f:
            cred = json.load(f)

        r = {}
        try:
            r = self.read_json('/oauth/token',
                               {'grant_type': 'password',
                                'client_id': cred['client_id'],
                                'client_secret': cred['client_secret'],
                                'email' : self._email,
                                'password' : passwd })
        except Exception as e:
            self._log.write("Authorization failed: {}".format(str(e)))

        if 'access_token' not in r:
            return False

        self.state['access_token'] = r['access_token']
        self.save_state()

        return True

    def load_state(self):
        self.state = {}
        if os.path.exists(self._state_path):
            with open(self._state_path, "r") as f:
                self.state = json.load(f)

    def save_state(self):
        with open(self._state_path, 'w') as f:
            json.dump(self.state, f, indent=4)

    def vehicle(self, vin):
        return self.vehicles()[vin]

    def vehicles(self, refresh = False):
        if refresh or 'vehicles' not in self.state:
            d = self.read_json('/api/1/vehicles')
            self.state['vehicles'] = d['response']
            self.save_state()

        for v in self.state['vehicles']:
            vin = v['vin']

            if vin in self._vehicles:
                self._vehicles[vin]._data = v
            else:
                self._vehicles[vin] = vehicle.Vehicle(vin, self, v, self._log)

        return self._vehicles
