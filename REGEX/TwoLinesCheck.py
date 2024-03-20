import re

config = """
hostname BC06-EBH-5501-01-B4B-01
taskgroup READ-ONLY-TGRP
task read fr
task read aaa

router bgp 65502
bgp router-id 172.30.10.41
bgp graceful-restart
ibgp policy out enforce-modifications
"""

hostname_pattern = re.compile(r'^hostname\s+.*EBH-5501', re.M)
router_bgp_pattern = re.compile(r'^router bgp\s+\d+', re.M)

hostname_match = hostname_pattern.search(config)
router_bgp_match = router_bgp_pattern.search(config)

if hostname_match and router_bgp_match:
    print("Both lines are present in the configuration.")
else:
    print("One or both lines are missing from the configuration.")
