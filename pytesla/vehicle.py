class CommandError(Exception):
    """Tesla Model S vehicle command returned failure"""
    pass

class Vehicle:
    def __init__(self, vin, conn, payload):
        self._conn = conn
        self._vin = vin
        self._id = None

        assert payload['vin'] == self.vin
        self._id = payload['id']
        self._options = payload['option_codes'].split(',')
        self._state = payload['state']
        self._color = payload['color']

    def __repr__(self):
        return "<Vehicle %s>" % self.vin

    # Helpers
    @property
    def vin(self):
        return self._vin

    @property
    def id(self):
        return self._id

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
        p = self._conn.read_json_path('/api/1/vehicles/{}/mobile_enabled' \
                                      .format(self.id))
        return p['response']

    @property
    def charge_state(self):
        return self._request('charge_state')

    @property
    def climate_state(self):
        return self._request('climate_state')

    @property
    def drive_state(self):
        return self._request('drive_state')

    @property
    def gui_settings(self):
        return self._request('gui_settings')

    @property
    def vehicle_state(self):
        return self._request('vehicle_state')

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
        return self._conn.read_json_path('/api/1/vehicles/{}/wake_up' \
                                         .format(self.id), {})
