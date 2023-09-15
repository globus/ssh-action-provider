#### Overview

The globus_ssh Action Provider allows users to execute a command on the remote oauth-ssh enabled server.


##### Testing

You can verify this specific Action Provider's behavior by selectively running its pytests with the following command:

    ```bash
    poetry run pytest tests/test_globus_ssh.py
    ```

Finally, specify a database endpoint to use in testing.  The test defaults to searching for a DynamoDB instance running on localhost:4566 and spinning this up localstack with Docker is recommended. To change this setting, modify the configuration at globus/automate/providers/actions_config.py, and set the boto_dynamodb_client_params variable for GlobusSsh accordingly.
