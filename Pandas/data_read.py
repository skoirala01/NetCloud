#import pandas as pd
import os


try:
    import pandas as pd
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
    import pandas as pd

def printpandaversion():
    print(pd.__version__)

def readcsvdata(path):
    df = pd.read_csv(path+'/data.csv')

    #Tip: use to_string() to print the entire DataFrame.
    print(df.to_string())

    #If you have a large DataFrame with many rows, Pandas will only return the first 5 rows, and the last 5 rows:
    print(df)

    #Print maximum rows
    print(pd.options.display.max_rows)


    ##limit the maximum rows and read it
    pd.options.display.max_rows = 9999
    df = pd.read_csv('data.csv')
    print(df)

    #Print first 5 rows
    print(df.head())

    #Print first 10 rows
    print(df.head(10))

    #Print last 5 rows
    print(df.tail())

    #Print last 10 rows
    print(df.tail(10))

def export(path):
    df = pd.read_csv(path+'/data.csv')
    df.to_csv('dataexportfile.csv')
    df.to_json('dataexportfile.json')

    df.to_excel("dataexportfile.xlsx", sheet_name='Sheet_name_1')


def main():
    printpandaversion()
    path = os.getcwd()
    readcsvdata(path)
    export(path)


if __name__ ==  "__main__":
    main()
