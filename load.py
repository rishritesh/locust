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
            self.client.post("/userEvents", json={"ext_user_id":"0eaa15abfdd1e122b2aa1c39234d9e6191a1cca655bdbdcdb73ca97421d958ae","event_key":"refer_earn","event_data":{"refer_earn":0}})

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
        'host': 'http://localhost:8080/esb/send'  # Replace with your Quarkus app's host and port
    }).run()

