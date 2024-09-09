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

    current_item = None

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
        logger.info(f"Processing {self}")
        self.current_item = self

    def __exit__(self, exc_type, exc_value, traceback):
        logger = logging.getLogger(__name__)
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
