from collections import OrderedDict


class MimirMeta(object):
    """
    Meta data returned from the last Mimir call
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

    def _replace(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])
        return self

    def _asdict(self):
        return OrderedDict(self.__dict__)

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
