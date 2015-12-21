from . import stream

class CommandError(Exception):
    """Tesla Model S vehicle command returned failure"""
    pass

class Vehicle:
    def __init__(self, vin, conn, payload):
        assert payload['vin'] == vin

        self._conn = conn
        self._data = payload

    def __repr__(self):
        return "<Vehicle {}>".format(self.vin)

    # Helpers
    @property
    def vin(self):
        return self._data['vin']

    @property
    def id(self):
        return self._data['id']

    @property
    def vehicle_id(self):
        return self._data['vehicle_id']

    @property
    def state(self):
        return self._data['state']

    @property
    def email(self):
        return self._conn._email

    @property
    def stream_auth_token(self):
        return self._data['tokens'][0]

    # Stream entry generator for events defined in StreamEvents
    # (events should be an array of StreamEvents). This generator
    # generates tuples of an array of the requested events (preceded
    # by a timestamp) and a reference to the stream itself (which can
    # be closed to stop receiving events). This generator will
    # generate count number of events, or as many as it gets if count
    # is 0.
    def stream(self, events, count = 0):
        s = stream.Stream(self)
        return s.read_stream(events, count)

    def refresh(self):
        self._conn.vehicles(True)

    def _request(self, verb, command = False, **kwargs):
        action = 'data_request'
        post_data = None
        if command:
            action = 'command'
            post_data = kwargs
        elif kwargs:
            raise Exception("kwargs given for non-command request.")

        p = self._conn.read_json_path('/api/1/vehicles/{}/{}/{}' \
                                      .format(self.id, action, verb),
                                      post_data)
        if command and not p['response']:
            # Command returned failure, raise exception
            raise CommandError(p['error'])

        return p

    # API getter properties
    @property
    def mobile_enabled(self):
        return self._conn.read_json_path('/api/1/vehicles/{}/mobile_enabled' \
                                         .format(self.id))['response']

    @property
    def charge_state(self):
        return self._request('charge_state')['response']

    @property
    def climate_state(self):
        return self._request('climate_state')['response']

    @property
    def drive_state(self):
        return self._request('drive_state')['response']

    @property
    def gui_settings(self):
        return self._request('gui_settings')['response']

    @property
    def vehicle_state(self):
        return self._request('vehicle_state')['response']

    # API commands
    def door_lock(self):
        return self._request('door_lock', command = True)

    def door_unlock(self):
        return self._request('door_unlock', command = True)

    def charge_port_door_open(self):
        return self._request('charge_port_door_open', command = True)

    def charge_standard(self):
        return self._request('charge_standard', command = True)

    def charge_max_range(self):
        return self._request('charge_max_range', command = True)

    def charge_start(self):
        return self._request('charge_start', command = True)

    def charge_stop(self):
        return self._request('charge_stop', command = True)

    def set_charge_limit(self, limit):
        return self._request('set_charge_limit', command = True,
                             percent = limit)

    def flash_lights(self):
        return self._request('flash_lights', command = True)

    def honk_horn(self):
        return self._request('honk_horn', command = True)

    def set_temps(self, driver, passenger):
        return self._request('set_temps', command = True, driver_temp = driver,
                             passenger_temp = passenger)

    def auto_conditioning_start(self):
        return self._request('auto_conditioning_start', command = True)

    def auto_conditioning_stop(self):
        return self._request('auto_conditioning_stop', command = True)

    def sun_roof_control(self, state, percent = None):
        if state == 'move' and percent:
            return self._request('sun_roof_control', command = True,
                                 state = state, percent = percent)

        if state in ('open', 'close', 'comfort', 'vent'):
            return self._request('sun_roof_control', command = True,
                                 state = state)

        raise ValueError("Invalid sunroof state")

    def wake_up(self):
        d = self._conn.read_json_path('/api/1/vehicles/{}/wake_up' \
                                      .format(self.id), {})['response']

        # Update vehicle tokens if they're different from our cached
        # ones.
        tokens = d['tokens']

        if tokens != self._data['tokens']:
            self._data['tokens'] = tokens
            self._conn.save_state()

        return d
