import dill
import json
import logging
import sqlite3
import os
from provider.util import SshUtil


logger = logging.getLogger(__name__)


class LocalStore:
    """
    This a database implementation using local file storage
    File based cache implemented using sqlite3
    Only 2 columns - id (str primary key) and value (str)
    The db is stored at the root of the service with suffix .sqlitedb

    TODO as this is a key/value pair, it can be distributed to several segments
     based on key hash to avoid I/O conflicts, for multi-node access, not necessary
     at this time
    Usage:
            * mydata = LocalStore("NBA_players")
            * mydata.put("best_player", "Lebron Bryant")
            * mydata.put("worst_player", "Kobe James")
            * if 'Lebron' in mydata.get("best_player"):
            *     print("Correct, worst player is %s" % mydata.get("worst_player"))
            * else:
            *     print("No way!!  Burning the place down.")
    """
    _DEFAULT_DATABASE_NAME = 'ssh_local_db'
    _DB_FILE_SUFFIX = '.sqlitedb'

    def __init__(self, db_name=_DEFAULT_DATABASE_NAME):
        """
        db_name is used as the prefix of the local db file name as well
        as the name of the table in the .sqlite3 database
        """
        db_name = db_name.strip()
        if not db_name:
            raise ValueError("db_name must be provided : (%s)" % db_name)
        if ';' in db_name or '.' in db_name or "'" in db_name:
            raise ValueError("db_name can not contain [;.']")
        self.db_table = db_name

        conn = None
        try:
            conn = sqlite3.connect(self._file_name())
            conn.execute("CREATE TABLE IF NOT EXISTS %s(id primary key, value text)" % self.db_table)
            conn.commit()
        except Exception as e:
            logger.error('Exception when creating table %s: %s' % (self.db_table, str(e)))
        finally:
            if conn:
                conn.close()

    def _file_name(self):
        return self.db_table + self._DB_FILE_SUFFIX

    def delete_database(self):
        if os.path.exists(self._file_name()):
            os.remove(self._file_name())

    def clear_table(self):
        conn = None
        try:
            conn = sqlite3.connect(self._file_name())
            conn.execute("DROP TABLE IF EXISTS %s" % self.db_table)
            conn.commit()
            conn.execute("CREATE TABLE %s(id primary key, value text)" % self.db_table)
            conn.commit()
        except Exception as e:
            logger.error('Exception when dropping table %s: %s' % (self.db_table, str(e)))
        finally:
            if conn:
                conn.close()

    @staticmethod
    def is_valid_key(key):
        # Disallow colon and semicolon in key
        return ';' not in key and ':' not in key

    def delete(self, key):
        if not self.is_valid_key(key):
            logger.error("Invalid key:  %s" % str(key))
            return
        conn = sqlite3.connect(self._file_name())
        try:
            conn.execute('DELETE from %s where id = ?' % self.db_table, [key])
            conn.commit()
        except sqlite3.OperationalError as e:
            if 'no such table' in str(e):
                logger.error("Shouldn't encounter this error, table should be created already in delete_value")
        except sqlite3.DatabaseError as e:
            logger.error("Database error exception: %s" % str(e))
        finally:
            conn.close()

    def put(self, key, value):
        if not self.is_valid_key(key):
            raise ValueError('Key can not contain (;) or (")')
        conn = sqlite3.connect(self._file_name())
        try:
            conn.execute("INSERT OR IGNORE INTO %s(id, value) values (?, ?)" % self.db_table, [key, value])
            conn.execute('UPDATE %s SET value=? where id=?' % self.db_table, [value, key])
            conn.commit()
        except sqlite3.OperationalError as e:
            if 'no such table' in str(e):
                logger.error("Shouldn't encounter this error, table should be created already in put_value")
        except sqlite3.DatabaseError as e:
            logger.error("Database error exception: %s" % str(e))
        except Exception as e:
            logger.error("Unknown put exception: %s" % str(e))
        finally:
            conn.close()

    def get(self, key):
        if not self.is_valid_key(key):
            return None
        conn = sqlite3.connect(self._file_name())
        try:
            # logger.debug("getting %s from table %s" % (key, self.db_table))
            value_cursor = conn.execute('select value from %s where id = ?' % self.db_table, [key])
            result = value_cursor.fetchone()
            if result:
                return result[0]
        except sqlite3.OperationalError as e:
            if 'no such table' in str(e):
                logger.error("Shouldn't encounter this error, table should be created already in get_value")
        except sqlite3.DatabaseError as e:
            logger.error("Database error exception: %s" % str(e))
        finally:
            conn.close()
        return None


class ActionDatabase(LocalStore):
    _DEFAULT_ACTION_NAME = "globus_actions"

    def __init__(self, request_id=None, table_name=_DEFAULT_ACTION_NAME):
        """
        If request_id is provided, it will be the default value
        for action_id for this ActionDatabase instance for methods
        """
        LocalStore.__init__(self, db_name=table_name)
        self.action_id = request_id

    def get_info_dict(self, action_id=None):
        if action_id is None:
            action_id = self.action_id
        assert action_id, "action_id must be provided"
        result = self.get(action_id)
        if result:
            try:
                return json.loads(result)
            except json.JSONDecodeError as e:
                logger.error("Invalid entry in info storage: %s" % str(e))
        return {}

    def store_action_request(self, action, request=None, action_id=None):
        assert action.action_id
        action_object = {
            'status': action,
            'request': request,
        }
        if not action_id:
            assert request and request.request_id
            action_id = request.request_id
        action_encoded = dill.dumps(action_object)
        self.put(action_id, action_encoded)

    def get_action_request(self, action_id=None):
        if action_id is None:
            action_id = self.action_id
        assert action_id, "action_id must be provided"
        action_encoded = self.get(action_id)
        if action_encoded:
            action_object = dill.loads(action_encoded)
            assert 'status' in action_object
            assert 'request' in action_object
            return (action_object.get('status', None),
                    action_object.get('request', None))
        else:
            return None, None

    def update_action_request(self, action_status, action_id=None, request=None):
        if action_id is None:
            action_id = self.action_id
        action_object = self.get(action_id)
        if not action_object:
            logger.info(f"Action {action_id} was newly created on update")
        return self.store_action_request(
            action_status,
            request=request,
            action_id=action_id
        )

    def delete_action_request(self, action_id=None):
        if action_id is None:
            action_id = self.action_id
        assert action_id, "action_id must be provided"
        action = self.get(action_id)
        if action:
            self.delete(action_id)
            logger.info(f"Action {action_id} was deleted from table")
        else:
            raise KeyError(f"Action {action_id} was not found")
