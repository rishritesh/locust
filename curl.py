from locust import HttpUser, task, between, events
from prometheus_client import start_http_server, Summary, Counter, generate_latest
import threading
import pandas as pd
import subprocess
import shlex
import time
import re

# Define Prometheus metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Number of requests made')

def extract_endpoint(curl_command):
    match = re.search(r"'(https?://[^/]+(/[^/]+)+)", curl_command)
    if match:
        return match.group(1)
    return "unknown_endpoint"

class MyUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Load dynamic values from Excel file
        self.df = pd.read_excel('curl.xlsx', engine='openpyxl')
        self.df.columns = self.df.columns.str.strip()
        print(f"Columns in Excel file: {self.df.columns.tolist()}")
        self.total_rows = len(self.df)
        print(f"Total rows in Excel file: {self.total_rows}")

    @task
    def execute_curls(self):
        for index, row in self.df.iterrows():
            self.execute_single_curl(row)

    @REQUEST_TIME.time()
    def execute_single_curl(self, row):
        curl_command = row['curl_command']
        service_name = row['service_name']
        print(f"Executing curl command: {curl_command} for service: {service_name}")
        start_time = time.time()
        try:
            curl_args = shlex.split(curl_command)
            response = subprocess.run(curl_args, capture_output=True, timeout=30)
            
            response_time = int((time.time() - start_time) * 1000)
            response_length = len(response.stdout)
            endpoint = extract_endpoint(curl_command)
            request_name = f"{service_name}:"
            if response.returncode == 0 and response.stdout:
                events.request.fire(
                    request_type="curl",
                    name=request_name,
                    response_time=response_time,
                    response_length=response_length,
                    response=response,
                    context={},
                    exception=None,
                )
                print(f"Response status code: {response.returncode}")
                print(f"Response content: {response.stdout.decode('utf-8')}")
            else:
                events.request.fire(
                    request_type="curl",
                    name=request_name,
                    response_time=response_time,
                    response_length=0,
                    response=response,
                    context={},
                    exception=Exception(f"Curl command failed or returned empty response with return code {response.returncode}")
                )
                print(f"Curl command failed or returned empty response with return code: {response.returncode}")
                print(f"Error output: {response.stderr.decode('utf-8')}")
            REQUEST_COUNT.inc()
        except subprocess.TimeoutExpired:
            events.request.fire(
                request_type="curl",
                name=request_name,
                response_time=30000,  # 30 seconds timeout
                response_length=0,
                response=None,
                context={},
                exception=Exception("Timeout")
            )
            print("Curl command timed out after 30 seconds")
        except Exception as e:
            events.request.fire(
                request_type="curl",
                name=request_name,
                response_time=int((time.time() - start_time) * 1000),
                response_length=0,
                response=None,
                context={},
                exception=e
            )
            print(f"Error executing curl command: {str(e)}")

# Function to expose Prometheus metrics
def start_prometheus_server():
    start_http_server(9646)
    while True:
        generate_latest()

if __name__ == "__main__":
    threading.Thread(target=start_prometheus_server).start()
    from locust import main
    main.main(["-f", __file__, "--web-host", "localhost", "--web-port", "8089"])

