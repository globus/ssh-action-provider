import datetime
import logging
import os
from typing import Dict, Optional, Tuple
from provider.local_db import ActionDatabase
from provider.util import SshUtil #, SshActionProviderJsonEncoder, SshHttpException

from flask import Flask

from globus_action_provider_tools import AuthState
from globus_action_provider_tools.authorization import (
    authorize_action_access_or_404,
    authorize_action_management_or_404,
)
from globus_action_provider_tools.data_types import (
    ActionFailedDetails,
    ActionInactiveDetails,
    ActionProviderDescription,
    ActionRequest,
    ActionStatus,
    ActionStatusValue,
)
from globus_action_provider_tools.flask.apt_blueprint import ActionProviderBlueprint
from globus_action_provider_tools.flask.exceptions import ActionConflict, ActionNotFound
from paramiko import AutoAddPolicy
from paramiko.client import SSHClient

from provider.config import SshConfig
from .schema import GlobusSshDirectorySchema

ap_description = ActionProviderDescription(
    globus_auth_scope="",
    admin_contact="",
    title="Execute remote ssh command",
    subtitle="Run a shell command on the remote OAuth enabled server",
    synchronous=True,
    input_schema=GlobusSshDirectorySchema,
    log_supported=False,
)

provider_bp = ActionProviderBlueprint(
    name="ssh",
    import_name=__name__,
    url_prefix="",
    provider_description=ap_description,
    globus_auth_client_name="",
)

logger = logging.getLogger(__name__)


def _check_dependent_scope_present(
    request: ActionRequest, auth: AuthState
) -> Optional[str]:
    """return a required dependent scope if it is present in the request,
    and we cannot get a token for that scope via a dependent grant.

    """
    required_scope = request.body.get("required_dependent_scope")
    if required_scope is not None:
        authorizer = auth.get_authorizer_for_scope(required_scope)
        if authorizer is None:
            # Missing the required scope, so return the required scope string
            return f"{ap_description.globus_auth_scope}[{required_scope}]"
    return None


def fail_action(action: ActionStatus, err: str) -> ActionStatus:
    error_msg = f"Error: {err}"
    action.status = ActionStatusValue.FAILED
    action.details = ActionFailedDetails(code="Failed", description=error_msg)
    return action


def _ssh_worker(
    action: ActionStatus, request: ActionRequest, auth: AuthState
) -> ActionStatus:
    cmd = request.body.get("command")
    server = request.body.get("ssh_server")

    action.status = ActionStatusValue.SUCCEEDED
    start_time = datetime.datetime.now()

    if cmd and server:
        if server in SshConfig.KNOWN_SERVER_SCOPES:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(AutoAddPolicy())
            tokens = auth.get_dependent_tokens().by_scopes
            username_or_email = "N/A"
            ssh_server_scope = SshConfig.KNOWN_SERVER_SCOPES[server]["scope"]
            if ssh_server_scope not in tokens:
                fail_action(action, SshConfig.ERROR_DEPENDENT_TOKEN)
                return action

            token_info = auth.introspect_token()
            if "username" in token_info:
                username_or_email = token_info["username"]
            elif "email" in token_info:
                username_or_email = token_info["email"]

            # TODO confirm that email address should also work
            #     if /etc/oauth_ssh/globus-acct-map is configured
            #     For now, use username only
            at_index = username_or_email.find("@")
            if at_index > 0:
                username_or_email = username_or_email[:at_index]

            ssh_output = "N/A"
            try:
                ssh_client.connect(
                    server,
                    username=username_or_email,
                    password=tokens[ssh_server_scope]["access_token"],
                    port=22,
                    timeout=SshConfig.CONNECT_TIMEOUT_SECONDS,
                )
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                err = stderr.read(SshConfig.ERROR_READ_BYTES).decode("utf-8")
                ssh_output = stdout.read(SshConfig.OUTPUT_READ_BYTES).decode("utf-8")
                ssh_client.close()
            except Exception as e:
                err = f"Encountered {SshUtil.get_start(str(e))} connecting to {server}"

            if not err:
                action.details = {"ssh_output": ssh_output}
        else:
            err = SshConfig.ERROR_INVALID_SERVER.format(server=server)
    else:
        err = SshConfig.ERROR_MISSING_INPUT

    if not err and action.status == ActionStatusValue.SUCCEEDED:
        action.completion_time = SshUtil.iso_tz_now()
        duration = datetime.datetime.now() - start_time
        action.details["execution_time_ms"] = duration.microseconds // 1000
    else:
        fail_action(action, err)

    return action


