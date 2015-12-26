from . import stream

class CommandError(Exception):
    """Tesla Model S vehicle command returned failure"""
    pass

class Vehicle:
    def __init__(self, vin, conn, payload, log):
        assert payload['vin'] == vin

        self._conn = conn
        self._data = payload
        self._log = log

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
        return stream.Stream(self).read_stream(events, count)

    def refresh(self):
        self._conn.vehicles(True)

    def request(self, verb):
        return self._conn.read_json('/api/1/vehicles/{}/data_request/{}' \
                                    .format(self.id, verb))['response']

    def command(self, verb, **kwargs):
        p = self._conn.read_json('/api/1/vehicles/{}/command/{}' \
                                 .format(self.id, verb), kwargs)
        if 'response' not in p or not p['response']:
            # Command returned failure, raise exception
            raise CommandError(p['error'])

        return p['response']

    # API getter properties
    @property
    def mobile_enabled(self):
        return self._conn.read_json('/api/1/vehicles/{}/mobile_enabled' \
                                    .format(self.id))['response']

    @property
    def charge_state(self):
        return self.request('charge_state')

    @property
    def climate_state(self):
        return self.request('climate_state')

    @property
    def drive_state(self):
        return self.request('drive_state')

    @property
    def gui_settings(self):
        return self.request('gui_settings')

    @property
    def vehicle_state(self):
        return self.request('vehicle_state')

    # API commands
    def door_lock(self):
        return self.command('door_lock')

    def door_unlock(self):
        return self.command('door_unlock')

    def charge_port_door_open(self):
        return self.command('charge_port_door_open')

    def charge_standard(self):
        return self.command('charge_standard')

    def charge_max_range(self):
        return self.command('charge_max_range')

    def charge_start(self):
        return self.command('charge_start')

    def charge_stop(self):
        return self.command('charge_stop')

    def set_charge_limit(self, limit):
        self.command('set_charge_limit', percent = limit)

    def flash_lights(self):
        return self.command('flash_lights')

    def honk_horn(self):
        return self.command('honk_horn')

    def set_temps(self, driver, passenger):
        return self.command('set_temps', driver_temp = driver,
                            passenger_temp = passenger)

    def auto_conditioning_start(self):
        return self.command('auto_conditioning_start')

    def auto_conditioning_stop(self):
        return self.command('auto_conditioning_stop')

    def sun_roof_control(self, state, percent = None):
        args = {'state': state}

        if state == 'move' and percent != None:
            args['percent'] = percent

        if state in ('open', 'close', 'move', 'comfort', 'vent'):
            return self.command('sun_roof_control', **args)

        raise ValueError("Invalid sunroof state")

    def wake_up(self):
        d = self._conn.read_json('/api/1/vehicles/{}/wake_up' \
                                 .format(self.id), {})['response']

        # Update vehicle tokens if they're different from our cached
        # ones.
        tokens = d['tokens']

        if tokens != self._data['tokens']:
            self._data['tokens'] = tokens
            self._conn.save_state()

        return d
