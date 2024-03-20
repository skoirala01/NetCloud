# -*- coding: utf-8 -*-
"""
Common routines for generating text that can be displayed to the end user
"""

try:
    import bdblib
    from bdblib.exceptions import BDBTaskError
    MODE = 'bdb'
except:
    MODE = 'standalone'

def sprint_companies(companies,
                     doSort=True,
                     html=True,
                     urlBase=None,
                     urlCpyKeyParamName=None,
                     urlParamsOther=""):
    """
    Given a list of NP Companies (i.e. returned from np.companies_entitled.get()),
    return a string that can be presented to the end user.

      companies          - List of NP Companies (i.e. np.companies_entitled.get())
      doSort             - By default, table will be sorted based on company name
      html               - By default, HTML output will be returned
      urlBase            - base URL for this script
      urlCpyKeyParamName - URI parameter name that is used to identify the cpyKey
      urlParamsOther     - Any other data you which to attach to the URL (ie. other params)

    If html is True, then cpyKey can optionally be turned into a hyperlink if
    both of the url parameters are also supplied (urlBase & urlParamName)
    Company Key Hyperlinks will look something like:
        {urlBase}?{urlParamName}=382742
    or:
        https://scripts.cisco.com/ui/use/npTestScript?companyKey=382742
    In this example, urlParamName="companyKey", which is the BDB Input field
    name that end-users must supply (also found in the "def task(...)" line of the BDB script)

    If there are other parameters you need to attach to the URL, use urlParamsOther,
    which will appear directly after the fully formed URL + "&".
    Example:
       urlParamsOther="osType=IOS&debug=True"
    Generates a URL like:
       https://scripts.cisco.com/ui/use/npTestScript?companyKey=382742&osType=IOS&debug=True
    
    """

    text = ""
    # BDB uses the Atlantic UI (CSS styles)
    #   http://swtg-rtp-dev-7/styleguide/index.html
    #             <tr class="danger">
    if html:
        text = """
        <table class="table table--bordered table--loose">
            <thead>
                <tr>
                    <th>Company Key</th>
                    <th>Company Name</th>
                </tr>
            </thead>
        <tbody>
        """

    # User could have passed us a list
    # Or they may have passed the Mimir iterator instead (inline sort will not work in that case)
    if doSort:
        sorted_companies = sorted(companies, key=lambda x: x.cpyName.lower())
        companies = sorted_companies

    for c in companies:
        if html:
            cpyKeyField=c.cpyKey
            if (urlBase and urlCpyKeyParamName):
                paramsOther = urlParamsOther
                if len(urlParamsOther) and urlParamsOther != '&':
                    paramsOther =  "&" + urlParamsOther
                cpyKeyField = '<a href="{0}?{1}={2}{3}"> {4} </a>'.format(
                    urlBase, urlCpyKeyParamName, c.cpyKey, paramsOther, c.cpyKey)
            text += '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(cpyKeyField, c.cpyName)
        else:
            text += "        {:>7} - {}\n".format(c.cpyKey, c.cpyName)

    if html:
        text += '</tbody></table>'

    return text

def sprint_groups(groups,
                  doSort=True,
                  html=True,
                  urlBase=None,
                  urlGroupParamName=None,
                  urlParamsOther=""):
    """
    Given a list of NP Groups (i.e. returned from np.grouper() or np.groups.get(cpyKey=cpyKey)),
    return a string that can be presented to the end user.
        
      groups            - List of NP Groups (i.e. np.grouper())
      doSort            - By default, table will be sorted based on group name
      html              - By default, HTML output will be returned
      urlBase           - base URL for this script
      urlGroupParamName - URI parameter name that is used to identify the groupId
      urlParamsOther     - Any other data you which to attach to the URL (ie. "cpyKey=84723")

    If html is True, then groupId can optionally be turned into a hyperlink if
    both of the url parameters are also supplied (urlBase & urlGroupParamName)
    Group ID Hyperlinks will look something like:
        {urlBase}?{urlGroupParamName}=382742
    or:
        https://scripts.cisco.com/ui/use/npTestScript?groupidField=382742

    You will most certainly also want to include the company key in urlParamsOther
    Example:
       urlParamsOther="companyKeyField=383854"
    Generates a URL like:
       https://scripts.cisco.com/ui/use/npTestScript?groupField=2742&companyKeyField=383854
    
    """
    text = ""
    # BDB uses the Atlantic UI (CSS styles)
    #   http://swtg-rtp-dev-7/styleguide/index.html
    #             <tr class="danger">
    if html:
        text = """
        <table class="table table--bordered table--loose">
            <thead>
                <tr>
                    <th>Group ID</th>
                    <th>Group Name</th>
                </tr>
            </thead>
        <tbody>
        """

    if doSort:
        sorted_groups = sorted(groups, key=lambda x: x.groupName.lower())
        groups = sorted_groups

    for g in groups:
        if html:
            groupIdField=g.groupId
            if (urlBase and urlGroupParamName):
                paramsOther = urlParamsOther
                if len(urlParamsOther) and urlParamsOther != '&':
                    paramsOther =  "&" + urlParamsOther
                groupIdField = '<a href="{0}?{1}={2}{3}"> {4} </a>'.format(
                    urlBase, urlGroupParamName, g.groupId, paramsOther, g.groupId)
            text += '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(groupIdField, g.groupName)
        else:
            text += "        {:>7} - {}\n".format(g.groupId, g.groupName)

    if html:
        text += '</tbody></table>'

    return text


