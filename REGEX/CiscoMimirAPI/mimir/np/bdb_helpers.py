import re

SSO_COOKIE_NAME = 'ObSSOCookie'

def get_my_BDB_url(scriptFilename=None, env=None):
    """
    Figure out the BDB URL for this script
    From the BDB environment variable, we can learn the base webservice URL:
         u'webservice': u'https://scripts.cisco.com:443'
         (if env is not passed, just assume it is scripts.cisco.com)
    Calling script must pass "scriptFilename=__file__". We cannot figure
    that out (within this routine __file__ = the location of this library
         __file__ = 'bdb/tasks/{scriptName}/__init__'
    """

    webservice = "https://scripts.cisco.com"
    if env and "webservice" in env.session_info:
        m = re.search(r'(.+):', env.session_info["webservice"])
        if m:
            webservice = m.group(1)

    m = re.search(r'bdb/tasks/(.+)/__init__', scriptFilename)
    if m:
        return "{}/ui/use/{}".format(webservice, m.group(1))


def bdb_SSO_cookie(cookies):
    """
    Return the SSO cookies from the BDB env.cookies dict
    Return None if SSO is not enabled for this BDB script
    """

    if cookies is None or SSO_COOKIE_NAME not in cookies:
            return None
    return cookies[SSO_COOKIE_NAME]
