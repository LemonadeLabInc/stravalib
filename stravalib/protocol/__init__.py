from __future__ import division, absolute_import, print_function
import json
import logging
import collections

import requests
from pytz import FixedOffset
from dateutil import parser as date_parser

from stravalib import exc
from stravalib.measurement import IMPERIAL, METRIC

Credentials = collections.namedtuple('Credentials', ('username', 'password'))
    
class BaseModelMapper(object):
    """
    Base class for the mappers that populate model objects from V1/V2 results.
    """
    
    def __init__(self, units):
        """
        Initialize model mapper with desired units ('imperial' or 'metric').
        """
        valid_units = (IMPERIAL, METRIC)
        if not units in valid_units:
            raise ValueError("units param must be one of: {0}".format(valid_units))
        self.units = units

    def _parse_datetime(self, datestr, utcoffset=None):
        """
        Parses a Strava datetime; if offset is provided, this will be added to the date as a fixed-offset timezone.
        
        There are some quirks to Strava dates; namely they look like they are UTC but they are actually local to the
        rider's TZ. (It's OK, we just replace the tz.)
        
        :param utcoffset: The offset east of UTC, specified in seconds (for some bizarre reason).
        :type utcoffset: int
        """
        if utcoffset:
            tz = FixedOffset(utcoffset / 60)
        else:
            tz = None
        return date_parser.parse(datestr).replace(tzinfo=tz)
        
class BaseServerProxy(object):
    """
    
    """
    server = 'www.strava.com'
    
    def __init__(self, requests_session=None):
        """
        Initialize this protocol client, optionally providing a (shared) :class:`requests.Session`
        object.
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        if requests_session:
            self.rsess = requests_session
        else:
            self.rsess = requests.Session()
    
    def _get(self, url, params=None):
        self.log.debug("GET {0!r} with params {1!r}".format(url, params))
        raw = self.rsess.get(url, params=params)
        raw.raise_for_status()
        resp = self._handle_protocol_error(raw.json())
        return resp
    
    def _handle_protocol_error(self, response):
        """
        Parses the JSON response from the server, raising a :class:`stravatools.api.Fault` if the
        server returned an error.
        
        :param response: The response JSON
        :raises Fault: If the response contains an error. 
        """
        if 'error' in response:
            raise exc.Fault(response['error'])
        return response
    