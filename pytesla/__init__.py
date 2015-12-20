__version__ = "0.3"
__date__ = "02-06-2013"
__author__ = "Denis Laprise - dlaprise@gmail.com"

from . import vehicle
Vehicle = vehicle.Vehicle
CommandError = vehicle.CommandError

from . import connection
Connection = connection.Connection
