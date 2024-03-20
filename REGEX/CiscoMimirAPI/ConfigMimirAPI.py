import os
import sys
import re
from datetime import datetime, timedelta
from os.path import isfile
from mimir import Mimir, MimirAuthenticationError

# Import the telemetry module for CX Catalog. If the required module is not installed, install it.

try:
    from ciscoconfparse import CiscoConfParse
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ciscoconfparse'])
    import aide

def np_auth():
    # Instantiate a new Mimir client object
    m = Mimir()
    # Authenticate with NP using user credentials.
    try:
        m.authenticate()
    except MimirAuthenticationError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(2)
    return m


def get_np(m, host, today, last_week):
    # Network Profiler Company ID for Verizon Wireless
    company_id = "94617"

    device_details = m.np.device_details.get(cpyKey=company_id, deviceName=host)
    if device_details:
        try:
            device_details_entry = next(device_details)
            device_config_time = datetime.strptime(device_details_entry.configTime, '%Y-%m-%dT%H:%M:%S')
            device_date = device_config_time.date()
            if not (last_week <= device_date <= today):
                # Config was NOT pulled by NP within the last week.
                print(f"##### {host} config file was in NP, but it's more than 1 week old. Save the config file manually and then re-run the script.")
                return "old"
        except:
            config_info = ""
            return config_info

    # Get the standard running config for the device from NP.
    device_np = m.np.devices.get(cpyKey=company_id, deviceName=host)
    # Check if the NP response contains a config.
    if device_np:
        try:
            device_info = next(device_np)
        except:
            config_info = ""
            return config_info
        config_np = m.np.config.get(cpyKey=company_id, deviceId=device_info.deviceId, configType='STANDARD RUNNING')
        try:
            config_info = next(config_np)
            return config_info.rawData
        except:
            config_info = ""
            return config_info

def hostname_routerid_check(hostname, runfile):
    #hostname_pattern = re.compile(r'^hostname\s+.*-S-', re.M)
    #router_bgp_pattern = re.compile(r'^router bgp\s+\d+', re.M)
    #hostname_match = runfile.find_objects(r'^hostname')
    #hostname_match = runfile.find_objects(r'\bhostname .*-S-.*\b')
    hostname_match = runfile.find_lines(r'^hostname\s+.*-S-')
    hostname_match = runfile.find_lines(r'^hostname\s+.*-P-')
    router_bgp_match = runfile.find_objects(r'^router bgp\s+\d+')
    print(router_bgp_match)

    if hostname_match and router_bgp_match:
        print(f"{hostname} - hostname and router id found in running config.")
        return hostname
    else:
        print(f"{hostname} - does not have router id.")
        return

'''
    eula_cfg_line = [x.text for x in runfile.find_objects(r"^license accept end user agreement")]
    if not eula_cfg_line:
        print(f"{hostname} - Missing EULA in running config.")
        return hostname
    else:
        print(f"{hostname} - All good for EULA.")
        return
'''

def save_hostname_routerid(hostname_routerid):
    # Create a file that lists all the devices found to match the required condition.
    with open("hostname_routerid.txt", 'w') as file:
        if hostname_routerid:
            for host in hostname_routerid:
                file.write(f"{host}\n")
        else:
            file.write(f"")
    return


def main():
    # Get the list of device hostnames.
    path = os.getcwd()
    try:
        os.mkdir((path+'/NP_DATA/'))
    except:
        print('folder is already there')
    filename = path+"/CiscoMimirAPI/hostlist.txt"
    print(filename)
    try:
        print(0)
        with open(filename, 'rt') as file:
            hostname_list = [line.rstrip() for line in file]
    except:
        print("There was an issue opening 'hostlist.txt'. Make sure this file is in the same directory as this script.")
        sys.exit()

    cisco_device_count = len(hostname_list)
    np_directory_name = os.path.join(os.getcwd(), "NP_DATA")


    host_missing_config = []
    for host in hostname_list:
        # Create the file path used to save the old config.
        np_file_name = os.path.join(np_directory_name, f"{host}.cfg")
        # If the file isn't in the NP_DATA directory, add it to the host_missing_config list.
        if not os.path.isfile(np_file_name):
            host_missing_config.append(host)

    if host_missing_config:
        for host in host_missing_config:
            print(f"{host} config file not in NP_DATA directory. NP will be used.")
        print()
        # Authenticate to NP once.
        auth = np_auth()
        today = datetime.today().date()
        last_week = today - timedelta(days=7)
        # Retrieve the running config from NP for each device using their Old Hostname.
        for host in host_missing_config:
            # Create the file path used to save the old config.
            np_file_name = os.path.join(np_directory_name, f"{host}.cfg")
            print(f"Retrieving {host} config file from NP - Started")
            # Get config from NP.
            conf_contents = get_np(auth, host, today, last_week)
            # If the device isn't in NP, don't make a new file.
            if conf_contents == "":
                print(f"{host} config file not found in NP. Save the config file manually and then re-run the script.")
                print(f"Retrieving {host} config file from NP - Completed")
            elif conf_contents == "old":
                continue
            else:
                with open(np_file_name, 'w') as fd:
                    fd.write(conf_contents)
                print(f"Retrieving {host} config file from NP - Completed")
    else:
        # If the files already exist, inform the user that the local files will be used and not updated by NP.
        print(f"Current config files already exists locally for each host. NP will not be used.")

    print()

    if [x for x in hostname_list if not isfile(os.path.join(np_directory_name, f"{x}.cfg"))]:
        for host in [x for x in hostname_list if not isfile(os.path.join(np_directory_name, f"{x}.cfg"))]:
            print(f"{host} config file not found locally. Save this to the NP_DATA directory with file extension .cfg and then rerun the script.")
        print()
        print("Device configs will not be parsed until you save the above files and re-run the script.")
        sys.exit()
    else:
        hostname_routerid = []

        print(f"Parsing started.")
        # Check the config for each device in the list.
        for hostname in hostname_list:
            np_file_name = os.path.join(np_directory_name, f"{hostname}.cfg")
            runfile = CiscoConfParse(np_file_name, syntax='ios')

            if hostname_routerid_check(hostname, runfile):
                hostname_routerid.append(hostname)
        print(f"Parsing completed.\n")
        print("Saving list of devices from EULA check.")
        save_hostname_routerid(hostname_routerid)


if __name__ == "__main__":
    main()
