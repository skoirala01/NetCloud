# NetCloud

# NSOCommandsToLoginAndUpdateConfigurationsToProductionRouters
- This python script is used to generate the NSO commands for the given list of the devices saved in a text file ListofDevices.txt
- The commands are used to run in the NSO terminal
  - NSO can be logged in Linux_Host_Machine with command 'Linux_VM$ ssh root@<NSO_Ipv6>'
  - Go to the NSO CLI admin mode using 'ncs_cli -Cu admin'

# Prerequisite
- NSO Development team has already updated the NED Drivers and Backup Configs
- Download the Python3 software from the https://www.python.org/downloads/

# Procedures
- Clone or download this Python Script in your computer (local machine)
- Open the ListofDevices.txt in the given directory and update list of devices
- Open command prompt in window or terminal in the MAC
- Run the python file with the command python3 CXCloud_MW_CommandsGeneration.py, this generate batch files (each batch files include five devices)
- Answers the prompted telemetry questions 
- Newly generated batch files gives the NSO commands
