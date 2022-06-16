import uuid

import pytest
from provider.util import SshUtil
from datetime import datetime
from random import randrange
import logging
from provider.local_db import ActionDatabase, LocalStore

from globus_action_provider_tools.data_types import (
    ActionRequest,
    ActionStatus,
    ActionStatusValue,
)

logger = logging.getLogger(__name__)

_TEST_DB_FILE = 'test_settings'


@pytest.fixture(scope="session", autouse=True)
def db_setup():
    """
    To ensure database cleanup after tests
    """
    conn = LocalStore(_TEST_DB_FILE)
    yield conn
    conn.delete_database()


class TestSshUtil(object):
    _total_reads = 0
    _total_writes = 0
    _TEST_DB_SECONDS = 2
    _TEST_DB_SECONDS_DELAYED = 5

    def test_action_database(self):
        action_id = 'first_ssh_action_' + str(randrange(50))
        action_db = ActionDatabase(
            table_name=_TEST_DB_FILE,
            request_id=action_id
        )
        test_time = SshUtil.iso_tz_now()
        status = ActionStatus(
            status=ActionStatusValue.ACTIVE,
            creator_id=f"urn:globus:groups:id:{str(uuid.uuid4())}",
            display_status=ActionStatusValue.ACTIVE,
            start_time=test_time,
            details={},
        )
        action_request = ActionRequest(
            request_id=action_id,
            body={'my_field': 'my_value'},
        )
        action_db.store_action_request(status, request=action_request)
        status, request = action_db.get_action_request()
        assert test_time == status.start_time
        assert "my_value" == request.body['my_field']

        action_request.label = "new_label"
        status.status = ActionStatusValue.FAILED
        action_db.update_action_request(status, request=action_request)

        status, request = action_db.get_action_request()
        assert ActionStatusValue.FAILED == status.status
        assert "new_label" == request.label

        with pytest.raises(KeyError):
            action_db.delete_action_request(action_id="invalid_action_id")

        action_db.delete_action_request()

    # def test_central_time(self):
        # Closest is US/Central as there is no America/Chicago?
        # assert '1969-12-31T18:00:01-06:00' == SshUtil.central_time(1)
        # assert ('2019-08-11T15:55:05.153142-05:00' ==
        #         SshUtil.central_time(datetime.fromtimestamp(1565556905.153142)))
        # try:
        #     SshUtil.central_time('not valid')
        #     assert False, 'Expected ValueError'
        # except ValueError:
        #     pass
