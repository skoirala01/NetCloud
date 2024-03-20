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

pattern = re.compile(r'(?=.*^hostname\s+.*EBH-5501)(?=.*^router bgp\s+\d+)', re.M)
matches = pattern.search(config)

if matches:
    print("Both lines are present in the configuration.")
else:
    print("One or both lines are missing from the configuration.")




'''
If you want to match a router configuration that includes both a specific hostname line containing "EBH-5501" and a "router bgp" line, and you want to verify that both lines are present in any order, you could use the following regex pattern:

(?=.*^hostname\s+.*EBH-5501)(?=.*^router bgp\s+\d+)
This pattern uses positive lookaheads to check for the presence of both strings anywhere in the text:

(?=.*^hostname\s+.*EBH-5501) is a positive lookahead that asserts that somewhere in the text there is a line that starts with "hostname" followed by any characters and "EBH-5501".
(?=.*^router bgp\s+\d+) is another positive lookahead that asserts that somewhere in the text there is a line that starts with "router bgp" followed by whitespace and one or more digits.
Here is a breakdown of the components:

(?=...) is a positive lookahead. It asserts that a particular regex can be matched following the current position, without consuming any characters.
.* matches any character (except for line terminators) zero or more times.
^ asserts the position at the start of a line (when used with the multiline flag m in some regex engines).
hostname\s+ matches the literal string "hostname" followed by one or more whitespace characters.
router bgp\s+ matches the literal string "router bgp" followed by one or more whitespace characters.
\d+ matches one or more digits.
The entire pattern needs to be used with the multiline flag m in regex engines that support it, which allows ^ to match the start of any line within the text, not just the start of the entire text.

'''
