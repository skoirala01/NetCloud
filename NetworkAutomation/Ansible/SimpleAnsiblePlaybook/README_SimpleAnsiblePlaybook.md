# NetCloud
Author:
Sudip Koirala - Network Consulting Engineer, Network Automation Engineer, Network Architect

Recording Link: https://cisco.webex.com/recordingservice/sites/cisco/recording/playback/14ecb1356282103abbaf0050568f9cbe

pw: Please Contact Author 


Lab Procedures:
==============

1. create the 'ansible.cfg' file and defined below:
`[defaults]
#some basic default values...
inventory      =  directory of the host files, e.g., /export-home/<yourusername>/Test_Ansible/hosts 
`

2. create the 'hosts' file and dump the below in it
`[asr9k]
9.0.2.39 ansible_host=9.0.2.39 ansible_network_os=iosxr 
`

3. create the directory vars, and create a new file main.yml file into this directiory and dump below (vars/main.yml): 

`ansible_ssh_pass: XXXXX
ansible_ssh_user: XXXXXXXXXXX 
`
 

4. create the 'playbook.yml' file and dump below.. Follow the proper indentation.
```---
- name: testing router commands
  hosts: asr9k
  gather_facts: no
  connection: network_cli
  vars:
    ansible_user: username
    ansible_password: password
    ansible_network_os: iosxr

  tasks:
    - name: connection and show interface commands
      iosxr_command:
        commands: show ip int br
      register: output
    - name: Display
      debug:
        msg: "{{output.stdout_lines}}"

```
5. play the yaml file like below
`ansible-playbook play.yml 
`
 

 


[Ansible Reference link](https://docs.ansible.com/ansible/latest/collections/cisco/ios/ios_l3_interfaces_module.html 
)
