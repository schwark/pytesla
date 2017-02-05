try:
    from urllib.parse import urlparse, urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urlparse import urlparse
    from urllib import urlencode
    from urllib2 import urlopen, Request, HTTPError

import contextlib
import base64

#import http.client
#http.client.HTTPConnection.debuglevel = 1

class StreamEvents:
    SPEED            = 'speed'         # int, or str if shift_state is ''
    ODOMETER         = 'odometer'      # float
    STATE_OF_CHARGE  = 'soc'           # int
    ELEVATION        = 'elevation'     # int
    HEADING          = 'est_heading'   # int
    LATITUDE         = 'est_lat'       # float
    LONGITUDE        = 'est_lng'       # float
    POWER            = 'power'         # int
    SHIFT_STATE      = 'shift_state'   # str
    ALL              = ['speed', 'odometer', 'soc', 'elevation',
                        'est_heading', 'est_lat', 'est_lng', 'power',
                        'shift_state']

class Stream:
    def __init__(self, vehicle):
        self._vehicle = vehicle
        self._request = None
        self._log = vehicle._log

    def __repr__(self):
        return "<Stream {}>".format(str(self._vehicle))

    def connect(self, events):
        self._log.debug("Stream connect")
        n = 0

        while (n < 2):
            n += 1

            self._log.debug("Stream connect iteration {}".format(n))

            auth_str = "{}:{}".format(self._vehicle.email,
                                      self._vehicle.stream_auth_token)
            auth = base64.b64encode(bytes(auth_str, 'utf-8')).decode('utf-8')

            params = "?values=" + ','.join(events)

            url ='https://streaming.vn.teslamotors.com/stream/{}/{}' \
                .format(self._vehicle.vehicle_id, params)
            headers = {'Authorization': 'Basic ' + auth}

            self._request = Request(url, headers = headers)

            try:
                response = urlopen(self._request)

                if not response:
                    raise Exception("Connection failed, no response returned.")

                self._log.debug("Stream connection established")

                return response
            except HTTPError as e:
                if e.code == 401 and \
                   e.reason in ["provide valid authentication",
                                "Unauthorized"]:
                    self._log.debug("Authentication error, retrying")

                    # Refresh our vehicles list to ensure we have an
                    # up-to-date token.
                    self._vehicle.refresh()

                    continue

                raise e

        raise Exception("Stream connection failed.")

    def close(self):
        self._request = None

    def read_stream(self, events, count):
        self._log.debug("In read_stream(count = {})".format(count))
        total = 0
        iter_count = 0

        while True:
            n = 0

            iter_count += 1

            self._log.debug("In read_stream(), iteration {}".format(iter_count))

            with contextlib.closing(self.connect(events)) as response:
                self._log.debug("In read_stream(), connected")
                for line in response:
                    data = line.decode('utf-8').strip().split(',')
                    event = {'timestamp': data[0]}
                    for i in range(0, len(events)):
                        event[events[i]] = data[i + 1]

                    yield (event, self)

                    n += 1
                    total += 1

                    self._log.debug("In read_stream(), n = {}, total = {}" \
                                    .format(n, total))

                    if count != 0 and total >= count or not self._request:
                        self._log.debug("In read_stream(), inner break")
                        break

            # If we were closed, stop
            if not self._request:
                self._log.debug("In read_stream(), closed")
                break

            # If the car isn't being driven the streaming server just
            # sends one event and then times out. In that case, stop.
            if n <= 1:
                self._log.debug("In read_stream(), n <= 1")
                break

            # If we got as many or more events than we asked for, stop.
            if count != 0 and total >= count:
                self._log.debug("In read_stream(), done")
                break
