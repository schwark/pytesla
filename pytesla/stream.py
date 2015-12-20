import urllib.request
import base64

#import http.client
#http.client.HTTPConnection.debuglevel = 1

class StreamEvents:
    SPEED            = 'speed'
    ODOMETER         = 'odometer'
    STATE_OF_CHARGE  = 'soc'
    ELEVATION        = 'elevation'
    HEADING          = 'est_heading'
    LATITUDE         = 'est_lat'
    LONGITUDE        = 'est_lng'
    POWER            = 'power'
    SHIFT_STATE      = 'shift_state'
    ALL              = 'speed,odometer,soc,elevation,est_heading,est_lat,est_lng,power,shift_state'

class Stream:
    def __init__(self, vehicle, events):
        self._vehicle = vehicle
        self._request = None
        self._response = None
        self._events = events

    def __repr__(self):
        return "<Stream {}>".format(str(self._vehicle))

    def connect(self):
        n = 0

        while (n < 2):
            n += 1

            token = self._vehicle.stream_auth_token
            auth_str = "{}:{}".format(self._vehicle.email, token)
            auth = base64.b64encode(bytes(auth_str, 'utf-8')).decode('utf-8')
            params = "?values=" + ','.join(self._events)

            url ='https://streaming.vn.teslamotors.com/stream/{}/{}' \
                .format(self._vehicle.vehicle_id, params)
            headers = {'Authorization': 'Basic {}'.format(auth)}

            self._request = urllib.request.Request(url, headers = headers)

            try:
                response = urllib.request.urlopen(self._request)
            except urllib.error.HTTPError as e:
                if e.code == 401 and e.reason == "provide valid authentication":
                    self._vehicle.refresh()

                    continue

                raise e

            return response

    def close(self):
        self._request = None

    def events(self, count = 0):
        with self.connect() as response:
            n = 0
            for line in response:
                yield (line.decode('utf-8').strip().split(','), self)

                n += 1

                if count != 0 and n >= count:
                    break

                if not self._request:
                    break
