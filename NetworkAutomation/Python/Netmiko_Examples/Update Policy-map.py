####Author: Sudip Koirala, NCE, Network Automation Engineer
##############

import netmiko
import uuid
import os
import shutil
import time

# Input the ip addresses from the host file
# User prompted for Credentials

exceptions = (netmiko.ssh_exception.NetMikoTimeoutException, netmiko.ssh_exception.NetMikoAuthenticationException, netmiko.NetmikoTimeoutError, netmiko.NetmikoAuthError, IndexError)
print("Please enter the credentials to login to Router")
Username = raw_input("Enter your Username: ")
Password = raw_input("Enter your Password: ")

hostsparser = open("hosts.txt", 'r')
for host in hostsparser:
    try:
        ip = host.strip()

        net_connect = netmiko.ConnectHandler(device_type='cisco_xr', ip=ip , username=Username, password=Password, global_delay_factor=3)

        net_connect.send_command("term len 0")
        output = net_connect.send_command("show running-config")

        net_connect.send_command("clear configuration inconsistency")
        net_connect.send_command("admin clear configuration inconsistency")
        hostname = " "
        BeforeChangeRouterName = ip+"-"+time.strftime("%m-%d-%y")
        parser = open(BeforeChangeRouterName+".txt", 'w')
        parser.write(output)
        parser.close()
        dict1 = dict()

        parser = open(BeforeChangeRouterName+".txt", 'r')
        for i in parser:
            if "hostname" in i:
                hostname = i.split(" ")[1].strip()
                break
        parser.close()
        backup_file = hostname+"-policy-map-backup-config-"+time.strftime("%m-%d-%y")
        print("Successfully connected to: "+hostname)
        net_connect.send_command("copy running-config disk0:" +backup_file + "\n\r")
        print("Back-up config saved on disk0 as: "+backup_file)
        # Hostname with timestamp
        parser = open(BeforeChangeRouterName+".txt", 'r')
        commands = []
        policymap = " "
        classmap = " "

        print("Checking the Policy-maps that need to be changed for: "+hostname)
        for j in parser:

            if "policy-map" in j:
                for j in parser:


                    if (("policy-map" in j)&("end" not in j)):
                        policymap = j.strip()
                    elif (" class " in j):

                        classmap = j.strip()
                    elif (("police rate" in j)&("percent" not in j)):
                        if (("bps" in j)&("kbps" not in j)&("mbps" not in j)&("gbps" not in j)):
                            if ((int(j.split(" ")[4])/1024)<64):
                                commands.append(policymap)
                                commands.append(classmap)
                                # This command adds the police rate statement for 64kbps with the default burst rate and appends the peak-burst if present

                                commands.append("police rate 64 kbps "+j.split("bps")[1])
                                dict1[uuid.uuid4()] = commands


                                classmap = " "
                                commands = []
                        elif (("kbps" in j)&("mbps" not in j)&("gbps" not in j)):
                            if int(j.split(" ")[4]) < 64:
                                commands.append(policymap)
                                commands.append(classmap)

                                commands.append("police rate 64 kbps "+j.split("kbps")[1])
                                dict1[uuid.uuid4()] = commands

                                classmap = " "
                                commands = []
                        elif (("bps" not in j) & ("kbps" not in j) & ("mbps" in j)):
                                pass
                        elif (("bps" not in j) & ("kbps" not in j) & ("gbps" in j)):
                                pass

        parser.close()


        try:
            os.makedirs(hostname)
        except :
            print("Directory already exists, removing and creating it")
            shutil.rmtree(hostname)
            os.makedirs(hostname)
        shutil.copy2(BeforeChangeRouterName+".txt", ".//"+hostname)
        os.rename(".//"+hostname+"//"+BeforeChangeRouterName+".txt", ".//"+hostname+"//"+hostname+"-config-before-changed-"+time.strftime("%m-%d-%y")+".txt")
        os.remove(BeforeChangeRouterName+".txt")


        # Collect all the commands first and then commit them later
        #show them in a file about the before and after changes. Configuration rollback changes command to display the changed policy-maps ***
        #Take a back up of the running config in disk0:


        net_connect.config_mode()
        print("Configuring and committing the Policy-map changes for: "+hostname)
        for i in dict1:
            
            net_connect.send_config_set(dict1[i])


        net_connect.send_command("commit")

        net_connect.exit_config_mode()

        AfterChangedRouterName = hostname+"-config-after-changed"+time.strftime("%m-%d-%y")
        # config with the time stamp
        print("Collecting the last changed configuration for: " + hostname)

        parser = open(hostname+"//"+hostname+"-last-changed-config.txt", 'w')
        parser.write(net_connect.send_command("show configuration commit changes last 1"))
        parser.close()

        output = net_connect.send_command("show running-config")
        parser = open(hostname+"//"+AfterChangedRouterName+".txt", 'w')
        parser.write(output)
        parser.close()
        net_connect.disconnect()
        print("Disconnecting from: "+hostname)
        # Hostname, config changed successfully.
        # A router issue unreachable how it can handle other routers. Skip that device and go ahead with the other routers.


 
    except exceptions as e:
        print("******")
        print("Unable to execute script for: "+hostname)
        print(e)
        print("******")
hostsparser.close()
