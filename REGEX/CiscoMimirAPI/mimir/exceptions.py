""" Exceptions used by Mimir """

# When Mimir responses with a failure, meta.status contains something like:
#    "code": "403",
#    "state": "FAIL",
#    "status": 1,
#    "type": "Forbidden"
#    "error": "Access Forbidden",
#    "reason": "Access Forbidden: You do not have access to the requested resource.",
#
# We attach these 6 attributes to the MimirException class,
# along with a generic "msg" attribute.


class MimirError(Exception):
    """ Base class for any Mimir exception
    """

    def __init__(self, *args, **kwargs):
        """Initialize MimirError with a status values and message."""
        if len(args) > 0:
            # In python2, e.message returned that arg[0] string.
            # In python3, e.message no longer exists by defaul
            self.message = args[0]

        status = kwargs.pop('status', None)
        if status:
            # Values returned in Mimir Meta.status block:
            self.code = int(status.pop('code', 0))
            self.state = status.pop('state', None)
            self.status = int(status.pop('status', 0))
            self.type = status.pop('type', None)
            self.error = status.pop('error', None)
            self.reason = status.pop('reason', None)
        else:
            self.code = 0
            self.state = None
            self.status = 0
            self.type = None
            self.error = None
            self.reason = None

        super(MimirError, self).__init__(*args, **kwargs)

    pass


class MimirAuthenticationError(MimirError):
    """ Response was a redirect to SSO """
    pass


class MimirAuthorizationError(MimirError):
    """ 403 Response from Mimir Service """
    pass


class MimirScopeNotFound(MimirError):
    """ 404 Response from Mimir Service """
    pass
