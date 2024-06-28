from locust import HttpUser, TaskSet, task, between

class UserBehavior(TaskSet):
    @task
    def index(self):
        self.client.post("/mini",json={"accountNo": "string","fromDate": "string","toDate": "string","token": "string", "numberOfRows": "string","tranType": "string","order": "string"})


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(1, 5)

