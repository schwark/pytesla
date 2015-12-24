=======
pytesla
=======

pytesla is a python binding to the `Tesla Model S REST API <http://docs.timdorr.apiary.io/>` so that you can monitor your car or programmatically interact with it. It makes it easy to schedule charging times, trigger heating/cooling according to weather or just gather stats.

It currently maps the REST API 1:1.

This program requires that the client id and client secret (see <http://docs.timdorr.apiary.io/> for link to secrets) be stored as json data in ~/.pytesla, i.e.:

    { "client_id":     "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "client_secret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }

Usage
=====

    >>> import pytesla
    >>> mycar = pytesla.Connection('myemail', 'mypassword').vehicle('myvin')
    >>> mycar.honk_horn()
    True
    >>> for e in mycar.stream(StreamEvents.ALL, 2):
    >>>    print(str(e[0]))
    {'shift_state': 'P', 'elevation': '28', 'soc': '83', 'est_heading': '128', 'est_lat': 'xxx.yyy', 'timestamp': '1450666313710', 'power': '0', 'odometer': '1868.8', 'speed': '', 'est_lng': 'xxx.yyy'}
    {'shift_state': 'D', 'elevation': '28', 'soc': '83', 'est_heading': '128', 'est_lat': 'xxx.yyy', 'timestamp': '1450666315459', 'power': '21', 'odometer': '1868.8', 'speed': '43', 'est_lng': 'xxx.yyy'}

Installation
============

    $ pip install pytesla

