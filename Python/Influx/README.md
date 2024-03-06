Install influxdb
---
`pip install influxdb`


Theory about InfluxDB
----
InfluxDB is a time series database designed to handle high write and query loads. It is a product from InfluxData as part of their InfluxData platform, which also includes Chronograf (for visualization), Kapacitor (for data processing and alerting), and Telegraf (for data collection). InfluxDB is commonly used for applications that require high-performance handling of time series data, such as monitoring systems, IoT applications, and real-time analytics.

In Python, you can interact with InfluxDB using the influxdb client library, which allows you to connect to an InfluxDB instance, write data, query data, and more.

Here is an example of how you can use the influxdb library to write data to and query data from an InfluxDB database. Before running the code, you need to install the influxdb Python package:
