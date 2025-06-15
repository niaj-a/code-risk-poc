from __future__ import annotations

import os

# set env before app imports so settings/engine see test values
os.environ["APP_NAME"] = "Bank Code Risk POC Test"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["MAX_DIFF_CHARS"] = "60000"
os.environ["ALLOWED_REPOSITORIES"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_API_KEY"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""
os.environ["AZURE_OPENAI_DEPLOYMENT"] = ""

import pytest
from fastapi.testclient import TestClient
db_session.configure_engine(os.environ["DATABASE_URL"])
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


@pytest.fixture()
def settings():
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture()
def db_engine():
    Base.metadata.drop_all(bind=db_session.engine)
