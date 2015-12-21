=======
pytesla
=======

pytesla is a python binding to the `Tesla Model S REST API <http://docs.timdorr.apiary.io/>` so that you can monitor your car or programmatically interact with it. It makes it easy to schedule charging times, trigger heating/cooling according to weather or just gather stats.

It currently maps the REST API 1:1.

Usage
=====

    >>> import pytesla
    >>> mycar = pytesla.Connection('myemail', 'mypassword').vehicle('myvin')
    >>> mycar.honk_horn()
    True
    >>> for e in mycar.stream([StreamEvents.ALL], 2):
    >>>    print(e)
    (['1450666313710', '0', '1868.8', '71', '15', '48', 'xxx.yyy', 'xxx.yyy', '1', 'P'], <Stream <Vehicle xxx>>)
    (['1450666315459', '0', '1868.8', '71', '15', '48', 'xxx.yyy', 'xxx.yyy', '2', 'P'], <Stream <Vehicle xxx>>)

Installation
============

    $ pip install pytesla

