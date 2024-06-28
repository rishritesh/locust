from locust import HttpUser, task, between
from prometheus_client import start_http_server, Summary, Counter, generate_latest
import threading

# Define Prometheus metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Number of requests made')

class MyUser(HttpUser):
    wait_time = between(1, 3)

    @task
    @REQUEST_TIME.time()  # Measure the time of this task
    def my_task(self):
        with REQUEST_TIME.time():
            self.client.post("/mini", json={"accountNo": "string","fromDate": "string","toDate": "string","token": "string", "numberOfRows": "string","tranType": "string","order": "string"})

        REQUEST_COUNT.inc()  # Increment request count

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
        'host': 'http://localhost:9099/request'  # Replace with your Quarkus app's host and port
    }).run()

