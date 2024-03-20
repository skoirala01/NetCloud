from collections import OrderedDict


class MimirData(object):
    """
    A single data result object (aka. row of data) returned from the Mimir API
    """

    def __init__(self, data):
        """
        Instanciate a MimirData object by passing a dict object
        In mimir.py, this is a row of data returned from JSON
        """
        fields = []
        for key in data:
            fields.append(key)
            setattr(self, key, data[key])
        setattr(self, '_fields', tuple(fields))

    def __key(self):
        return tuple(v for k, v in sorted(self.__dict__.items()))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __str__(self):
        displayStr = None
        for name in self.__dict__:
            if displayStr is None:
                displayStr = "MimirData("
            else:
                displayStr += ", "
            displayStr += name + "=" + self.__getattribute__(name).__str__()
        return displayStr + ")"

    def __repr__(self):
        # Same as above, but the type of each item is revealed (ie. u'My Company', instead of just: My Company)
        displayStr = None
        for name in self.__dict__:
            if displayStr is None:
                displayStr = "MimirData("
            else:
                displayStr += ", "
            displayStr += name + "=" + self.__getattribute__(name).__repr__()
        return displayStr + ")"

    def _replace(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self

    def _asdict(self):
        return OrderedDict(self.__dict__)


def to_camel_case(snake_str):
    """
    Convert a_snake_str into ACamelCaseString
    (The first letter is capitalized)
    """
    components = snake_str.split('_')
    return "".join(x.title() for x in components)


def genMimirDataClass(scope, service):
    """
    Generate a MimirData class with a specific name
    Normally, we are passed just the service call name
    (adding scope is not really necessary, since most scripts only deal
    with a single scope)
    Examples:
       DeviceDetails
       HwEoxBulletins
       ProductRuleNaOids
    """
    className = to_camel_case(service)
    if not isinstance(className, str):
        # Python 2 - className will likely be unicode.  Must convert to type string
        className = str(className)
    NewClass = type(className, (MimirData, ), {"_scope": scope, "_service": service})
    return NewClass
