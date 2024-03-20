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

pattern = re.compile(r'(?s)hostname\s+.*?EBH-5501.*?router bgp\s+\d+')
matches = pattern.findall(config)

for match in matches:
    print(match)
