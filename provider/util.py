import logging

import arrow
# import time
# import pytz
# from datetime import timedelta, datetime
# import uuid
# from dateutil import parser
# import numbers
# from random import uniform, randint

# from globus_action_provider_tools.data_types import ActionProviderJsonEncoder


logger = logging.getLogger(__name__)


class SshUtil(object):
    @staticmethod
    def iso_tz_now() -> str:
        """
        Returns an iso8601 compliant, timezone aware timestamp str.
        """
        return str(arrow.utcnow())

    # TODO Remove as we don't care about Chicago Time anymore?
    # @staticmethod
    # def central_time(timestamp_or_datetime) -> str:
    #     """
    #     Converts the input timestamp to central time zone time in isoformat
    #     """
    #     return SshUtil.parse_time(timestamp_or_datetime, 'US/Central')
    #
    # @staticmethod
    # def parse_time(timestamp_or_datetime, tzstr) -> str:
    #     if isinstance(timestamp_or_datetime, datetime):
    #         dt = datetime.fromtimestamp(timestamp_or_datetime.timestamp(), tz=pytz.utc)
    #     elif (isinstance(timestamp_or_datetime, float)
    #           or isinstance(timestamp_or_datetime, int)):
    #         dt = datetime.fromtimestamp(timestamp_or_datetime, tz=pytz.utc)
    #     else:
    #         raise ValueError("Input must be datetime or float timestamp")
    #     return dt.astimezone(pytz.timezone(tzstr)).isoformat()

    @staticmethod
    def get_start(s, max_length=8, replace_line_breaks=False):
        """
        Returns the start of a string, with '...' replacing the rest if
         it is longer than max_length
        """
        if not s:
            return s
        elif not isinstance(s, str):
            raise ValueError("Input to get_start must be a string")
        elif len(s) <= max_length:
            result = s
        else:
            result = s[:max_length] + '...'

        line_break_replacement = ' <br> '
        if replace_line_breaks:
            return result.replace('\n', line_break_replacement)
        else:
            return result


# TODO delete if not needed
# class SshHttpException(Exception):
#     http_status = 500
#     message = "Application error"
#     err_type = "SshActionProviderServerError"
#     errors = ()
#
#     def __init__(self, message=None, token=None, errors=None, err_type=None):
#         super(Exception, self).__init__(message)
#       #  Turning class attrs into instance attrs:
        # self.http_status = self.http_status
        # self.message = message or self.message
        # self.errors = errors or self.errors
        # self.err_type = err_type or self.err_type
    #
    # def __iter__(self):
        #  Allows us to call dict() on exceptions
        # items = (("status", self.http_status), ("message", self.message))
        # for item in items:
        #     yield item
#
#
# class SshActionProviderJsonEncoder(ActionProviderJsonEncoder):
#     def default(self, obj):
#         if isinstance(obj, uuid.UUID):
#             return str(obj)
#         return super(ActionProviderJsonEncoder, self).default(obj)