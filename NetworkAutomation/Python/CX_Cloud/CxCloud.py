'''
Written by Sudip, skoirala@cisco.com
'''

from datetime import date
import os
#Import the telemetry module for CX Catalog. If the required is not installed, install it
try:
    import aide
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'git+https://wwwin-github.cisco.com/AIDE/aide-python-agent.git'])
    import aide

def NSO_Commands(path, Dev_filename):

    with open(Dev_filename,'r') as file:
        cmd_file = open(f'''{path}/{str(0)}CmdFile.txt''','w')
        five_dev_list = []

        for i, line in enumerate(file, start=1):
            five_dev_list.append(line.strip())
            if i%5 == 0:

                cmd_file.write(f'''*******Monitor the logs from cdlogs*******\n''')
                cmd_file.write(f'''tail -f ncs-python-vm-ebh.log | grep -i "Completed"\n''')

                cmd_file.write(f'''\n*******Check the "Reload/Connect/Disconnect/Sync from" taken cared by Development Team *******\n''')

                cmd_file.write(f'''\n*******Create the new directory for each Set*******\n\n\n''')

                cmd_file.write(f'''\n\n*******ASR920 - Mannually confiure ARCHIVE directory*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''devices device {line.strip()}  live-status exec any "mkdir bootflash:ARCHIVE | prompts ENTER"\n''')

                cmd_file.write(f'''\n\n*******VersionCheck|ConfigCheck | From Exec Mode*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''show devices device {line.strip()} live-status version\n''')
                    cmd_file.write(f'''show running-config devices device {line.strip()} config | save {line.strip()}.running_config_{date.today()}.txt\n''')


                cmd_file.write(f'''\n\n*******Enable TraceLogs from ExecMode:*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''devices device {line.strip()} disconnect\n''')
                    cmd_file.write(f'''devices device {line.strip()} connect\n''')

                cmd_file.write(f'''\n\n*******WriteMemory and CopyConfig*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''devices device {line.strip()} live-status exec any "write memory"\n''')
                    cmd_file.write(f'''devices device {line.strip()} live-status exec any "copy running-config bootflash:Remediation_Config_{date.today()} | prompts ENTER"\n''')


                cmd_file.write(f'''\n\n*******Perform Sync from for all devices*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''devices device {line.strip()} sync-from\n''')

                cmd_file.write(f'''\n\n*******DryRun*******\n''')
                list_loop = ''
                for line in five_dev_list:
                    list_loop = list_loop + line + ' '
                cmd_file.write(f'''device-compliance remediation device [ {list_loop}] operation dry-run action-timeout 1200\n''')

                cmd_file.write(f'''\n\n*******Commit if No Errors*******\n''')
                list_loop = ''
                for line in five_dev_list:
                    list_loop = list_loop + line + ' '
                cmd_file.write(f'''device-compliance remediation device [ {list_loop}] operation commit action-timeout 1200 | save Batch{int(i/5 - 1)}.commit\n''')

                cmd_file.write(f'''\n\n*******Cleaning NSO Instances for the given device - Global Config Mode*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''no ebh csr {line.strip()} golden-config\n''')
                    cmd_file.write(f'''no ebh csr-type {line.strip()}\n''')
                    cmd_file.write(f'''commit no-networking\n''')

                cmd_file.write(f'''\n\n*******DryRun*******\n''')
                list_loop = ''
                for line in five_dev_list:
                    list_loop = list_loop + line + ' '
                cmd_file.write(f'''device-compliance remediation device [ {list_loop}] operation dry-run action-timeout 1200\n''')


                cmd_file.write(f'''\n\n*******Copy the Batch{int(i/5 - 1)} Trace Files*******\n''')
                for line in five_dev_list:
                    cmd_file.write(f'''cp /var/log/ncs/ned-cisco-ios-cli-6.92-{line}.trace /root/MW_02262024/\n''')


                cmd_file.close()
                cmd_file = open(f'''{path}/{str(int(i/5))}CmdFile.txt''','w')
                five_dev_list = []

    cmd_file.close()


def hr_savings(Device_Inventory):
    '''
    this is to calculate the saving hours
    :return:
    '''
    #Count the number of batch files
    file = os.listdir()
    batch_count = 0
    for list in file:
        if 'Cmd' in list:
            batch_count = batch_count + 1
    vzw_ebh_pid = "B89210"

    pid_answer = input(f"The script has completed successfully."
                       f"\nUsage and savings data is being logged to CX Catalog."
                       f"\nWas this script used for PID {vzw_ebh_pid}? [yes] ")
    savings_answer = input(f"Commands were created for total {batch_count} device and saved in each batch files."
                           f"\nDid this save you {batch_count*0.1} (5 mins per batch file) hours? [yes] ")
    if savings_answer.lower() == 'yes' or 'y':
        saving_total = batch_count * 0.1
        print(saving_total)


    try:
        #Submit the telemtry data.
        aide.submit_statistics(
            pid=vzw_ebh_pid,
            tool_id='65d9f27e60ef8cc8f44ca9b9',
            metadata={
                    "potential_savings": saving_total,  # Hours
                    "report_savings": True,},
        )
    except:
        print("There was an issue reporting usage and savings to CX Catalog.")
    return



def main():
    path = os.getcwd()
    ''' Please update the list of Devices in each time'''
    #Dev_filename = f'''{path}/ListofDevices.txt'''
    Device_Inventory = f'''ListofDevices.txt'''


    NSO_Commands(path, Device_Inventory)
    hr_savings(Device_Inventory)
    print('Done Reporting Data')

if __name__ == "__main__":
    main()