def _update_action_state(
    action: ActionStatus, request: ActionRequest, auth: AuthState
) -> ActionStatus:
    if action.is_complete():
        return action

    required_scope = _check_dependent_scope_present(request, auth)
    if required_scope is not None:
        action.status = ActionStatusValue.INACTIVE
        action.details = ActionInactiveDetails(
            code="ConsentRequired",
            description=f"Consent is required for scope {required_scope}",
            required_scope=required_scope,
        )
    else:
        action = _ssh_worker(action, request, auth)

    action.display_status = action.status
    return action


def save_action(action: ActionStatus, request=None, request_id=None):
    assert action
    if request_id:
        assert request.request_id == request_id
    else:
        assert request
        request_id = request.request_id
    ActionDatabase().store_action_request(
        action,
        request=request,
        action_id=request_id
    )


def delete_action(request_id):
    assert request_id
    ActionDatabase().delete_action_request(action_id=request_id)


def get_status(request_id):
    status, action_request = get_status_and_request(request_id)
    return status


def get_status_and_request(request_id):
    assert request_id
    return ActionDatabase().get_action_request(action_id=request_id)


@provider_bp.action_run
def run_action(request: ActionRequest, auth: AuthState) -> Tuple[ActionStatus, int]:
    status = ActionStatus(
        status=ActionStatusValue.ACTIVE,
        display_status=ActionStatusValue.ACTIVE,
        start_time=SshUtil.iso_tz_now(),
        completion_time=None,
        creator_id=auth.effective_identity,
        monitor_by=request.monitor_by,
        manage_by=request.manage_by,
        details={},
    )

    status = _update_action_state(status, request, auth)
    save_action(status, request)
    return status, 202


@provider_bp.action_resume
def action_resume(action_id: str, auth: AuthState):
    action, request = get_status_and_request(action_id)
    if action is None:
        raise ActionNotFound(f"No Action with id {action_id} found")
    authorize_action_management_or_404(action, auth)

    action = _update_action_state(action, request, auth)
    save_action(action, request=request)
    return action


@provider_bp.action_status
def action_status(action_id: str, auth: AuthState):
    action, request = get_status_and_request(action_id)
    if action:
        authorize_action_access_or_404(action, auth)

        action = _update_action_state(action, request, auth)
        save_action(action, request=request)
        return action
    else:
        raise ActionNotFound(f"No Action with id {action_id} found")


@provider_bp.action_cancel
def action_cancel(action_id: str, auth: AuthState):
    status, request = get_status_and_request(action_id)
    if status is None:
        raise ActionNotFound(f"No Action with id {action_id} found")
    authorize_action_management_or_404(status, auth)
    if status.is_complete():
        return status
    else:
        status.status = ActionStatusValue.FAILED
        status.completion_time = SshUtil.iso_tz_now()
        status.display_status = f"Cancelled by {auth.effective_identity}"[:64]
        save_action(status, request)


@provider_bp.action_release
def action_release(action_id: str, auth: AuthState):
    action, request = get_status(action_id)
    if action is None:
        raise ActionNotFound(f"No Action with id {action_id} found")
    authorize_action_management_or_404(action, auth)

    action = _update_action_state(action, request, auth)
    if not action.is_complete():
        raise ActionConflict("Action is not complete")

    delete_action(action_id)
    return action


def load_ssh_provider(app: Flask, config: dict = None) -> Flask:
    """
    This is the entry point for the Flask blueprint
    """

    if config is None:
        config = SshConfig.BP_CONFIG

    env_client_id = os.getenv(SshConfig.CLIENT_ID_ENV)
    env_client_secret = os.getenv(SshConfig.CLIENT_SECRET_ENV)

    if env_client_id:
        config["globus_auth_client_id"] = env_client_id
        # TODO figure out why _name is used in auth client_id checking
        config["globus_auth_client_name"] = env_client_id
    else:
        raise EnvironmentError(f"{SshConfig.CLIENT_ID_ENV} needs to be set")

    if env_client_secret:
        config["globus_auth_client_secret"] = env_client_secret
    else:
        raise EnvironmentError(f"{SshConfig.CLIENT_SECRET_ENV} needs to be set")

    provider_bp.url_prefix = config["url_prefix"]

    # TODO change to _name
    provider_bp.globus_auth_client_name = config["globus_auth_client_id"]

    app.config["CLIENT_ID"] = config["globus_auth_client_id"]
    app.config["CLIENT_SECRET"] = config["globus_auth_client_secret"]

    ap_description.globus_auth_scope = config["globus_auth_scope"]
    ap_description.visible_to = config["visible_to"]
    ap_description.runnable_by = config["runnable_by"]
    ap_description.admin_contact = config["admin_contact"]
    ap_description.administered_by = config["administered_by"]

    app.register_blueprint(provider_bp)

    logger.info("SSH Provider loaded successfully")

    return app
