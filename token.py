from locust import HttpUser, task, between
from prometheus_client import start_http_server, Summary, Counter, generate_latest
import threading
import pandas as pd
import json

# Define Prometheus metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Number of requests made')

class MyUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Load dynamic values from Excel file
        self.df = pd.read_excel('confi.xlsx', engine='openpyxl')
        self.df.columns = self.df.columns.str.strip()
        print(f"Columns in Excel file: {self.df.columns.tolist()}")  # Print column names for debugging
        self.current_index = 0
        self.host = self.df.at[0, 'host']  # Set the initial host from the first row

    @task
    @REQUEST_TIME.time()  # Measure the time of this task
    def my_task(self):
        # Get current row data
        row = self.df.iloc[self.current_index]
        self.host = row['host']  # Update the host dynamically for each request
        endpoint = row['endpoint']
        payload = json.loads(row['payload'])
        token = row.get('token', None)  # Get token if available

        headers = {'Authorization': f'Bearer {token}'} if token else {}

        with REQUEST_TIME.time():
            self.client.post(endpoint, json=payload, headers=headers)
        
        REQUEST_COUNT.inc()  # Increment request count

        # Update index to the next row, loop back to start if at the end
        self.current_index = (self.current_index + 1) % len(self.df)

# Function to expose Prometheus metrics
def start_prometheus_server():
    start_http_server(9646)  # Start Prometheus metrics server on port 9646

    # Expose a /metrics endpoint that Prometheus expects
    while True:
        generate_latest()

# Start Locust load test and Prometheus metrics server
if __name__ == "__main__":
    # Start Prometheus metrics server in a separate thread
    threading.Thread(target=start_prometheus_server).start()

    # Start Locust load test
    MyUser(environment={
        'host': 'http://localhost'  # Set a default host to satisfy Locust requirement
    }).run()

