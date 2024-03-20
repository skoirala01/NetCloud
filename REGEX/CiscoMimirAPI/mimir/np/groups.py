from __future__ import unicode_literals, absolute_import, print_function

"""
Common routines when using Mimir to get data from NetProfiler.
Based on np_mimir_base.py

Idea is to have a persistent filter of groups the user is interested in
Alternately, user could just pass around a list of groups in their script

classes defined:
  Groups

Usage (method "grouper()" is defined in mimir_np.py)

Using the persistent group filter:
    groups = np.grouper(groupListStr="*Metro*,*DC*")

    print ("Company has {} total groups.  These are the Metro and DC groups:".format(
                                                   len(groups.get_groups(all=True))))
    for group in groups.get_groups():
        print ("Group: {}".format(group.groupName))
    # Changing filters does not cost anything (Mimir is not queried again)
    groups.filter_groups("*NY*,*LA*"):
    for group in groups.get_groups():
        print ("NY or LA Group: {}".format(group.groupName))


Using a more intuitive aproach (iterates over the filtered list)
    groups = np.grouper(groupListStr="*Metro*,*DC*")
    for group in groups:
        print ("Group: {}".format(group.groupName))

"""

import re
import fnmatch
from mimir import Mimir, MimirError, MimirAuthenticationError

class Groups(object):
    def __init__(self, mimirclient, cpyKey, groupListStr=None, beStrict=True, asFilterObject=False):
        """
        :param mimirclient:  Mimir client object with authenticated session
        :param cpyKey:       company key identifier
        :param groupListStr: Comma separated list of groups to limit (by groupId, groupName, or groupName wildcard)
        :param beStrict:     Used only if groupListStr is provided.
                                  True  = If any specified group is not found, return error.
                                  False = Only return error if no specified groups were found

        :return:             Groups object
        """

        # User may want to access these attributes
        self.groupListStr = groupListStr
        self.cpyKey = cpyKey

        self._logger = mimirclient._logger
        self._errLines = []
        self._filtered_groups = []
        self._all_np_groups = list(mimirclient.np.groups.get(cpyKey=cpyKey))
        self.filter_groups(groupListStr, beStrict)

        return

    def filter_groups(self, groupListStr=None, beStrict=True):
        """
        :param groupListStr: Comma separated list of groups to limit
        :param beStrict:     If any requested group cannot be found (or wildcard has no matches), return None
        :return:             A list of np_groups that match the filter
        """

        self.groupListStr = groupListStr
        # Reset the filter if one was already set
        # (A null list means no filter is set)
        self._filtered_groups = []
        if ((groupListStr is None) or (groupListStr == "")):
            # We just wanted to eliminate any existing filter...
            return

        # A list of all known Group Names for this NP Customer
        np_groupNames = []
        for group in self._all_np_groups:
            np_groupNames.append(group.groupName)

        group_list = groupListStr.split(',')
        # Will be extend-ing the list as we look at it, so safer to use an index than iterate over it
        i = 0
        while i < len(group_list):
            groupName = group_list[i];
            i = i + 1;
            # Remove trailing spaces (very confusing that NP allows this)
            groupName = groupName.strip()
            if ("*" in groupName) or ("?" in groupName):
                matchedGroupNames = self.find_matches(np_groupNames, groupName)
                if not matchedGroupNames:
                    errMsg = "Wildcard string \"{}\" does not match any defined groups for customer key {}".format(groupName, self.cpyKey)
                    self._logger.warning(errMsg)
                    self._errLines.append(errMsg)
                else:
                    #logger.debug("Group {}, matched the groups {}".format(groupName, ", ".join(matchedGroupNames)))
                    group_list.extend(matchedGroupNames)
                continue

            group = self.get_group(groupName)
            if group is not None:
                self._filtered_groups.append(group)
                #logger.debug("Group {}, ID {}".format(groupName, group.groupId))
            else:
                errMsg = "Group \"{}\" not found for customer key {}".format(groupName, self.cpyKey)
                self._logger.warning(errMsg)
                self._errLines.append(errMsg)

        return

    def get_group(self, groupToFind):
        """
        Get a single group (by exact name or groupId number)

        :param groupToFind:  groupId Number, or Name of the group to lookup
        :return:             group object, or None if not found
        """

        # See if we were supplied an integer (which most likely would be a groupId number)
        try:
            groupId = int(groupToFind)
        except:
            groupId = None
            # Remove trailing spaces
            groupToFind = groupToFind.strip()

        for group in self._all_np_groups:
            groupName = group.groupName.strip()
            if groupName == groupToFind:
                return group
            elif groupId and (group.groupId == groupId):
                return group
        # Fail
        return None

    def all(self):
        """
        Return all known NP Groups
        """
        return self._all_np_groups

    def filtered(self):
        """
        Return all filtered NP Groups
        """
        return self._filtered_groups

    def __len__(self):
        return len(self._filtered_groups)

    def __iter__(self):
        """
        Iterating over the groups
        If groupListStr was None, list all groups
        Otherwise, only list the filtered groups
        """
        if self.groupListStr is None:
            groupList = self.all()
        else:
            groupList = self.filtered()

        for group in groupList:
            yield group

    def __str__(self):
        if self.groupListStr is None:
            return "There are {0} Groups in NP for customerId {1}".format(
                len(self._all_np_groups),
                self.cpyKey)
        else:
            return "There are {0} Groups in NP for customerId {1}. {2} matched filter: \"{3}\"".format(
                len(self._all_np_groups),
                self.cpyKey,
                len(self._filtered_groups),
                self.groupListStr)

    def err(self):
        """
        Return the error lines that may have been set when we queried NP
        """
        if self._errLines:
            return self._errLines
        else:
            return None


    def find_matches (self, searchList, matchString):
        """
        Return the entries in searchList that match the glob matchString
        This differs from fnmatch.filter() in that I want to make sure it is always case insensitive
        fnmatch.trans will remove any trailing spaces from the matched string
        """
        result = []
        matchRegex = re.compile(fnmatch.translate(matchString), re.IGNORECASE)
        for itemStr in searchList:
            if matchRegex.match(itemStr):
                result.append(itemStr)
        return result
