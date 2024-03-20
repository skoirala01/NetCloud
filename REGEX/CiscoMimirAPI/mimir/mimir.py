from __future__ import unicode_literals, absolute_import

import os
import numbers
import types
import sys
import json
import getpass
import inspect
from time import time
import traceback
import copy
import logging
import pickle
import hashlib
import platform
from . import __version__
from .exceptions import MimirError, MimirAuthenticationError, MimirAuthorizationError
from .mimirData import MimirData, genMimirDataClass
from .mimirMeta import MimirMeta
import requests
from requests.exceptions import HTTPError

try:
    # to support python 3.10 and newer
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

if sys.version_info > (3, 0):
    from urllib.parse import urlencode
    basestring = str
    unicode = str
else:
    from urllib import urlencode
""" Python Client for the Mimir web API

This module defines the following class:

- `Mimir`, a client for the mimir webservice api

How To Use This Module
======================
(See the individual classes, methods, and attributes for details.)

    Instantiation
    --------------
    >>> from mimir import Mimir
    >>> m = Mimir()

    or if you want to Cache all results into the directory "/tmp/mcache"
    >>> m = Mimir(cache_dir="/tmp/mcache")

    or if you want to store and re-use the sso cookie in ~/.mimir-cookies-py
    >>> m = Mimir(cookie_file = "default")


    Authentication
    --------------
       cookie_file will be tried first (if it exists).
       If cookie is not valid (or does not exist) you will receive an
       interactive password prompt:
    >>> m.authenticate('username')

    or if you want to specify the password
    >>> m.authenticate('username', 'password')

    or if you are running within BDB (Big Data Broker)
    >>> m.authenticate(sso=env.cookies["ObSSOCookie"], interactive=False)


    Queries
    --------------
    >>> m.get_services()

    >>> m.get_services(scope='NP')

    >>> m.call_service(scope='NP', service='companies')

    Cache the output to a file and prevent multiple API calls for the same data
    (Easier to set a global cache_dir in the Mimir() call)
    >>> m.call_service(scope='NP', service='companies', cache_dir='/tmp/cache')

    Cache data is valid for 1 day be default, but can be changed
    >>> m.call_service(scope='NP', service='hw_eox_bulletins', cache_dir='/tmp/cache', cache_days=7)

    >>> m.call_service(scope='NP', service='groups', params={'cpyKey': 105261})

    OR (sugary)

    >>> m.np.companies.get()

    >>> m.np.groups.get(cpyKey=105261)
"""

__docformat__ = 'restructuredtext'

API_SPEC_FORMAT = 'swagger'
DEFAULT_HEADER = {'Accept': 'application/json', 'Content-Type': 'application/json'}
DEFAULT_SCHEME = 'https'
DEFAULT_PORT = 80
DEFAULT_API_PATH = '/api/mimir'
DEFAULT_URL = 'https://mimir-prod.cisco.com'
DEFAULT_CACHE_DAYS = 1
# If these are set as enviroment variables, use them by default
ENV_VAR_CACHE_DIR = 'MIMIR_CACHE_DIR'
ENV_VAR_CACHE_DAYS = 'MIMIR_CACHE_DAYS'
ENV_VAR_COOKIE_JAR = 'MIMIR_COOKIE_FILE'
SECONDS_PER_DAY = 86400
HTTP_METHODS = ['get', 'options', 'head', 'post', 'put', 'patch', 'delete']
# No longer using sso.cisco.com directly. Using Mimir Auth/login method instead
SSO_COOKIE_NAME = 'ObSSOCookie'
JSON_CONTENT = ['application/json;charset=UTF-8', 'application/json']

# This file will be put in users home directory if cookie file parameter
# is set to the string "default"
DEFAULT_COOKIE_FILE = '.mimir-cookies-py'

# If no bytes are received from HTTP server in this many seconds, timeout
# the session
DEFAULT_SSO_TIMEOUT = 30
DEFAULT_MIMIR_TIMEOUT = 1200
# chunk size for streaming non-json content
DEFAULT_CHUNK_SIZE = 1024

# used for stream parsing
META_PREFIX = '],"meta":'
DATA_PREFIX = '{"data":['


