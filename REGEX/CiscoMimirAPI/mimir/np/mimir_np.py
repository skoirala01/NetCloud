from __future__ import unicode_literals, absolute_import

from mimir import Mimir, MimirAuthenticationError, MimirAuthorizationError, MimirError
from .bdb_helpers import bdb_SSO_cookie
from .groups import Groups
from .chunker import Chunker
import logging

# Extends the Mimir class
class Mimir_np(Mimir):
    """ A client the mimir webservice api, focused on the NetProfiler (NP) service
    """
    def __init__(self, **kwargs):
        """
        Initializing this class does 3 things:
           1. Instanciate a new Mimir_np object
           2. Authenticate using that Mimir_np object
           3. If authentication is successful, and an NP company key was specified (cpyKey):
                  Verifies user is authorized to access the specified NP company
                 Throws MimirAuthorizationError if user is not authorized

        :param cookies:     HTTP cookies object (when calling from a BDB script, pass "cookies=env.cookies")
                            If the SSO cookie ("ObSSOCookie") is in the cookies dict, use it (and cookie_file is disabled)
        :param cookie_file: File to store cookies (authentication cookie)
                            "disable" = Do not use a cookie file
                            None      = Do not use a cookie file (unless environment variable MIMIR_COOKIE_FILE says otherwise)
                            "default" = Use environment variable MIMIR_COOKIE_FILE if it exists, otherwise use ~/.mimir-cache-py
                            filename  = filename to use to store cookies
        :param cache_dir:   Cache all queries in a directory.  Good while developing scripts!
                            "disable" = Do not cache any Mimir data
                            None      = Do not cache any Mimir data (unless environment variable MIMIR_CACHE_DIR says otherwise)
                            directory = Directory to cache data into
        :param cache_days:  Cached queries will be reused for this many days (default = 1 day)
                            None      = Use environment variable MIMIR_CACHE_DAYS if it exists, otherwise use default (1 day)
                            0         = Do not read any cache files (treat them all as expired).  May still write cache files (depending on cache_dir setting)
        :param username: username passed on command line
        :param password: password if passed on command line
        :param interactive: If no password supplied (and SSO Cookie is not valid), prompt for it
        :param cpyKey: Optionally, verify we have access to this NP Company.

        Common exceptions that can occur
              MimirAuthenticationError  - Username was not provided, or authentication
                                          was denied (SSO server was reachable, however)
              MimirAuthorizationError   - NP cpyKey was specified, and user does not have
                                          access to that account (Mimir never implemented
                                          this, so it is part of Mimir_np.call_service()
              MimirError                - Some other error

              requests.exceptions.ConnectionError
                                        - 'Failed to establish a new connection: \
                                           [Errno 8] nodename nor servname provided, or not known'
                                    - If you are not on the cisco network, or Mimir server is down

        New Methods (not found in the Mimir parent class):
            get_my_companies() - Make a call to np.companies_entitled.get()
                                 and filter out Test accounts
            grouper() - Get NP group info for a customer
            chunker() - Get data in chunks and avoid duplicates

        """
        logger = logging.getLogger(__name__)

        # Will remove these 3 from kwargs to prevent authentication
        # when we instanciate the Mimir object
        username = None
        if "username" in kwargs:
            username = kwargs["username"]
            del kwargs["username"]
        password = None
        if "password" in kwargs:
            password = kwargs["password"]
            del kwargs["password"]
        # BDB Passes sso cookie as cookies["ObSSOCookie"]
        cookies = None
        if "cookies" in kwargs:
            cookies = kwargs["cookies"]
            del kwargs["cookies"]
        # Loki just passes the sso cookie directly
        sso = None
        if "sso" in kwargs:
            sso = kwargs["sso"]
            del kwargs["sso"]

        # Extract/remove any parameters that are unique to the Mimir_np class
        throwAuthExceptions = True
        if "throwAuthExceptions" in kwargs:
            throwAuthExceptions = kwargs["throwAuthExceptions"]
            del kwargs["throwAuthExceptions"]

        cpyKey = None
        if "cpyKey" in kwargs:
            cpyKey = kwargs["cpyKey"]
            del kwargs["cpyKey"]

        groupId = None
        if "groupId" in kwargs:
            groupId = kwargs["groupId"]
            del kwargs["groupId"]

        url = None;
        if "usedev" in kwargs:
            if kwargs["usedev"]:
                # This only happens with standalone client.  BDB client does not have an option to set this
                # So okay to use print() function
                logger.info("***************** USING DEVELOPMENT SERVER ***********************")
                url = "http://mimir-dev.cisco.com"
            del kwargs["usedev"]

        if sso is None:
            sso = bdb_SSO_cookie(cookies)
            if sso is not None:
                logger.debug("Will be using the SSO Cookie from BDB")
                # Got SSO cookie from BDB HTTP interface (most likely)
                kwargs["cookie_file"] = "Disable"

        # Now intialize the parent (Mimir) class object
        # Below are default values (4/2016), in case you want to change them:
        #    hostname='mimir-prod.cisco.com',
        #    port=80
        #    timeout=600
        Mimir.__init__(self, **kwargs)

        # Now, authenticate
        # Call the Mimir authenticate method
        self.authenticate(user=username, password=password, sso=sso)

        self.cpyKey = cpyKey
        self.groupId = groupId
        if cpyKey is None or cpyKey == 0:
            # End-user did not really want to get data from an actual customer
            # No need to try authorization, just quickly return
            self.company_info = None
            self.cpyKey = None
            return

        # Verify this user is authorized to access this particular NP account

        # An Authorization exception will be thrown in Mimir_np.call_service() if
        # the user does not have authorization (no need to catch any exceptions here)
        if throwAuthExceptions:
            self.company_info = list(self.np.companies.get(cpyKey=cpyKey))[0]
        else:
            # Problem with throwing an authorization exception is the script would
            # then need to re-autheniticate in order to extract companies_entitled
            # for this user.
            # Instead, allow the calling script to use m.company_info to see if
            # authorization failed
            try:
                self.company_info = list(self.np.companies.get(cpyKey=cpyKey))[0]
            except MimirAuthorizationError:
                self.company_info = None
                self.cpyKey = None

        return

    def call_service(self, **kwargs):
        """
        Extends Mimir call_service()
        Will fill in cpyKey for most NP queries
        """
        self._logger.debug("Called Mimir_np.call_service with args: {}".format(kwargs))

        if "params" in kwargs:
            if "cpyKey" not in kwargs["params"]:
                self._logger.debug("cpyKey not specified, using {}".format(self.cpyKey))
                kwargs["params"]["cpyKey"] = self.cpyKey
            if "groupId" not in kwargs["params"]:
                self._logger.debug("groupId not specified, using {}".format(self.groupId))
                kwargs["params"]["groupId"] = self.groupId

        # TODO: If scope or path was not specified, we will set it to "np"
        if "path" in kwargs and kwargs["path"]:
            # Does path have both a scope and a service (ie. "np/device_details")?
            # If it has no slash, then it must just be a service
            if "/" not in kwargs["path"]:
                kwargs["path"] = "np/" + kwargs["path"]
                self._logger.debug(
                    "Added np scope to path.  Now path = {}".format(kwargs["path"]))

        try:
            data = Mimir.call_service(self, **kwargs)
            return data
        except MimirError as e:
            # Mimir exception types have no defined attributes :-(
            # Uses the default exception class "args" to pass a list
            # The first element of the list is the error string
            msg = e.args[0]
            # msg can be one of:
            #   raise MimirError("{0} - {1}".format(errorType, errorReason))
            #   raise MimirError(SSO_COOKIE_NAME + " was passed but is None")
            #   raise MimirError(meta.status['reason']) - If "stream = False" this could be used
            if "Access Forbidden" in msg:
                raise MimirAuthorizationError(msg)
            raise


    def get(self, *args, **kwargs):
        """
        Makes the request.
        Overrides Mimir.get()
        Will call Mimir_np.call_service() instead of Mimir.call_service()
        """
        self._logger.debug("Called Mimir_np.get")
        return self.call_service(path=Mimir._url(self, *args), params=kwargs)


    def grouper(self, **kwargs):
        """
        Instanciate an NP Groups object
        """

        if self.cpyKey and "cpyKey" not in kwargs:
            kwargs["cpyKey"] = self.cpyKey
        if self.groupId and "groupListStr" not in kwargs:
            kwargs["groupListStr"] = self.groupId
        return Groups(self, **kwargs)


    def chunker(self, **kwargs):
        """
        Instanciate a chunker object
        """

        if "scope" not in kwargs:
            kwargs["scope"] = "NP"
        if self.cpyKey:
            if "mimir_params" not in kwargs:
                kwargs["mimir_params"] = { 'cpyKey' : self.cpyKey }
            elif "cpyKey" not in kwargs["mimir_params"]:
                kwargs["mimir_params"]["cpyKey"] = self.cpyKey

        return Chunker(self, **kwargs)

    # Common interface - list companies the user has access to, but ignore Test accounts
    def get_my_companies(self, includeTest=False, username=None):
        """
        :param includeTest: All AS employees have access to 35+ Test accounts,
                            which clutter the list
        :param username:    If running an older Mimir client, this must be supplied
        :return:            list of companies user has access to (sorted by company name)
        """

        if username is None:
            if self._authenticated_user is None:
                self._logger.error(
                    "Called get_my_companies(), but cannot determine your username")
                return []
            else:
                username = self._authenticated_user

        companies = self.companies_entitled.get(userId=username)

        mycompanies = []
        for c in companies:
            if c.cpyType == "Test Account":
                if includeTest:
                    mycompanies.append(c)
            else:
                mycompanies.append(c)
        return mycompanies
