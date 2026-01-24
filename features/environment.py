import os
import threading
import time
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use a separate test database
os.environ["DATABASE_URL"] = "sqlite:///./test_data/test.db"
os.environ["PASSWORD_SALT"] = "test-salt"

from database import Base, engine
from main import app


class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.server = None

    def run(self):
        config = uvicorn.Config(app, host="127.0.0.1", port=8081, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True


def before_all(context):
    os.makedirs("test_data", exist_ok=True)
    Base.metadata.create_all(bind=engine)

    context.server_thread = ServerThread()
    context.server_thread.start()
    time.sleep(1)

    context.base_url = "http://127.0.0.1:8081"
    context.users = {}


def after_all(context):
    context.server_thread.stop()


def before_scenario(context, scenario):
    # Clear all tables before each scenario
    Session = sessionmaker(bind=engine)
    session = Session()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()
    context.users = {}
    context.last_response = None
    context.last_progress = None
