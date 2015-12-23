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
    def __init__(self, vehicle):
        self._vehicle = vehicle
        self._request = None

    def __repr__(self):
        return "<Stream {}>".format(str(self._vehicle))

    def connect(self, events):
        n = 0

        while (n < 2):
            n += 1

            token = self._vehicle.stream_auth_token
            auth_str = "{}:{}".format(self._vehicle.email, token)
            auth = base64.b64encode(bytes(auth_str, 'utf-8')).decode('utf-8')
            params = "?values=" + ','.join(events)

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

    def read_stream(self, events, count):
        total = 0
        iter_count = 0

        while True:
            n = 0

            iter_count += 1

            with self.connect(events) as response:
                for line in response:
                    yield (line.decode('utf-8').strip().split(','), self)

                    n += 1
                    total += 1

                    if count != 0 and total >= count or not self._request:
                        break

            # If we were closed, stop
            if not self._request:
                break

            # If the car isn't being driven the streaming server just
            # sends one event and then times out. In that case, stop.
            if n <= 1:
                break

            # If we got as many or more events than we asked for, stop.
            if count != 0 and total >= count:
                break
