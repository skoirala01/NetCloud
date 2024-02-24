'''
Written by Sudip
'''

from datetime import date

five_dev_list = []
path = '/Users/skoirala/Documents/Customized/GIT_NETCLOUD/NetCloud/NetworkAutomation/Python/CX_Cloud'

''' Please update the list of Devices in each time'''
Dev_filename = f'''{path}/ListofDevices.txt'''


cmd_file = open(f'''{path}/{str(0)}CmdFile.txt''','w')

with open(Dev_filename,'r') as file:
    for i, line in enumerate(file, start=1):
        five_dev_list.append(line.strip())
        if i%5 == 0:

            cmd_file.write(f'''*******Mannually confiure ARCHIVE directory*******\n''')
            for line in five_dev_list:
                cmd_file.write(f'''devices device {line.strip()}  live-status exec any "mkdir bootflash:ARCHIVE | prompts ENTER"\n''')

            cmd_file.write(f'''\n\n*******VersionCheck|ConfigCheck | From Exec Mode*******\n''')
            for line in five_dev_list:
                cmd_file.write(f'''show devices device {line.strip()} live-status version\n''')
                cmd_file.write(f'''show running-config devices device {line.strip()} config | save SHPTLAWRT1A-P-CI-0509-01.running_config_{date.today()}.txt\n''')


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

            cmd_file.close()
            cmd_file = open(f'''{path}/{str(int(i/5))}CmdFile.txt''','w')
            five_dev_list = []

cmd_file.close()

