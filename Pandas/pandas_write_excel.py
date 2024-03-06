import pandas as pd
try:
    import openpyxl
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'openpyxl'])
    import openpyxl

# Create a simple DataFrame
data = {
    'Name': ['John Doe', 'Jane Smith', 'Emily Jones'],
    'Age': [28, 34, 24],
    'City': ['New York', 'Chicago', 'Los Angeles']
}

df = pd.DataFrame(data)

# Specify the Excel writer engine and the name of the Excel file.
excel_writer = pd.ExcelWriter('people.xlsx', engine='openpyxl')

# Write the DataFrame to the Excel file.
df.to_excel(excel_writer, sheet_name='Sheet1', index=False)

# Save the Excel file.
excel_writer.close()

print('DataFrame is written to Excel File successfully.')
