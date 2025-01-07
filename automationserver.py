import os
import requests
import json
import logging
from dataclasses import dataclass


class AutomationServerConfig:
    token = ""
    url = ""
    session = ""
    resource = ""
    process = ""

    workitem_id = None

    def from_enviroment(fallback_url: str = "", fallback_token: str = ""):
        logger = logging.getLogger(__name__)

        if "ATS_URL" not in os.environ or "ATS_TOKEN" not in os.environ:
            AutomationServerConfig.url = fallback_url
            AutomationServerConfig.token = fallback_token
            logger.info(f"Using fallback URL {fallback_url} and token {fallback_token}")
            return

        AutomationServerConfig.url = os.environ["ATS_URL"]
        AutomationServerConfig.token = os.environ["ATS_TOKEN"]
        AutomationServerConfig.session = os.environ["ATS_SESSION"]
        AutomationServerConfig.resource = os.environ["ATS_RESOURCE"]    
        AutomationServerConfig.process = os.environ["ATS_PROCESS"]
        

        logger.info(f"Using URL {AutomationServerConfig.url} and token {AutomationServerConfig.token}")

    

# Custom HTTP Handler for logging
class AutomationServerLoggingHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        print("Sending log")
        log_entry = self.format(record)  # Format the log record
        log_data = { "workitem_id": 0, "message": log_entry }

        if AutomationServerConfig.session == "" or AutomationServerConfig.url == "":
            return

        if AutomationServerConfig.workitem_id is not None:
            log_data["workitem_id"] = AutomationServerConfig.workitem_id

        try:
            response = requests.post(
                f"{AutomationServerConfig.url}/sessions/{AutomationServerConfig.session}/log",
                headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
                json=log_data,
            )
            response.raise_for_status()
        except Exception as e:
            # Handle any exceptions that occur when sending the log
            print(f"Failed to send log to {self.url}: {e}")



class AutomationServer:
    session_id = None

    def __init__(self, session_id=None):
        session_id = session_id
        self.workqueue_id = None
        self.url = AutomationServerConfig.url
        self.token = AutomationServerConfig.token

        if session_id is not None:
            self.session = Session.get_session(session_id)
            self.process = Process.get_process(self.session.process_id)
            if self.process.workqueue_id > 0:
                self.workqueue_id = self.process.workqueue_id
        else:
            self.session = None
            self.process = None


    def workqueue(self):
        if self.workqueue_id is None:
            raise ValueError("workqueue_id is not set")

        return Workqueue.get_workqueue(self.workqueue_id)

    def from_environment():
        # Check if ats_url, ats_token and ats_session are set in the environment, if not, return None
        if "ATS_SESSION" not in os.environ:
            return None

        return AutomationServer(os.environ["ATS_SESSION"])

    def debug(workqueue_id):
        ats = AutomationServer(None)
        ats.workqueue_id = workqueue_id
        return ats

    def __str__(self):
        return f"AutomationServer(url={self.url}, token={self.token},session = {self.session}, process = {self.process}, workqueue_id={self.workqueue_id})"


@dataclass
class Session:
    id: int
    process_id: int
    resource_id: int
    dispatched_at: str
    status: str
    stop_requested: bool
    deleted: bool
    parameters: str
    created_at: str
    updated_at: str

    def get_session(session_id):
        response = requests.get(
            f"{AutomationServerConfig.url}/sessions/{session_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
        )
        response.raise_for_status()

        return Session(**response.json())

@dataclass
class Process:
    id: int
    name: str
    description: str
    requirements: str
    target_type: str
    target_source: str
    target_credentials_id: int
    credentials_id: int
    workqueue_id: int
    deleted: bool
    created_at: str
    updated_at: str

    def get_process(process_id):
        response = requests.get(
            f"{AutomationServerConfig.url}/processes/{process_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
        )
        response.raise_for_status()

        return Process(**response.json())

@dataclass
class Workqueue:
    id: int
    name: str
    description: str
    enabled: bool
    deleted: bool
    created_at: str
    updated_at: str

    def add_item(self, data: dict, reference: str):
        response = requests.post(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/add",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"data": json.dumps(data), "reference": reference},
        )
        response.raise_for_status()

        return WorkItem(**response.json())

    def get_workqueue(workqueue_id):
        response = requests.get(
            f"{AutomationServerConfig.url}/workqueues/{workqueue_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
        )
        response.raise_for_status()

        return Workqueue(**response.json())

    def clear_workqueue(self, workitem_status=None, days_older_than=None):
        response = requests.post(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/clear",
            json={
                "workitem_status": workitem_status,
                "days_older_than": days_older_than,
            },
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
        )
        response.raise_for_status()

    def __iter__(self):
        return self

    def __next__(self):
        response = requests.get(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/next_item",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
        )

        if response.status_code == 204:
            raise StopIteration

        response.raise_for_status()

        AutomationServerConfig.workitem_id = response.json()["id"]

        return WorkItem(**response.json())


@dataclass
class WorkItem:
    id: int
    data: str
    reference: str
    locked: bool
    status: str
    message: str
    workqueue_id: int
    created_at: str
    updated_at: str


    def get_data_as_dict(self) -> dict:
        return json.loads(self.data)

    def update(self, data: dict):
        response = requests.put(
            f"{AutomationServerConfig.url}/workitems/{self.id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"data": json.dumps(data), "reference": self.reference},
        )
        response.raise_for_status()
        self.data = json.dumps(data)
       


    def __enter__(self):
        logger = logging.getLogger(__name__)
        logger.debug(f"Processing {self}")
        AutomationServerConfig.workitem_id = self.id

    def __exit__(self, exc_type, exc_value, traceback):
        logger = logging.getLogger(__name__)
        AutomationServerConfig.workitem_id = None
        if exc_type:
            logger.error(
                f"An error occurred while processing {self}: {exc_value}"
            )
            self.fail(str(exc_value))

        # If we are working on an item that is in progress, we will mark it as completed
        if self.status == "in progress":
            self.complete("Completed")

    def __str__(self) -> str:
        return f"WorkItem(id={self.id}, reference={self.reference}, data={self.data})"

    def fail(self, message):
        self.update_status("failed", message)

    def complete(self, message):
        self.update_status("completed", message)

    def pending_user(self, message):
        self.update_status("pending user action", message)

    def update_status(self, status, message: str = ""):
        response = requests.put(
            f"{AutomationServerConfig.url}/workitems/{self.id}/status",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"status": status, message: message},
        )
        response.raise_for_status()
        self.status = status
        self.message = message
