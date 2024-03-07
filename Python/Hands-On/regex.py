import re

regexIP = '''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
    25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'''

def validateIP(strIP):

    if(re.search(regexIP, strIP)):
        print("Valid IP address")

    else:
        print("Invalid IP address")
 
if __name__ == '__main__' :

    strIP = "122.134.3.123"
    validateIP(strIP)

    strIP = "44.235.34.1"
    validateIP(strIP)

    strIP = "277.13.23.17"
    validateIP(strIP)
