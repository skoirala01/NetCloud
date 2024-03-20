from __future__ import unicode_literals, absolute_import
# -*- coding: utf-8 -*-
"""
Common routines when using Mimir to get data from NetProfiler.
Based on np_mimir_base.py

"""
__title__ = 'mimir.np'
__version__ = '0.0.1'
__author__ = 'John Bien <jbien@cisco.com>'

from .mimir_np import Mimir_np
from .output import sprint_companies, sprint_groups, print_my_companies, print_group_error
from .bdb_helpers import get_my_BDB_url, bdb_SSO_cookie
from .exceptions import *
