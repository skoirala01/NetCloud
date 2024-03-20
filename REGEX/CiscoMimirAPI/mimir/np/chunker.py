
""" Get chunks of data using the Mimir API

    We may need to get data from NP in chunks that could overlap.
    The most obvious case is getting data from multiple NP Groups:
         data1 = mimir.call_service(scope="NP", service="device_details", params={'cpyKey': 105261, 'groupId': 87273})
         data2 = mimir.call_service(scope="NP", service="device_details", params={'cpyKey': 105261, 'groupId': 13297})
         data3 = mimir.call_service(scope="NP", service="device_details", params={'cpyKey': 105261, 'groupId': 59018})
    Since a device can exist in more than one group, we cannot simply append data1, data2 and data3.
    We need a method that avoids duplicates.

This module defines the 'Chunker' class

How To Use This Module
======================

INSTANCIATION
    mimir_np defines the method chunker() which instanciates a new Chunker object
    At instantiation, we need to define:
        - which Mimir {scope}/{service} we will be using
        - what field names define a unique row (key)
    
    # For the np.device_details table, the single field 'deviceId', can be used as a unique key
    device_details = np.chunker(scope="NP", service="device_details", keynames=[ deviceId ])

    # If there are specific parameters that should be passed to every query for a scope/service, they can be supplied during instanciation
    device_details = np.chunker(scope="NP", service="device_details", keynames=[ deviceId ], mimir_params={ "cpyKey" : company_id })
    # Of course, the mimir_np object will supply a default scope of "NP",
    # and the user may have specified a default cpyKey when mimir_np was instanciated
    # which could simply the above call as:
    device_details = np.chunker(service="device_details", keynames=[ deviceId ])

    # For the np.fn_details table, there is no single unique key for the table
    # (a physicalElementId can have multiple field notices against it).
    # In this case, 2 keys are needed to uniquely identify a row:
    fn_details = np.chunker(service="fn_details', keynames=[ 'fieldNoticeId', 'physicalElementId'])
    
METHODS
    .query()
        # We will call chunker multiple times, each time providing different filter params
        device_details.query(cpyKey=105261, groupId=87273)
        device_details.query(cpyKey=105261, groupId=13297)
        device_details.query(cpyKey=105261, groupId=59018)
        # Note, most NP tables can be filtered in many different ways
        device_details.query(cpyKey=105261, swType='IOS-XR')
        device_details.query(cpyKey=105261, swType='IOS', swVersion='15.1(4)M4')
        device_details.query(cpyKey=105261, swType='IOS-XE', swVersion='15.1(4)M4')
        # (If a default cpyKey was supplied during instanciation, it could be removed from the query. If one is supplied, it overrides the default)

        The above 6 .query() calls would get all devices where:
            groupId=87273
            or groupId=13297
            or groupId=59018
            or swType='IOS-XR'
            or (swType='IOS' and swVersion='15.1(4)M4)
            or (swType='IOS-XE' and swVersion='15.1(4)M4')

    .rows()
        # After we've made all the Mimir calls, we can iterate over every row in the resulting table
        for device in device_details.rows():
            print "Device Name={} and it is running {} version {}".format(device.deviceName, device.swType, device.swVersion)

    .get()
        # We can also access any single row directly by specifying the keyname(s) that define a unique row
        this_device = device.details.get( deviceId=93472 )
        this_fn = fn_details.get( fieldNoticeId=4038, physicalElementId=2827104 )

FUTURE
    .getrows()
        # If there were multiple keynames, an individual keyname may reference multiple rows
        # This will get all field notices that affect a particular part
        devices = fn_details.getrows( physicalElementId=2827104 )
        
        # Actually, we could filter based on any field - but the search is optomized if you use one of the keynames
        # (otherwise, we need to loop through every row to find the ones that match the requested field(s)
        
"""

class Chunker(object):
    def __init__(self, mimir_client, scope, service, keynames=None, mimir_params=None):
        """
        :param mimir_client: An authenticated Mimir client object
        :param scope:        Which Mimir Scope will be queried (ie. "NP")
        :param service:      Which Mimir Service will be queried (ie. "device_details")
        :param keynames:     List of fieldnames that form a unique key (to prevent duplicates)
                             If keynames==None, there will be no keys (just a big list, with possible duplicates)
        :param mimir_params: Optional list of parameters to pass to each Mimir call (like cache_days, etc...)
        """
        self.mimir = mimir_client
        self.scope = scope
        self.service = service
        self.keynames = keynames
        self.mimir_params=mimir_params

        if keynames is None:
            # All data is simply appended into a list
            self._data = []
        else:
            self._data = dict()
            # Keys will be sorted by field name (so it doesn't matter the order the user specifies)
            self.keynames.sort()

        self.last_query_duplicate_rows = None
        self.last_query_unique_rows = None
        self.last_query_total_rows = None

    def query(self, **kwargs):
        """
        :param kwargs: list of keyword arguments that get passed to the Mimir call
        """

        # Add the specified query params to any in self.mimir_params
        params = dict()
        if self.mimir_params:
            for opt in self.mimir_params.keys():
                params[opt] = self.mimir_params[opt]
        for opt in kwargs:
            params[opt] = kwargs[opt]

        # User may want to see how much duplication exists between the chunks
        self.last_query_duplicate_rows = 0
        self.last_query_unique_rows = 0
        self.last_query_total_rows = 0
        if self.keynames is not None:
            for row in self.mimir.call_service(scope=self.scope, service=self.service, params=params):
                self.last_query_total_rows += 1
                key = None
                for keyname in self.keynames:
                    this_key = row.__getattribute__(keyname)
                    if key is None:
                        key = str(this_key)
                    else:
                        # More than 1 key = a more complex string (keys seperated by commas)
                        key = key + "," + str(this_key)
                if key in self._data:
                    self.last_query_duplicate_rows += 1
                else:
                    self.last_query_unique_rows += 1
                self._data[key] = row
        else:
            # Result is an array
            rows = list(self.mimir.call_service(scope=self.scope, service=self.service, params=params))
            self._data.extend(rows)
            self.last_query_total_rows = len(rows)
            self.last_query_duplicate_rows = None
            self.last_query_unique_rows = None

    def rows(self):
        """
        Return all the rows of data
        """
        return self._data.values()

    def __iter__(self):
        """
        Iterator for all rows
        """
        for row in self.rows():
            yield row

    def __len__(self):
        return len(self._data)

    def get(self, **kwargs):
        """
        Get a single row, where the key exactly matches those passed in the function
        (Although, order of args is not important - they are sorted by key name)
        """

        params = kwargs
        keynames = sorted(params.keys())
        # Build the key string in exactly the same manner as we did in the query() method
        key = None
        for keyname in keynames:
            this_key = params[keyname]
            if key is None:
                key = str(this_key)
            else:
                # More than 1 key = a more complex string (keys seperated by commas)
                key = key + "," + str(this_key)
        if key in self._data:
            return self._data[key]
        else:
            return None

    def getrows(self, **kwargs):
        """
        Future
        """
        params = kwargs
        return None