class Mimir(object):
    """ A client the mimir webservice api.
    """

    def __init__(self,
                 name=None,
                 parent=None,
                 append_slash=False,
                 username=None,
                 password=None,
                 hostname=None,
                 port=DEFAULT_PORT,
                 url=None,
                 cookies=None,
                 paging=False,
                 stream=True,
                 api_path=DEFAULT_API_PATH,
                 scheme=DEFAULT_SCHEME,
                 cache_dir=None,
                 cache_days=DEFAULT_CACHE_DAYS,
                 cookie_file=None,
                 interactive=True,
                 debug=False,
                 timeout=DEFAULT_MIMIR_TIMEOUT,
                 app_id=None):
        """
        Init client object

        Parameters:

        - `name` -- name of node
        - `parent` -- parent node for chaining
        - `append_slash` -- flag if you want a trailing slash in urls
        - `hostname` (string)(optional): webservice hostname. Defaults to None
        - `port`     (int)(optional): tcp port the webservice runs on. Defaults to 80
        - `scheme`   (string)(optional): http/https
        - `url`      (string)(optional): url of the webservice. Must include scheme (http(s)://).
                                        Superceedes `hostname` and `port` and defaults to theirs
        - `cookies`          (dict)   (optional): cookies for authentication
        - `cache_dir`        (string) (optional): Directory to cache results.  Paging makes no sense if caching is enabled.
        - `cache_days`       (number) (optional): Number of days cache files are valid (0 = flush)
        - `cookie_file`      (string) (optional): Filename to save cookies in.  If "Default", then use ~/.mimir-cookies
        - `interactive`      (Boolean)(optional): Default (True) means we will prompt for password during authentication if necessary
        - `timeout`          (number)(optional): If no bytes have been received in this many seconds, raise an exception
        - `app_id`           (string) (optional): Customize App ID sent to Mimir via X-Mimir-App and User-Agent headers (default to script or package)

        Environment variables can be used to set the default values for:
           cache_dir    = os.environ["MIMIR_CACHE_DIR"]   by default (unless ENV_VAR_CACHE_DIR was modified)
           cache_days   = os.environ["MIMIR_CACHE_DAYS"]  by default (unless ENV_VAR_CACHE_DAYS was modified)
           cookie_file  = os.environ["MIMIR_COOKIE_FILE"] by default (unless ENV_VAR_COOKIE_JAR was modified)

        Examples:
            >>> m = Mimir()

            >>> m = Mimir(hostname='mimir-lab', port='4000',
                            cookies={'ObSSOCookie':"uMGAEDbEy9wIkSD%2BKrIJZIfKAvymEFaES7rm0EnKq..."})
        """
        if url:
            self._baseurl = url
        elif hostname:
            self._hostname = hostname
            self._port = port
            self._baseurl = '{0}://{1}:{2}'.format(scheme, hostname, str(port))
        else:
            self._baseurl = DEFAULT_URL

        self.debug = debug
        if self.debug:
            logging.basicConfig(
                stream=sys.stderr,
                level=logging.DEBUG,
                format="%(asctime)s [%(levelname)8s]:  %(message)s")

        self._name = name
        self._parent = parent
        self._append_slash = append_slash
        self._baseapi = "{0}{1}".format(self._baseurl, api_path)
        self._session = None
        self._authenticated_user = None
        self.json = False
        self.meta = None
        self.headers = {}
        self.paging = paging
        self.stream = stream

        self._logger = logging.getLogger(__name__)

        if ((cookie_file is None) or
            (cookie_file.lower() == "default")) and ENV_VAR_COOKIE_JAR in os.environ:
            # Environment variable could be set to "disable" or "default" or to an actual file
            self._logger.debug("Environment variable {} = {}".format(ENV_VAR_COOKIE_JAR, os.environ[
                ENV_VAR_COOKIE_JAR]))
            cookie_file = os.environ[ENV_VAR_COOKIE_JAR]
        self._cookie_file = None
        if (cookie_file is not None) and (cookie_file != ""):
            if cookie_file.lower() == "disable":
                self._cookie_file = None
            elif cookie_file.lower() == "default":
                self._cookie_file = os.path.join(os.path.expanduser('~'), DEFAULT_COOKIE_FILE)
                self._logger.debug("Using default cookie jar file: {}".format(self._cookie_file))
            else:
                self._cookie_file = cookie_file
                self._logger.debug("Using specific cookie jar file: {}".format(self._cookie_file))

        # 10/2/2019 - Mimir backend changed to enable OAuth2 support - and it no longer returns ObSSO Cookies.
        #             (Cisco IT will eventually be turning of ObSSO cookie support)
        #             Work is underway to allow OAuth2 access_tokens to be passed
        #             Until then, there is no cookie we can save to cache for SSO support :-(
        if self._cookie_file is not None:
            self._logger.debug("FYI: Storing authentication credentials in a cookie jar ({}) is not currently supported".format(self._cookie_file))
            self._cookie_file = None

        if self._cookie_file is None:
            self._logger.debug("SSO Cookie will not be read from or stored to disk")

        # Same logic for cache_dir (but there is no "default" option)
        if cache_dir is None and ENV_VAR_CACHE_DIR in os.environ:
            cache_dir = os.environ[ENV_VAR_CACHE_DIR]
            self._logger.debug("Environment variable {} = {}".format(ENV_VAR_CACHE_DIR, cache_dir))
        self._cache_dir = None
        if (cache_dir is not None) and (cache_dir != ""):
            if cache_dir.lower() == "disable":
                self._cache_dir = None
            else:
                self._logger.debug("Cache directory set to: {}".format(cache_dir))
                self._cache_dir = cache_dir
        if self._cache_dir is None:
            self._logger.debug("Caching is disabled")

        if cache_days is None:
            if ENV_VAR_CACHE_DAYS in os.environ:
                cache_days = os.environ[ENV_VAR_CACHE_DAYS]
                self._logger.debug(
                    "Environment variable {} = {}".format(ENV_VAR_CACHE_DAYS, cache_days))
            else:
                cache_days = DEFAULT_CACHE_DAYS
        # Cache days must be an integer
        try:
            self._cache_days = int(cache_days)
        except ValueError:
            self._cache_days = DEFAULT_CACHE_DAYS
        if self._cache_dir is not None:
            self._logger.debug(
                "Cache files older than {} days will be ignored".format(self._cache_days))
        self._cache_handle = None
        self._cache_filename = None
        self._cache_filename_tmp = None

        self._interactive = interactive
        self._timeout = timeout

        self._user_agent = None
        self._app_id = app_id

        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        moduleName = None
        if mod:
            moduleName = str(mod.__name__)

        # construct user-agent and app id headers
        if self._app_id is None:
            if moduleName is None or moduleName == '__main__':
                if sys.argv[0]:
                    self._app_id = str(os.path.basename(sys.argv[0]))
                else:
                    # this is interactive mode most likely
                    self._app_id = 'python'
            elif moduleName.startswith('task_'):
                # BDB
                self._app_id = 'BDB ' + moduleName[5:]
            else:
                self._app_id = moduleName

        DEFAULT_HEADER[
            'User-Agent'] = "mimir-python-client: {0} requests: {1} python: {2}/{3} app: {4} platform: {5}".format(
                __version__, requests.__version__,
                platform.python_implementation(),
                platform.python_version(), self._app_id, platform.platform())
        DEFAULT_HEADER['X-Mimir-App'] = self._app_id
        self._logger.debug("User-Agent: " + DEFAULT_HEADER['User-Agent'])

        if cookies is None:
            # Load cookies from cookie_file
            cookies = self.get_cookies_from_file()

        self.reset_session(cookies=cookies)

        if username:
            self.authenticate(username, password)

    @classmethod
    def from_sso_cookie(cls, sso_cookie, **kw):
        """
        Alternative constructor for backwards compatability (Versions 0.2.4 and earlier)
        ** Better choice is to supply the SSO cookie to the authenticate method **
        Create `Mimir` client instance from an SSO cookie.
        All other keyword arguments are the same as `__init__`.

        Examples:
            >>> m = Mimir.from_sso_cookie('uMGAEDbEy9wIkSD%2BKrIJZIfKAvymE...',
                                          hostname='mimir-lab', port=4000)
        """
        kw['cookies'] = {SSO_COOKIE_NAME: sso_cookie}
        return cls(**kw)

    def _get_sso_cookie_uid(self):
        """
        Verify that the SSO cookie (in our cookie jar) is still valid
        Returns one of:
           - (string) username  : uid of the person who owns the cookie
           - (None)             : Cookie is not valid

        Parameters: none (SSO cookie should be in this session's cookie jar)

        """

        # First method tells us the username of the cookie's owner
        userInfo = self.verify_sso_cookie_info()
        if userInfo is not None:
            if userInfo.userid:
                return userInfo.userid

        # Failure.  Cookie not valid
        # An exception would have been thrown if Mimir was not reachable
        return None

    def get_sso_cookie_info(self):
        """
        For backwards compatability only (v0.2.28 and earlier has this function)
        Very unlikely anybody used this in their scripts - but it was exposed...

        It was the primary Cookie verification method that used  wsgx.cisco.com (which often was down)
        It returned a plain dict() (not an object of Mimir.resutl)
        """
        userinfoDict = dict()
        userinfo = self.verify_sso_cookie_info()
        if userinfo:
            userinfoDict['mail'] = userinfo.mail
            userinfoDict['uid'] = userinfo.userid
            userinfoDict['cn'] = userinfo.displayName
            # New routine does not break out first/last names.  So just giving
            # display name
            userinfoDict['givenName'] = userinfo.displayName
            userinfoDict['sn'] = userinfo.displayName
            return userinfoDict

    def verify_sso_cookie(self):
        """
        For backwards compatability only (v0.2.28 and earlier has this function)
        Very unlikely anybody used this in their scripts - but it was exposed...

        It was the secondary Cookie verification method that used  sso.cisco.com

        Returns one of:
            None - Cookie was not valid
            String "Valid" if cookie was valid
            raise an error on failure (mimir-prod.cisco.com being down breaks everything!)
        """

        userinfo = self.verify_sso_cookie_info()
        if userinfo is None:
            return None
        return "Valid"

    def verify_sso_cookie_info(self):
        """
        Cookie verification method: /api/mimir/auth/login

        If cookie was valid, it returns the JSON results:
            authTime        integer     The number of seconds expired during user authentication.
            displayName   string    Full name associated with a user.
            mail          string    An email address.
            remoteAddress   string    The IP Address of the requesting, remote client.
            roles           string    A list of one or more roles associated with a user.
            userAgent       string    The User Agent of the requesting, remote client.
            userid          string    A Cisco userid.
        Returns None otherwise

        """

        self._logger.debug("Getting SSO Information from Mimir...")
        try:
            # We will still write the cache file (if cacheing is enabled) to aid debugging,
            # but will never read it (cache_days=0).
            # If we find we do not want to write the cache file either, need to
            # set cache_dir=None
            userInfo = list(self.call_service(scope='auth', service='me', cache_days=0))[0]
            #print ("userInfo user = {}".format(userInfo.userid))
            return userInfo
        except MimirAuthenticationError:
            # When we used sso.cisco.com, this would be raised on bad auth
            return None
        except MimirAuthorizationError:
            # Mimir auth/me returns 401 - authorization
            return None

    def _get_sso_cookie_fromjar(self):
        """
        Look in the cookie jar for the SSO Cookie
        If it is in there, and looks valid, return it
        Otherwise, return None
        """

        cookies = requests.utils.dict_from_cookiejar(self._session.cookies)
        if not cookies or SSO_COOKIE_NAME not in cookies or cookies[SSO_COOKIE_NAME] is None:
            return None
        if cookies[SSO_COOKIE_NAME] == "loggedoutcontinue":
            # sso.cisco.com explicitly told us the cookie we were using was
            # invalid
            return None
        if len(cookies[SSO_COOKIE_NAME]) < 200:
            # Cookie is a very long string (398 characters).
            # If less than 200 characters, it is not a real SSO Cookie
            return None

        # Must be a real cookie
        return cookies[SSO_COOKIE_NAME]

    def authenticate(self, user=None, password=None, sso=None, username=None, interactive=None):
        """
        Authenticate to acquire SSO cookie (or use provided cookie if it is valid).

        Parameters:

        - `user`    : Cisco username
        - `password`: Cisco password. If not given, it will be asked interactively (for CLI sessions).
        - `sso`:      Cisco SSO Cookie to try (fallback to user/password if cookie is invalid)
        - `username` : Cisco username (allow either "user" or "username" for the parameter)

        """

        if interactive is None:
            interactive = self._interactive

        if (username is not None) and (user is None):
            # Keep this backwards compatable (param is "user"), but make it match
            # the __init__ function (which uses "username")
            user = username

        origUserArg = user
        if not user:
            user = getpass.getuser()

        sso_cookie_from = None
        if sso:
            # Use this cookie instead of whatever is in this session's cookie jar
            self.reset_session(cookies={SSO_COOKIE_NAME: sso})
            sso_cookie_from = "provided directly"
        else:
            sso = self._get_sso_cookie_fromjar()
            if sso:
                sso_cookie_from = "found in the cookie jar"

        if sso is not None:
            # See if the SSO Cookie is valid (not expired)
            self._logger.debug("Verifying SSO cookie that was {}".format(sso_cookie_from))
            uid = self._get_sso_cookie_uid()
            if uid is not None:
                self._logger.debug("Existing SSO Cookie is valid. It belongs to: {0}".format(uid))
                if ((origUserArg is None) or (uid == user)):
                    # Full Success, SSO belongs to the user, or no user was
                    # specified for this function
                    self.save_cookies()
                    self._authenticated_user = uid
                    return requests.utils.dict_from_cookiejar(self._session.cookies)

                # User supplied a different username - need to re-authenticate
                self._logger.debug(
                    "Existing SSO Cookie is for user {0}, requested user is {1}".format(uid, user))

            self._logger.debug("Existing SSO Cookie is not valid.  Need to re-authenticate")
            # Remove that cookie from the cookie jar so we can tell if username
            # authentication is successful
            self.reset_session()

        self._logger.debug("Will attempt user based authentication for: {}".format(user))
        #
        # User Based Authentication
        #
        # What we will return in any exception status
        fail_status = {
            'code': 999,
            'state': "FAIL",
            'status': 1,
            'type': "Logic Error",
            'error': None,
            'reason': None
        }
        if sso_cookie_from is not None:
            # If no user or password was provided (but SSO was), then fail
            # with code 401 and "Bad SSO Cookie" (instead of 999 and "Logic Error")
            fail_status["code"] = 401
            fail_status["type"] = "Authentication"
            fail_status["error"] = "Authentication Failed"
            fail_status["reason"] = "Bad SSO Cookie ({})".format(sso_cookie_from)

        if user is None:
            if fail_status["reason"]:
                fail_status["reason"] += " and cannot determine username"
            raise MimirAuthenticationError(
                "Authentication Failure - Cannot determine username", status=fail_status)

        if password is None:
            if interactive:
                self._logger.debug("Requesting Password from user")
                # getpass works under Windows, but not under pycharm console (it just freezes)
                # Workaround if using pycharm is to run with the debug enabled
                # (or run directly from the CMD window and bypass pycharm)
                if "PYCHARM_HOSTED" in os.environ:
                    self._logger.warning("You seem to be running this script under PyCharm.")
                    self._logger.warning(
                        "You must run in Debug mode in order to be prompted for a password")
                    self._logger.warning("Script will freeze at this point otherwise...")
                password = getpass.getpass(
                    'Enter Cisco password for user {0}: '.format(user).encode('ascii'))
            else:
                if fail_status["reason"]:
                    fail_status["reason"] += " and no password was provided for user {}".format(
                        user)
                raise MimirAuthenticationError(
                    "SSO Authentication Failure - No password provided for user {0}".format(user),
                    status=fail_status)

        # Adding auth informations to session, so we can fall back to basic
        # auth in case we're using a generic user
        self._session.auth = (user, password)

        # Get SSO cookie using Mimir API
        mimir_login_url = self._baseapi + "/auth/login"
        payload = {'userid': user, 'password': password}
        response = self._session.post(mimir_login_url, data=payload, allow_redirects=True)
        # When using Mimir for Auth/Me authentication, a wrong password will
        # cause this to throw an HTTPError exception (401 - Unauthorized for url)
        try:
            response.raise_for_status()
        except HTTPError as e:
            if e.response.status_code == requests.codes.unauthorized:
                raise MimirAuthenticationError(
                    "SSO Authentication Failure - We are unable to verify your credentials or could not locate you in the enterprise directory.",
                    status={
                        'code': 401,
                        'state': "FAIL",
                        'status': 1,
                        'type': "Authentication",
                        'error': "Authentication Failed",
                        'reason': "Bad username or password"
                    })
            raise

        # Disabled 10/3/2019 - SSO cookies are no longer provided by the Mimir API
        # catch invalid sso cookie (old logic - when using sso.cisco.com for authentication)
        # if self._get_sso_cookie_fromjar() is None:
        #     raise MimirAuthenticationError(
        #         "SSO Authentication Failure - We are unable to verify your credentials or could not locate you in the enterprise directory.",
        #         status={
        #             'code': 401,
        #             'state': "FAIL",
        #             'status': 1,
        #             'type': "Authentication",
        #             'error': "Authentication Failed",
        #             'reason': "Bad username or password"
        #         })

        self._authenticated_user = user
        # store cookies in a file for re-use
        self.save_cookies()
        return requests.utils.dict_from_cookiejar(self._session.cookies)

    def reset_session(self, cookies=None):
        """
        Reset the session.

        Parameters:

        - `cookies` (dict)(optional): cookies to start with

        Example:

        >>> c.reset_session()
        >>> c.reset_session(cookies={'cookie_name':"s:73NwSbWmRusOSLhrfnLAmcAa.vAPLHPZDRQfoX/QN61U7dXRzfbzCERhBy5QfBkM+El4"})
        """

        self._authenticated_user = None
        self._session = requests.Session()

        if cookies is not None:
            #self._logger.debug("reset_session cookies as params: {0}".format(cookies))
            # add all cookies
            requests.utils.add_dict_to_cookiejar(self._session.cookies, cookies)

            # catch invalid sso cookie
            if SSO_COOKIE_NAME in cookies:
                if cookies[SSO_COOKIE_NAME] is None:
                    raise MimirError(
                        SSO_COOKIE_NAME + " was passed but is None",
                        status={
                            'code': 999,
                            'state': "FAIL",
                            'status': 1,
                            'type': "Logic Error",
                            'error': "SSO Cookie value is None"
                        })

    def save_cookies(self):
        """
        Save this session's SSO Cookie in a file (if requested)
        """

        if not self._cookie_file:
            return None

        cookies_to_save = {}
        cookies_to_save[SSO_COOKIE_NAME] = self._get_sso_cookie_fromjar()

        try:
            file = open(self._cookie_file, 'wb')
            os.chmod(self._cookie_file, 0o600)
            pickle.dump(cookies_to_save, file)
            file.close()
            self._logger.debug("Saved SSO Cookies to {0}".format(self._cookie_file))
        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            return None

        return self._cookie_file

    def get_cookies_from_file(self):

        if not self._cookie_file:
            return None

        if not os.path.isfile(self._cookie_file):
            self._logger.debug("SSO Cookie file ({0}) does not exist".format(self._cookie_file))
            return None

        cookies = None
        try:
            file = open(self._cookie_file, 'rb')
            cookies = pickle.load(file)
            file.close()
            self._logger.debug("Extracted Cookies from {0}".format(self._cookie_file))
        except ValueError as e:
            if e.message == "unsupported pickle protocol: 3":
                self._logger.warning(
                    "SSO Cookie file ({0}) created with Python3 - cannot read with Python2".format(
                        self._cookie_file))
            else:
                self._logger.warning(
                    "SSO Cookie file ({0}) corrupted: {1}".format(self._cookie_file, e.message))
            return None
        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            return None

        return cookies

    def get_services(self,
                     scope=None,
                     service=None,
                     cache_dir=None,
                     cache_days=None,
                     timestamp_request=False,
                     cache_filename_request=False,
                     format=API_SPEC_FORMAT):
        """
        Get list of Mimir API services

        Parameters:
        - `scope` (optional): Filter services by scope (e.g. 'NP')
        - `service` (optional): Filter services by request/service (e.g. 'company_list')

        Example:

        >>> m.get_services(scope='NP')

        {   u'definition': u'Pull the Inventory from Network Profile, based on a company key and group id.',
        u'input': [   {   u'name': u'cpy.key', u'var': u'cpy.key'},
                      {   u'name': u'date', u'var': u'date'}],
        u'output': None,
        u'request': u'np_reports',
        u'scope': u'NP',
        u'url': u'http://localhost.cisco.com:4000/api/mimir/np/np_reports',
        u'version': u'1.0'}]

        ...

        """
        url = self._baseapi
        if scope:
            url = self._baseapi + '/' + scope.lower()
        if service:
            url = url + '/' + service.lower() + '/definition'

        if cache_dir is None:
            cache_dir = self._cache_dir
        if cache_days is None:
            cache_days = self._cache_days

        if timestamp_request or cache_filename_request:
            cache_file = self._cache_file(cache_dir=cache_dir, url=url)
            if cache_filename_request:
                return cache_file
            # Otherwise, return the timestamp of the cached data
            if os.path.isfile(cache_file):
                st = os.stat(cache_file)
                return st.st_mtime
            return 0

        return self._get_cache(
            url=url, cache_dir=cache_dir, cache_days=cache_days, params={"format": format})

    def call_service_json(self, url=None, cache_dir=None, cache_days=None, params={}):
        """
        Call Mimir service and return results as raw JSON with no pagination handling
        NOTE: Its recommended to use call_service to take advantage of pagination support

        Parameters:
        - `scope`   (optional): Services by scope (e.g. 'np')
        - `service` (optional): Services by request/service (e.g. 'companies')
        - `path`    (optional): Services by path (e.g. 'np/companies')
        - `params`  (optional/required): Service parameters (optional for some services)

        Examples:

        """
        self._logger.debug(
            "Getting Data for {} with params: {} (cache={})".format(url, params, cache_dir))
        result = self._get_cache(url=url, params=params, cache_dir=cache_dir, cache_days=cache_days)

        return result

    def _get_cache(self, url, cache_dir=None, cache_days=None, params={}):
        """
        Get result from Cache or HTTP
        Parameters:
        - `url`     (required): Full URL
        - `params`  (optional/required): Service parameters (optional for some services)
        """

        cache_file = None
        self._cache_handle = None
        # Only set if we are writing to a cache file
        self._cache_filename = None
        self._cache_filename_tmp = None

        full_url = self._full_url(url, params)

        if cache_dir is not None:
            if not os.path.isdir(cache_dir):
                # Not using makedirs - at least the uppper level directory must
                # already exist
                os.mkdir(cache_dir)
            cache_file = self._cache_file(cache_dir=cache_dir, url=url, params=params)
            # The _cache_file routine should figure out what encoding the user wanted
            # Only if it chose "json", do we know what to do with it.
            ext = os.path.splitext(cache_file)[1]
            if ext == ".json":
                self.json = True

        dataStr = None
        if cache_file is not None:
            if os.path.isfile(cache_file):
                st = os.stat(cache_file)
                age = (time() - st.st_mtime)
                if (age > (cache_days * SECONDS_PER_DAY)):
                    self._logger.debug("Deleting expired cache file {} ({} seconds > {} seconds)".
                                       format(cache_file, int(age), (cache_days * SECONDS_PER_DAY)))
                    os.remove(cache_file)
                    self._cache_handle = None
                else:
                    self._logger.debug(
                        "Using cache file: {0}, age={1}".format(cache_file, int(age)))
                    self._logger.debug("Suppressing HTTP Request for {}".format(full_url))
                    f = open(cache_file, 'rb')
                    if self.stream:
                        return f
                    else:
                        if self.json:
                            dataStr = f.read().decode('utf8')
                        else:
                            dataStr = f.read()

                        f.close()
                        self._logger.debug("Read {} bytes from cached file (JSON={})".format(
                            len(dataStr), self.json))

        if dataStr is None:
            self._logger.debug("Making HTTP query for {0}".format(full_url))

            headers = DEFAULT_HEADER.copy()
            # if user specified data format remove Accept header
            if 'format' in params:
                del headers['Accept']

            r = self._session.get(
                full_url,
                allow_redirects=True,
                headers=headers,
                timeout=self._timeout,
                stream=self.stream)
            self._headers(r.headers)
            self.raise_on_http_error(r)

            if r.headers['Content-Type'].lower() in (name.lower() for name in JSON_CONTENT):
                self.json = True
            else:
                self.json = False

            # disable streaming for swagger specs
            if 'format' in params and params['format'] == 'swagger':
                self.json = True
                self.stream = False

            if cache_file is not None:
                self._cache_filename = cache_file  # We are writing to cache
                if self.stream:
                    # In Streaming mode, we write to the cache file in chunks as data is received.
                    # If the program exits before all data is received, the cache file will
                    # be not proper JSON - and the API will fail next time it tries to read that cache file
                    # So only write to a temp file, and rename it to the proper cache_file name
                    # after all data has been received
                    self._cache_filename_tmp = self._tmp_cache_file(cache_file)
                    self._logger.debug(
                        "Writing to temporary cache file {0}..".format(self._cache_filename_tmp))
                    self._cache_handle = open(self._cache_filename_tmp, "wb")
                else:
                    self._logger.debug("Opening cache file {0} for write...".format(cache_file))
                    self._cache_handle = open(cache_file, "wb")

            if self.stream:

                # return iterator
                if self.json:
                    return r.iter_lines()
                else:
                    return r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE)

            else:
                if self.json:
                    dataStr = r.text
                else:
                    dataStr = r.content
                if self._cache_handle is not None:
                    self._logger.debug(
                        "Writing {0} characters to {1}".format(len(dataStr), cache_file))
                    if self.json:
                        self._cache_handle.write(dataStr.encode('utf8'))
                    else:
                        self._cache_handle.write(dataStr)

                    self._cache_handle.close()

        # Only get this far if user specified stream=False
        if dataStr and self.json:
            result = json.loads(dataStr)
        else:
            return dataStr

        if result and 'meta' in result:
            meta = self._meta(result['meta'])
            if meta.status['state'] == 'FAIL':
                raise MimirError(meta.status['reason'], status=meta.status)

        return result

    def request(self,
                method,
                url,
                headers={},
                data=None,
                json=None,
                files=None,
                params={},
                asdict=False):
        """
        HTTP Request
        Parameters:
        - `method`  (required): HTTP Method
        - `url`     (required): Full URL
        - `headers` (optional/required): Service headers (optional for most services)
        - `json`    (optional/required): Service body JSON (optional for most services)
        - `files`   (optional/required): Service body files for file upload (optional for most services)
        - `data`    (optional/required): Service body or form data (optional for most services)
        - `params`  (optional/required): Service parameters (optional for some services)
        """

        full_url = self._full_url(self._baseapi + '/' + url.lower(), params)
        self._logger.debug("Making HTTP {0} query for {1}".format(method, full_url))

        # map in default headers
        for header in DEFAULT_HEADER:
            if header not in headers:
                headers[header] = DEFAULT_HEADER[header]

        req = requests.Request(method, full_url, data=data, headers=headers, json=json, files=files)
        prep = self._session.prepare_request(req)
        r = self._session.send(
            prep, allow_redirects=True, stream=self.stream, timeout=self._timeout)
        self._headers(r.headers)
        self.raise_on_http_error(r)

        if r.headers['Content-Type'].lower() in (name.lower() for name in JSON_CONTENT):
            self.json = True
        else:
            self.json = False

        if self.stream:
            # if JSON return our chunked iterator
            if self.json:
                return self._result_iterate(result=r.iter_lines(), asdict=asdict, meta=True)
            else:
                # return iterator
                return r.iter_content(chunk_size=DEFAULT_CHUNK_SIZE)
        else:
            # only decode JSON
            if self.json:
                result = json.loads(r.text)
            else:
                return r.content

            if result and 'meta' in result:
                meta = self._meta(result['meta'])
                if meta.status['state'] == 'FAIL':
                    raise MimirError(meta.status['reason'], status=meta.status)

            return result

    def _full_url(self, url, params={}):
        """
        Construct full HTTP url for request
        """

        if not url or url is None:
            return

        if params is None:
            params = {}

        return '{0}?{1}'.format(url, '&'.join([urlencode(d) for d in self._clean_params(params)]))

    def _clean_params(self, params={}):
        """
        Clean null, blank, and None input params
        """
        goodparams = []
        for k, v in params.items():
            if v is None:
                continue
            elif isinstance(v, bool) and not v and v is not False:
                continue
            elif isinstance(v, numbers.Number) and not v and v != 0:
                continue
            elif isinstance(v, basestring) and not v:
                continue
            elif isinstance(v, Iterable) and not isinstance(v, basestring):
                goodparams.extend([{k: val} for val in v])
            else:
                goodparams.append({k: v})

        # Following sorting is necessary to have deterministic URL's (essential
        # for caching based on URL)
        goodparams = sorted(goodparams, key=lambda d: list(d.items())[0])
        return goodparams

    def _cache_file(self, cache_dir, url, params={}):
        """
        Based on the Full URL, return the filename that would be used for caching
        URL can have lots of illegal filename characters, so using an SHA1 hash of the URL as the filename
        """

        # TODO: Handle other HTTP methods...
        url = self._full_url(url, params)

        if cache_dir is None:
            return

        h = hashlib.sha1()
        h.update(url.encode('utf8'))
        base_filename = h.hexdigest()
        filename_suffix = "json"  # This module only does JSON today.  Need to update this to support other types

        cache_file = os.path.join(cache_dir, base_filename + "." + filename_suffix)
        return cache_file

    def _tmp_cache_file(self, cache_filename):
        """
        Based on what the real cache filename is (using the _cache_file() logic above)
        Create a suitable temporary filename that works on most operating systems
        A temp cache is not going have valid JSON content, as it has not been fully written
        """
        (filebase, ext) = os.path.splitext(cache_filename)
        return filebase + ".TMP"

    def _result_iterate(self, result=None, asdict=False, meta=False, dataClass=MimirData):
        """
        Return the results from a Mimir service call w/o paging as python generator (iterator)

        Parameters:
        - `result`  (required): Data returned from Services call
        """

        data = []
        Result = None

        if isinstance(result, types.GeneratorType):

            # if not JSON just return raw results
            for chunk in result:

                if self._cache_handle:
                    if self.json:
                        self._cache_handle.write(chunk + b'\n')
                    else:
                        self._cache_handle.write(chunk)

                if self.json:
                    result = self._iterate_chunk(
                        chunk=chunk, asdict=asdict, meta=meta, dataClass=dataClass)
                else:
                    result = chunk
                if result:
                    yield result

            if self._cache_handle:
                self._cache_handle.close()
                if self._cache_filename_tmp:
                    # We were writing to a temporary cache file
                    # Now that it is completely written, rename it to the
                    # correct name
                    self._logger.debug(
                        "Renaming temporary cache file to {0}".format(self._cache_filename))
                    os.rename(self._cache_filename_tmp, self._cache_filename)
                    self._cache_filename = None
                    self._cache_filename_tmp = None

        elif hasattr(result, 'read'):
            # read lines and return results
            for line in result:
                line = line.rstrip()
                if line:
                    result = self._iterate_chunk(
                        chunk=line, asdict=asdict, meta=meta, dataClass=dataClass)
                    if result:
                        yield result
        else:
            if isinstance(result, list):
                data = result
            elif result is not None and 'data' in result:
                data = result.get("data", [])
            elif result is not None:
                data = [result]
            else:
                data = []

            for row in data:
                if asdict:
                    yield row
                else:
                    # Before v0.2.30, this returned a namedtuple.
                    # Now returns a class derived from the MimirData class
                    yield dataClass(row)

    def _iterate_chunk(self, chunk=None, asdict=False, meta=False, dataClass=MimirData):
        """
        Process a chunk or line of data from iterator

        Parameters:
        - `chunk`  (required): Line or chunk of data from iterator
        """

        Result = None

        if not isinstance(chunk, unicode):
            chunk = chunk.decode('utf8')

        if not chunk or not chunk.strip():
            return None

        elif chunk.startswith(META_PREFIX):

            metaString = chunk[len(META_PREFIX):]
            # the -1 strips the trailing }
            metaData = json.loads(metaString[:-1])
            metaInstance = self._meta(metaData)

            # if the caller requested meta responses
            # then return
            if meta:
                return metaInstance
            else:
                return None

        elif not chunk.startswith(DATA_PREFIX):
            # should be a row of data
            # remove trailing comma from json row
            row = json.loads(chunk.rstrip(','))
            if asdict:
                return row
            else:
                # Before v0.2.30, this returned a namedtuple.
                # Now returns a class derived from the MimirData class
                return dataClass(row)
        else:
            return None

    def _call_service_paged(self,
                            initial_page=None,
                            url=None,
                            asdict=False,
                            cache_dir=None,
                            cache_days=None,
                            dataClass=MimirData,
                            params={}):
        """
        Call Mimir service with paging and return results as python generator (iterator)

        Parameters:
        - `scope` (required): Services by scope (e.g. 'NP')
        - `service` (required): Services by request/service (e.g. 'companies')
        - `params`  (optional/required): Service parameters (optional for some services)

        """

        current_page = 1
        if 'page' in params:
            current_page = params['page']

        while current_page >= 0:
            params['page'] = current_page
            if initial_page is not None:
                result = initial_page
                initial_page = None
            else:
                result = self.call_service_json(
                    url=url, cache_dir=cache_dir, cache_days=cache_days, params=params)

            pages = 1
            iterator = self._result_iterate(
                result=result, asdict=asdict, meta=True, dataClass=dataClass)
            for item in iterator:
                if asdict and 'Meta' in str(item):
                    pages = item['Meta']['pagination']['pages']
                elif isinstance(item, MimirMeta):
                    pages = item.pagination['pages']
                else:
                    yield item

            if current_page < pages:
                current_page += 1
            else:
                current_page = -1

    def call_service(self,
                     scope=None,
                     service=None,
                     path=None,
                     asdict=False,
                     paging=None,
                     cache_dir=None,
                     cache_days=None,
                     timestamp_request=False,
                     cache_filename_request=False,
                     params={}):
        """
        Call Mimir service and return results as python generator (iterator)

        Parameters:
        - `scope` (required): Services by scope (e.g. 'NP')
        - `service` (required): Services by request/service (e.g. 'companies')
        - `paging`  (optional): Enable pagination (default is False)
        - `params`  (optional/required): Service parameters (optional for some services)
        - 'cache_dir' (optional)  Where to cache the results
        - 'cache_day' (optional)  How many days are the results good for
        - 'timestamp_request' (optional)  Do not return results, only return the timestamp of the data (0 = data is not cached)
        - 'cache_filename_request' (optional)  Return the path to the cache file, if exists

        Examples:

        >>> results = m.call_service(scope='NP', service='companies')
        >>> results.next()

        or

        >>> results = list(m.call_service(scope='NP', service='companies'))

        or

        >>> for result in m.call_service(scope='NP', service='companies')

        or

        >>> for result in m.call_service(path='np/companies')

        """

        self.json = False

        # Compute URL here, so we can return cached file info if requested
        url = self._baseapi

        # Depening on what Mimir call is being made, a different class name may be returned
        # By default, just return the generic MimirData class
        dataClass = MimirData

        if scope or service:
            if scope:
                url = self._baseapi + '/' + scope.lower()
            if service:
                url = url + '/' + service.lower()
        elif path:
            url = self._baseapi + '/' + path.lower()
        else:
            url = self._baseapi

        # common way to get scope and service from any url
        # needed change as paths can have IDs embedded so we
        # need to strip off the mimir base path and be looking
        # for the scope/service
        url_path = url[len(self._baseapi):].strip("/")
        if url_path:
            path_parts = url_path.split("/")
            if len(path_parts) >= 1:
                scope = path_parts[0]
                if not scope and len(path_parts) >= 2:
                    scope = path_parts[1]
                elif len(path_parts) >= 2:
                    service = path_parts[1]
                    dataClass = genMimirDataClass(scope, service)

        self._logger.debug("Will return objects of type {0}. scope={1}, service={2}, path={3}".
                           format(dataClass, scope, service, url_path))

        # by default if you call /api/mimir/np it will try
        # to generate and return an API spec in the requested
        # format
        if not service and 'format' not in params:
            params['format'] = API_SPEC_FORMAT

        # default to whatever was passed into constructor
        if paging is None:
            if 'paging' in params:
                paging = params['paging']
                params.pop('paging', None)
            elif 'page' in params:
                paging = True
            else:
                paging = self.paging
        if cache_dir is None:
            if 'cache_dir' in params:
                cache_dir = params['cache_dir']
                params.pop('cache_dir', None)
            else:
                cache_dir = self._cache_dir
        if cache_days is None:
            if 'cache_days' in params:
                cache_days = params['cache_days']
                params.pop('cache_days', None)
            else:
                cache_days = self._cache_days

        if timestamp_request or cache_filename_request:
            cache_file = self._cache_file(cache_dir=cache_dir, url=url, params=params)
            if cache_filename_request:
                return cache_file
            # Otherwise, return the timestamp of the cached data
            if os.path.isfile(cache_file):
                st = os.stat(cache_file)
                return st.st_mtime
            return 0

        # Get the data (or at least the initial page of data) from the server
        # Any exceptions (authorization failed, server unreachable, no data found),
        # will be thrown immediately (rather than while the results are
        # iterated)

        # enable paging if not already
        if paging and 'page' not in params:
            params['page'] = 1

        result = self.call_service_json(
            url=url, cache_dir=cache_dir, cache_days=cache_days, params=params)
        if paging:
            # Exceptions can be thrown within the iterator, so the client code may want to handle that.
            # But the most common exceptions (authorization, unreachable, no data) will have occurred
            # when we downloaded the initial page above.
            return self._call_service_paged(
                initial_page=result,
                asdict=asdict,
                url=url,
                cache_dir=cache_dir,
                cache_days=cache_days,
                params=params,
                dataClass=dataClass)
        else:
            # Return an iterator that will be used to access the data
            return self._result_iterate(result=result, asdict=asdict, dataClass=dataClass)

    def __is_sso_redirect(self, response):
        """ Returns true if the response is a Cisco SSO redirect, false otherwise
        """
        signatures = ['/autho/forms/CDClogin.html', 'sso.cisco.com', 'www.cisco.com/cgi-bin/login']
        for redirect in response.history:
            for signature in signatures:
                if signature in redirect.headers['location']:
                    return True
        return False

    def raise_on_http_error(self, response):
        """ Raises an exception if a redirect was received with hint to authenticate.
        If another status code is received, raise as per requests.response.raise_for_status()
        except for error 500 (internal server error) where we want to send the
        context for the error
        """

        # return if in the 200 or 300 range
        if (response.status_code < 400):
            return

        if (response.status_code == 401) or self.__is_sso_redirect(response):
            # 401 is returned when we call Mimir auth/me with bad credentials
            # status assigned is what was (most likely) in the meta.status of the response
            raise MimirAuthenticationError(
                "Did you use authenticate() or provide an authentication cookie?",
                status={
                    "code": 401,
                    "type": "Unauthorized",
                    "reason": "Login Failed. Try Again",
                    "state": "FAIL",
                    "status": 1
                })

        content = response.content

        if not isinstance(content, unicode):
            content = content.decode('utf8')

        if content and '"meta":' in content:
            self._logger.error("code: {0} message: {1}".format(str(response.status_code), content))
            data = json.loads(content)
            errorType = 'General'
            errorReason = content
            if data and 'meta' in data:
                meta = self._meta(data['meta'])
                if meta.status:
                    meta_status = meta.status
                    errorType = meta.status['error']
                    errorReason = meta.status['reason']
            errmsg = "{0} - {1}".format(errorType, errorReason)
            if (response.status_code == 403):
                meta_status["code"] = 403
                meta_status["type"] = "Forbidden"
                raise MimirAuthorizationError(errmsg, status=meta_status)
            else:
                raise MimirError(errmsg, status=meta_status)

        # catch unhandled error if any
        http_error_msg = ''

        if 400 <= response.status_code < 501:
            http_error_msg = '%s Client Error: %s' % (response.status_code,
                                                      "URL: {0}, Reason:{1}".format(
                                                          response.url, response.reason))
            if hasattr(response, 'payload'):
                http_error_msg += ', Payload: {0}'.format(response.content)

        elif 500 <= response.status_code < 600:
            http_error_msg = '%s Server Error: %s' % (response.status_code, response.reason)

        if http_error_msg:
            raise HTTPError(http_error_msg, response=response)

    def get(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.call_service(path=self._url(*args), params=kwargs)

    def head(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.request('HEAD', self._url(*args), **kwargs)

    def post(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.request('POST', self._url(*args), **kwargs)

    def put(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.request('PUT', self._url(*args), **kwargs)

    def patch(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.request('PATCH', self._url(*args), **kwargs)

    def delete(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.request('DELETE', self._url(*args), **kwargs)

    def timestamp(self, *args, **kwargs):
        """
        Return the timestamp of the cached result (or 0 if not cached)
        """
        return self.call_service(path=self._url(*args), params=kwargs, timestamp_request=True)

    def getfilename(self, *args, **kwargs):
        """
        Return the path to the file that has the cached results
        """
        return self.call_service(path=self._url(*args), params=kwargs, cache_filename_request=True)

    def getdict(self, *args, **kwargs):
        """
        Makes the request
        """
        return self.call_service(path=self._url(*args), asdict=True, params=kwargs)

    def _meta(self, data):
        """Maps meta-data and other attributes to parent
        """
        # TODO: This seems ugly but not sure of a better way right now

        metaInstance = MimirMeta(data)

        self.meta = metaInstance
        current = self
        while current:
            if current._parent:
                current._parent.meta = metaInstance
            current = current._parent
        return metaInstance

    def _headers(self, headers):
        """Maps latest response headers to parent object
        """
        # TODO: This seems ugly but not sure of a better way right now

        self.headers = headers
        current = self
        while current:
            if current._parent:
                current._parent.headers = headers
            current = current._parent

    def _spawn(self, name):
        """Returns a shallow copy of current `Mimir` instance as nested child
        Arguments:
            name -- name of child
        """
        child = copy.copy(self)
        child._name = name
        child._parent = self
        return child

    def __getattr__(self, name):
        """Here comes some magic. Any absent attribute typed within class
        falls here and return a new child `Mimir` instance in the chain.
        """
        # Ignore specials (Otherwise shallow copying causes infinite loops)
        if name.startswith('__'):
            raise AttributeError(name)
        return self._spawn(name)

    def __iter__(self):
        """Iterator implementation which iterates over `Mimir` chain."""
        current = self
        while current:
            if current._name:
                yield current
            current = current._parent

    def _chain(self, *args):
        """This method converts args into chained Mimir instances
        Arguments:
            *args -- array of string representable objects
        """
        chain = self
        for arg in args:
            chain = chain._spawn(str(arg))
        return chain

    def _close_session(self):
        """Closes session if exists"""
        if self._session:
            self._session.close()

    def __call__(self, *args):
        """Here comes second magic. If any `Mimir` instance called it
        returns a new child `Mimir` instance in the chain
        """
        return self._chain(*args)

    def _url(self, *args):
        """Converts current `Mimir` chain into a url string
        Arguments:
            *args -- extra url path components to tail
        """
        path_comps = [mock._name for mock in self._chain(*args)]
        url = "/".join(reversed(path_comps))
        if self._append_slash:
            url = url + "/"
        return url

    def __repr__(self):
        """ String representaion of current `Mimir` chain"""
        return self._url()


def main():
    """
    Perform some functions to demonstrate and test the module.
    """
    import pprint
    m = Mimir()
    # list all services
    result = m.get_services()
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(result)


if __name__ == '__main__':
    main()
