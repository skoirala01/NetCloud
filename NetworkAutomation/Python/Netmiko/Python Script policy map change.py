####Author: Sudip Koirala, NCE, Network Automation Engineer
##############
import netmiko
import time
import os
import uuid
import shutil
import getpass

#from netmiko import ConnectHandler
exceptions = (netmiko.ssh_exception.NetMikoTimeoutException, netmiko.ssh_exception.NetMikoAuthenticationException, netmiko.NetmikoTimeoutError, netmiko.NetmikoAuthError, IndexError)

working_dir = os.getcwd() + '/'
script_dir = os.path.dirname(os.path.abspath(__file__)) + '/'

Ip = raw_input("Please Enter ip address of the device: ")
Username = raw_input("Enter your Username: ")
Password = getpass.getpass("Password:: ")

hostname = " "
try:
    ####################################################
    ##########logging to router#########################
    net_connect = netmiko.ConnectHandler(device_type='cisco_xr', ip=Ip , username=Username, password=Password, global_delay_factor=1)
    ip = Ip
    net_connect.send_command("term len 0\n")
    output = net_connect.send_command("show running-config\n")
    net_connect.send_command("clear configuration inconsistency\n")
    net_connect.send_command("admin clear configuration inconsistency\n")
    original_config = ip+"-"+time.strftime("%m-%d-%y")
    
    parser = open(working_dir + original_config+".txt", 'w')
    parser.write(output)
    parser.close()
    
    parser = open(working_dir + original_config+".txt", 'r')
    dict1 = dict()
    for i in parser:
        if "hostname" in i:##Find the hostname from running config file
            hostname = i.split(" ")[1].strip()
            break
    parser.close()
    
    
    
    print("Successfully connected to: "+hostname)
    backup_file = hostname+"-policy-map-backup-config-"+time.strftime("%m-%d-%y" + '.txt')##backup in disk0:
    net_connect.config_mode()
    net_connect.send_config_set('do copy running-config disk0:' + backup_file +"\n\r")
    print("Successfully backed up config file to: "+hostname)
    #print("Configuring and committing the Policy-map changes for: "+hostname)    
    ###########################################################
    ############Reading and loading new policy map in the router#################
    dictnew_PM = ""
    NewPolicyMap = open(script_dir + "NewPolicyMapConfig-DS0-DS1.txt", 'r')

    dictnew_PM = dict()
    i=0
    for newPM in NewPolicyMap:
        dictnew_PM[i] = newPM.strip()
        i = i + 1
    print("Pushing New Policy MAP configs for both DS0 and DS1 circuits to: "+hostname)      
    for i in range(len(dictnew_PM)):
        print net_connect.send_config_set(dictnew_PM[i])
        time.sleep(0.01)
   


 
    ############Reading Data for policy map only#####################################
    dictold_PM = ""
    dictchange_PM_DS1 = ""
    dictchange_PM_DS0 = ""
    OldPolicyMap_DS0_DS1 = ""
    OldPolicyMap_DS0_DS1 = open(script_dir + "OldPolicyMap-DS0-DS1.txt", 'r')
    NewPolicyMap_DS1 = open(script_dir + "NewPolicyMap-DS1.txt", 'r')
    NewPolicyMap_DS0 = open(script_dir + "NewPolicyMap-DS0.txt", 'r')
    dictold_PM = dict()
    dictchange_PM_DS1 = dict()
    dictchange_PM_DS0 = dict()
    i=0
    for oldPolicyMap in OldPolicyMap_DS0_DS1:
        dictold_PM[i] = oldPolicyMap
        i = i + 1
    i = 0
    for changeToPolicyMap in NewPolicyMap_DS1:
        dictchange_PM_DS1[i] = changeToPolicyMap
        i = i+1
    i = 0
    for changeToPolicyMap in NewPolicyMap_DS0:
        dictchange_PM_DS0[i] = changeToPolicyMap
        i = i+1
    OldPolicyMap_DS0_DS1.close()
    NewPolicyMap_DS1.close()
    NewPolicyMap_DS0.close()
    ############################################################  
    ########################################################
    ##  Find the controller that has speed 56 for DS1 circuit##############
    PresentConfig = open(working_dir + original_config+".txt", 'r')
    tdminterface_DS1 = []
    tdminterface_DS0 = []
    controller = 'false'
    speedtest = 'false'
    DS0 = 'false'
    DS1 = 'false'
    channel_group = ''

    for config in PresentConfig:
        
        if ("controller T" in config) and (config[0] != ' '):#check controller interface
            controller = 'true'
            InterfaceNumber = config.split()[2]
        elif ("channel-group" in config):
            channel_group = config.split()[1]
            
        elif (('speed' in config) and (controller == 'true') and (config[1] == ' ')):
            speed64 = int(config.split()[1])
            if speed64 == 56:
                speedtest = 'true'
        elif (('timeslots 1-24' in config) and (controller == 'true') and (config[1] == ' ') and (speedtest == 'true')):
            tdminterface_DS1.append(InterfaceNumber + ':' + channel_group)
            DS1 = 'true'
            
        elif (('timeslots 1-24' not in config) and ('timeslots' in config) and (controller == 'true') and (config[1] == ' ') and (speedtest == 'true')):
            tdminterface_DS0.append(InterfaceNumber + ':' + channel_group)
            DS0 = 'true'
            
        elif(config[0] == '!'):
            DS0 = 'false'
            DS1 = 'false'
            controller = 'false'
            speedtest = 'false'
            channel_group = ''
                
    PresentConfig.close()
    #####################################################################
    ##if speed is 56, then update the policy map under the port interface
    dict_ServicePolicy = ""
    dict_ServicePolicy = dict()
    PushInterfaceConfig = []
    interface = ""
    pvc = ""
    ServicePolicyTest = 'false'
    servicepolicy = []
    intcount = 1
    
    PresentConfig = open(working_dir + original_config +".txt", 'r')
    CheckPushInterfaceConfig_DS1 = 'false'
    CheckPushInterfaceConfig_DS0 = 'true'
    for config in PresentConfig:
        if (("interface " in config) and (config[0] != ' ')):#check the interface
            for i in range (len(tdminterface_DS0)):
                if tdminterface_DS0[i] in config:
                    interface = config
                    CheckPushInterfaceConfig_DS0 = 'true'
                    ServicePolicyTest = 'false'
                    tdminterface_DS0[i]
                    break
                else:
                    CheckPushInterfaceConfig_DS0 = 'false'

        
        if (("interface " in config) and (config[0] != ' ')):#check the interface
            for i in range (len(tdminterface_DS1)):
                if tdminterface_DS1[i] in config:
                    interface = config
                    CheckPushInterfaceConfig_DS1 = 'true'
                    ServicePolicyTest = 'false'
                    tdminterface_DS1[i]
                    break
                else:
                    CheckPushInterfaceConfig_DS1 = 'false'

        elif (CheckPushInterfaceConfig_DS0 == 'true' and config[0] == ' '):#check config under interface with space in indent
            if (config.split()[0] == 'pvc'):#check pvc
                pvc = config
            elif('service-policy ' in config):#check service policy under the port interface
                for i in range(len(dictold_PM)):#compare service policy with old and new policy                
                    if(config.split()[2] == dictold_PM[i].split()[1]):#compare with old policy and update to change
                        servicepolicy.append('no' + config)
                        servicepolicy.append(config.replace(config.split()[2], dictchange_PM_DS0[i].split()[1]))
                        ServicePolicyTest = 'true'


        elif (CheckPushInterfaceConfig_DS1 == 'true' and config[0] == ' '):#check config under interface with space in indent
            if (config.split()[0] == 'pvc'):#check pvc
                pvc = config
            elif('service-policy ' in config):#check service policy under the port interface
                for i in range(len(dictold_PM)):#compare service policy with old and new policy                
                    if(config.split()[2] == dictold_PM[i].split()[1]):#compare with old policy and update to change
                        servicepolicy.append('no' + config)
                        servicepolicy.append(config.replace(config.split()[2], dictchange_PM_DS1[i].split()[1]))
                        ServicePolicyTest = 'true'

                        
        ##done with checking port interface, pvc and service policy
        ##Now collect data of interace, pvc and policy
        elif(ServicePolicyTest == 'true'):#if service policy then collect it, otherwise skip it
            PushInterfaceConfig.append(interface)
            PushInterfaceConfig.append(pvc)
            
            for i in range (len(servicepolicy)):
                PushInterfaceConfig.append(servicepolicy[i])
                
            dict_ServicePolicy[intcount] = PushInterfaceConfig
            dict_ServicePolicy[intcount]
            intcount = intcount + 1
            interface = ""
            pvc = ""
            servicepolicy = ""
            servicepolicy = []
            ServicePolicyTest = 'false'
            PushInterfaceConfig = []
        elif(ServicePolicyTest == 'false'):#if no servicepolicy need to update then reset it.
            interface = ""
            pvc = ""
            servicepolicy = ""
            servicepolicy = []
            ServicePolicyTest = 'false'
            PushInterfaceConfig = []
            CheckPushInterfaceConfig_DS1 = 'false'
            CheckPushInterfaceConfig_DS0 = 'false'
    PresentConfig.close()
    #####################################################################
    ##Find the policy map that has speed less than 64kbps, make it 64kbps
    commands = []
    PolicyMap = " "
    ClassMap = " "
    dict_policerate = dict()
    intcount = 1
    PresentConfig = open(working_dir + original_config +".txt", 'r')
    for config in PresentConfig:
        ##check polciy map and update policy map, service policy and police rate.
        if ("policy-map " in config) and (config[0] != ' '):# & ("end" not in config)):
            PolicyMap = config#extract the line without white spaces before and after the lines
        elif (" class " in config):
                    ClassMap = config 
        elif (("police rate" in config) and ("percent" not in config)):
            if (("bps" in config)&("kbps" not in config)&("mbps" not in config)&("gbps" not in config)):
                
                if ((int(config.split(" ")[4])/1024)<64):
                    
                    commands.append(PolicyMap)
                    commands.append(ClassMap)
                    # This command adds the police rate statement for 64kbps with the default burst rate and appends the peak-burst if present
                    commands.append("  police rate 64 kbps "+config.split("bps")[1] + '\n')
                    commands.append("root\n ! \n")
                    dict_policerate[uuid.uuid4()] = commands
    
    
                    ClassMap = " "
                    commands = []
            elif (("kbps" in config)&("mbps" not in config)&("gbps" not in config)):
                if int(config.split(" ")[4]) < 70:
                    commands.append(PolicyMap)
                    commands.append(ClassMap)
    
                    commands.append("  police rate 70 kbps "+config.split("kbps")[1])
                    commands.append("root\n ! \n")
                    dict_policerate[uuid.uuid4()] = commands
    #                print commands
                    ClassMap = " "
                    commands = []
            elif (("bps" not in config) & ("kbps" not in config) & ("mbps" in config)):
                    pass
            elif (("bps" not in config) & ("kbps" not in config) & ("gbps" in config)):
                    pass
    
         
    PresentConfig.close()
    pushintconfig = []
    PoliceRateMapUpdateFileName = "ConfigPushedin"+hostname+"-"+time.strftime("%m-%d-%y")+".txt"
    PoliceRateMapUpdate = open(working_dir + PoliceRateMapUpdateFileName, 'w')
    print("Updating policymap under port interface and backing up log file")
    for intcount in dict_ServicePolicy:
        pushintconfig = dict_ServicePolicy[intcount]
        for i in range(len(pushintconfig)):
            print net_connect.send_config_set(pushintconfig[i])
            PoliceRateMapUpdate.write((pushintconfig[i]))
    
    
    PMupdate = []
    for intcount in dict_policerate:
        PMupdate = dict_policerate[intcount]
        for i in range(len(PMupdate)):
            print net_connect.send_config_set(PMupdate[i])
            PoliceRateMapUpdate.write((PMupdate[i]))
    
    PoliceRateMapUpdate.close()
     
        
    #########################################################################3########
    print "\n\n\n\nCommitting 2nd time"
    print net_connect.send_command("commit\n")
    #print net_connect.send_command("clear configuration inconsistency\n")
    #print net_connect.send_command("admin clear configuration inconsistency\n")
    net_connect.exit_config_mode()
    print("config is commited and disconnecting from router")
    
    
    
    try:
        log_dir = working_dir + hostname + '/'
        os.makedirs(log_dir)
    except:
        print("Directory already exists, removing and creating it")
        shutil.rmtree(log_dir)
        os.makedirs(log_dir)
        print log_dir
    shutil.copy2((working_dir + PoliceRateMapUpdateFileName), log_dir)
    shutil.copy2(working_dir + original_config+".txt", log_dir)
    os.rename(log_dir + original_config+".txt", log_dir + hostname+"-config-before-changed-"+time.strftime("%m-%d-%y")+".txt")
    os.remove(working_dir + original_config+".txt")
    os.remove(working_dir + PoliceRateMapUpdateFileName)
    
    
    RouterHostName = hostname+"-config-after-changed-"+time.strftime("%m-%d-%y")
    print("Collecting the last changed configuration for: " + hostname)
    
    
    parser = open(log_dir + hostname+"-last-changed-config-"+time.strftime("%m-%d-%y")+".txt", 'w')
    parser.write(net_connect.send_command("show configuration commit changes last 1"))
    parser.close()
    
    output = net_connect.send_command("show running-config")
    parser = open(log_dir + RouterHostName +".txt", 'w')
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