def print_group_error(groups, cpyKey, cpyName,
                      bdbTaskOutput=None,
                      bdbUrlBase=None,
                      paramName_cpyKey=None,
                      paramName_groupList=None):
    """
    User selected a groupList that was an error (probably did not return any groupIds)
    Show the user what groups do exist in a format suitable for either BDB or CLI
    """
    if len(groups.all()) == 0:
        genOutput(bdbTaskOutput,
                  "Customer key {} ({}) has no NetProfiler Groups defined".format(
                      cpyKey, cpyName),
                  severity="Error")
        return

    # Generate the Table of available Groups for this customer
    if bdbTaskOutput:
        urlParamsOther = "{}={}".format(paramName_cpyKey, cpyKey)
        groups_table = sprint_groups(groups.all(),
                                     html=True,
                                     urlBase=bdbUrlBase,
                                     urlGroupParamName=paramName_groupList,
                                     urlParamsOther=urlParamsOther)
    else:
        groups_table = sprint_groups(groups.all(), html=False)

    if groups.groupListStr == "0":
        # Group ID of 0 is a way of asking to list authorized companies (not an error)
        # Just print the table, and return (no error messages)
        genOutput(bdbTaskOutput, groups_table)
        return

    genOutput(bdbTaskOutput,
              "Error: Groups \"{}\" (for {}) not found".format(groups.groupListStr, cpyName),
              severity="Error")

    if groups.err():
        # This will the list of errors (which groups could not be found)
        for errStr in groups.err():
            genOutput(bdbTaskOutput, errStr, severity="Error")

    genOutput(bdbTaskOutput,
              "Customer {} has {} NetProfiler Groups defined:".format(
                  cpyName, len(groups.all())),
              severity="Notice")
    genOutput(bdbTaskOutput, groups_table)

def genOutput(bdbTaskOutput=None, message="", severity=None):
    if bdbTaskOutput:
        bdbTaskOutput.append(bdbHighlightStr(message, severity))
    else:
        print(message)

def bdbHighlightStr(message, severity=None):
    if severity == "Error":
        return bdblib.HTML("<font color=red><b>{}<b></font>".format(message))
    elif severity == "Notice":
        return bdblib.HTML("<font color=blue><b>{}<b></font>".format(message))
        #return bdblib.HTML("<font color=\"blue\"><b>{}<b></font>".format(message))
    else:
        return bdblib.HTML(message)

def print_my_companies(mycompanies,
                       username,
                       bdbTaskOutput=None,
                       bdbUrlBase=None,
                       bdbUrlParamName=None):
    """
    Neatly print the list of companies a user has access to
    If bdbTaskOutput is set, HTML ouput is appended to that object
    Otherwise, logger.info() is used to generate the output
    """
    # mycompanies=get_my_companies(m, username, includeTest=False)

    if bdbTaskOutput:
        bdbTaskOutput.append(
            bdblib.HTML(
                "<b>UserId {} currently has access to the following NP accounts:</b><br>".format(
                    username)))

        bdbTaskOutput.append(
            bdblib.HTML(sprint_companies(mycompanies,
                                         html=True,
                                         urlBase=bdbUrlBase,
                                         urlCpyKeyParamName=bdbUrlParamName)))
    else:
        print("UserId {} currently has access to the following NP accounts:".format(username))
        print(sprint_companies(mycompanies, html=False))
