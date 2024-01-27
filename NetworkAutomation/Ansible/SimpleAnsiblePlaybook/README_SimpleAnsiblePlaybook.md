# NetCloud
Author:
Sudip Koirala - Network Consulting Engineer, Network Automation Engineer, Network Architect

Recording Link: https://cisco.webex.com/recordingservice/sites/cisco/recording/playback/14ecb1356282103abbaf0050568f9cbe
pw: Please Contact Author 

 

 

Lab Procedures:
==============

1. create the 'ansible.cfg' file and defined below:
[defaults]
# some basic default values... 

inventory      =  directory of the host files, e.g., /export-home/<yourusername>/Test_Ansible/hosts 

 

2. create the 'hosts' file and dump the below in it
[asr9k]
9.0.2.39 ansible_host=9.0.2.39 ansible_network_os=iosxr 

 

3. create the directory vars, and create a new file main.yml file into this directiory and dump below (vars/main.yml): 

ansible_ssh_pass: XXXXX
ansible_ssh_user: XXXXXXXXXXX 

 

4. create the 'playbook.yml' file and dump below.. Follow the proper indentation.
--- 

- name: Running-config Output 

  gather_facts: false 

  hosts: asr9k 

  vars_files: 

   - vars/main.yml 

 

  tasks: 

 

    - name: show run 

      connection: network_cli 

      ios_command: 

        commands:  show run router bgp 65002 

      register: output 

      #msg: "{{output.stdout_lines}}" 

      check_mode: yes 

   

    - name: Display 

      debug: 

        msg: "{{output.stdout_lines}}" 

 

5. play the yaml file like below 

ansible-playbook playbook.yml 

 

 

Ansible Reference link:
https://docs.ansible.com/ansible/latest/collections/cisco/ios/ios_l3_interfaces_module.html 
