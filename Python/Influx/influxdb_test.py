#from influxdb_client import InfluxDBClient, Point
#from influxdb_client.client.write_api import SYNCHRONOUS

try:
    from influxdb_client import InfluxDBClient, Point
except:
    import sys
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'influxdb'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'influxdb-client'])

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Connect to InfluxDB
client = InfluxDBClient(url='http://localhost:8086', token='your-token', org='your-org')

# Get a write API
write_api = client.write_api(write_options=SYNCHRONOUS)

# Define a Point with your data
point = Point("weather").tag("location", "New York").field("temperature", 55.5).field("humidity", 60)

# Write data to the database
write_api.write(bucket='your-bucket', record=point)

# Query data from the database
query_api = client.query_api()
results = query_api.query('from(bucket:"your-bucket") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "weather")')

# Print the results of the query
for table in results:
    for record in table.records:
        print(f'Time: {record.get_time()}, Location: {record.get_value("location")}, Temperature: {record.get_value("temperature")}, Humidity: {record.get_value("humidity")}')

# Close the client
client.close()
