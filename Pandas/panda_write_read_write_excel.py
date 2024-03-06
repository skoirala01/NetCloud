import pandas as pd

# Create a DataFrame to export if you don't have an existing Excel file.
# If you already have an Excel file, you can comment out the following lines.
initial_data = {
    'Name': ['John Doe', 'Jane Smith', 'Emily Jones'],
    'Age': [28, 34, 24],
    'City': ['New York', 'Chicago', 'Los Angeles']
}
initial_df = pd.DataFrame(initial_data)
initial_df.to_excel('initial_data.xlsx', index=False, engine='openpyxl')

# Now, let's assume you have 'initial_data.xlsx' and want to read it, modify it, and export it.

# Read the Excel file into a pandas DataFrame
df = pd.read_excel('initial_data.xlsx', engine='openpyxl')

# Let's add a new column to the DataFrame
df['Salary'] = [70000, 80000, 75000]

# Now, export the modified DataFrame to a new Excel file
output_file_name = 'modified_data.xlsx'
df.to_excel(output_file_name, index=False, engine='openpyxl')

print(df)
print(df.to_json())
print(f'DataFrame is read from the Excel file and written to a new Excel file "{output_file_name}" successfully.')
