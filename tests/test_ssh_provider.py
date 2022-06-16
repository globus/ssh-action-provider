import copy
import uuid
from functools import partial
from typing import Any, Dict, NamedTuple
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient
from globus_action_provider_tools.data_types import ActionStatusValue
import globus_action_provider_tools.testing.fixtures

import provider
from provider import provider_bp
from provider.config import SshConfig


@pytest.fixture
def noauth(apt_blueprint_noauth):
    apt_blueprint_noauth(provider_bp)


@pytest.fixture(autouse=True)
def patched_ssh_client():
    with patch("paramiko.client.SSHClient", return_value=MagicMock()) as p:
        p.connect = MagicMock()
        p.exec_command = MagicMock()
        p.close = MagicMock()
        yield p


class AutomateTestConfig(NamedTuple):
    app: Flask
    app_client: FlaskClient


@pytest.fixture()
def config() -> AutomateTestConfig:
    app = Flask(__name__)
    config = provider.load_ssh_provider(app, None)
    client = app.test_client()
    return AutomateTestConfig(app=app, app_client=client)


def endpoint_url(config: AutomateTestConfig, blueprint_name: str, suffix: str):
    return config.app.blueprints[blueprint_name].url_prefix + suffix


def get_introspection_endpoint(config: AutomateTestConfig, blueprint_name: str):
    return endpoint_url(config, blueprint_name, "/")


def get_run_endpoint(config: AutomateTestConfig, blueprint_name: str):
    return endpoint_url(config, blueprint_name, "/run")


def get_status_endpoint(
    config: AutomateTestConfig, blueprint_name: str, action_id: str
):
    return endpoint_url(config, blueprint_name, f"/{action_id}/status")


def get_resume_endpoint(
    config: AutomateTestConfig, blueprint_name: str, action_id: str
):
    return endpoint_url(config, blueprint_name, f"/{action_id}/resume")


def get_cancel_endpoint(
    config: AutomateTestConfig, blueprint_name: str, action_id: str
):
    return endpoint_url(config, blueprint_name, f"/{action_id}/cancel")


def get_release_endpoint(
    config: AutomateTestConfig, blueprint_name: str, action_id: str
):
    return endpoint_url(config, blueprint_name, f"/{action_id}/release")


def run_action_return_status(
    config: AutomateTestConfig, *, provider_blueprint_name: str, data: Dict[str, Any]
) -> Dict:
    """
    Helper function to easily launch an action and return its complete action status.
    This function is adequate for launching a job for any endpoint test except
    for the run endpoint.

    The calling function should have had all external dependencies (i.e.
    its authstate, tokenchecker, transfer clients) mocked so that this
    request successfully triggers an action.
    """
    if "request_id" not in data:
        data = copy.deepcopy(data)
        data["request_id"] = str(uuid.uuid4())

    run_endpoint = endpoint_url(config, provider_blueprint_name, "/run")
    run_response = config.app_client.post(run_endpoint, json=data)
    return run_response.json


def run_action_return_id(
    config: AutomateTestConfig,
        *,
        provider_blueprint_name: str,
        data: Dict[str, Any]
):
    """
    Helper function to easily launch an action and return its action_id.
    This function is adequate for launching a job for any endpoint test except
    for the run endpoint.

    The calling function should have had all external dependencies (i.e.
    its authstate, tokenchecker, transfer clients) mocked so that this
    request successfully triggers an action.
    """
    response = run_action_return_status(
        config, provider_blueprint_name=provider_blueprint_name, data=data
    )
    return response
    # TODO fix
    # return response["action_id"]


run_transfer_return_id = partial(
    run_action_return_id,
    provider_blueprint_name=provider_bp.name,
    data={
        "body": {
            "ssh_server": "ssh.my.example.edu",
            "command": "ls -l",
        },
    },
)


def test_introspection(config: AutomateTestConfig):
    introspection_endpoint = get_introspection_endpoint(config, provider_bp.name)
    response = config.app_client.get(introspection_endpoint)

    assert response.status_code == 200
    assert (
        response.json.get("input_schema")
        == provider_bp.provider_description.input_schema.schema()
    ), response.data


@pytest.mark.skip(reason="TODO Fix")
def test_run(patched_ssh_client, config: AutomateTestConfig, noauth):
    run_endpoint = get_run_endpoint(config, provider_bp.name)
    data: Dict[str, Any] = {
        "request_id": "-",
        # Non ssh server will do ping instead
        "body": {"ssh_server": "ssh.my.example.edu", "command": "ls -l"},
    }
    run_response = config.app_client.post(run_endpoint, json=data)
    assert run_response.status_code == 202, run_response.data

    ssh_server = data["body"].pop("ssh_server")
    command = data["body"].pop("command")
    patched_ssh_client().connect.assert_called_once_with(ssh_server)
    patched_ssh_client().exec_command.assert_called_once_with(command)
    patched_ssh_client().connect.assert_called_once()

    assert (
        run_response.json.get("status") == ActionStatusValue.SUCCEEDED
    ), run_response.data


def test_status_for_missing_action(
    patched_ssh_client, config: AutomateTestConfig, noauth
):
    action_id = "0000"
    status_endpoint = get_status_endpoint(config, provider_bp.name, action_id)
    status_response = config.app_client.get(status_endpoint)

    assert status_response.status_code == 404


@pytest.mark.skip(reason="TODO Fix")
def test_release(patched_ssh_client, config: AutomateTestConfig, noauth):
    action_id = run_transfer_return_id(config)
    release_endpoint = get_release_endpoint(config, provider_bp.name, action_id)
    release_response = config.app_client.post(release_endpoint)
    rerelease_response = config.app_client.post(release_endpoint)

    # TODO Fix
    # assert release_response.status_code == 200
    assert release_response.json.get("status") != ActionStatusValue.SUCCEEDED
    assert rerelease_response.status_code == 404


def test_release_for_missing_action(
    patched_ssh_client, config: AutomateTestConfig, noauth
):
    action_id = "0000"
    release_endpoint = get_release_endpoint(config, provider_bp.name, action_id)
    release_response = config.app_client.post(release_endpoint)

    assert release_response.status_code == 404
