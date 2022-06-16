class SshConfig:
    CONNECT_TIMEOUT_SECONDS = 10
    ERROR_READ_BYTES = 10000
    OUTPUT_READ_BYTES = 100000

    # Environment vars that need to be set for the AP Confidential Client
    CLIENT_ID_ENV = 'SSH_AP_CLIENT_ID'
    CLIENT_SECRET_ENV = 'SSH_AP_CLIENT_SECRET'

    APP_NAME = "my_ssh_action_provider"

    """
    These scopes are manually set up via PUT to /v2/api/scopes.
    
    They only need to be set up once per OAuth-SSH capable Server
    
    See https://docs.globus.org/api/auth/reference/#get_scopes on details
    on how to create scopes for clients
    
    Note that without an entry below, and if the Scope is private,
    searching by name for scope UUID will not work for auth purposes
    """
    KNOWN_SERVER_SCOPES = {
        "ssh.my.server.edu": {
            # Example server #1
            "scope_id": "c0c3fd00-6a73-4801-930e-008d0ee6c26e",
            "scope": "https://auth.globus.org/scopes/ssh.my.server.edu/ssh",
        },
        # TODO Remove ssh.globustest.org after internal globus testing
        "ssh.globustest.org": {
            # Example server #2
            "scope_id": "c0c3fd00-6a73-4801-930e-008d0ee6c26e",
            "scope": "https://auth.globus.org/scopes/ssh.my.server.edu/ssh",
        },
    }

    BP_CONFIG = {
        "python_module": "ssh_action_provider.provider",
        "entry_point": "app",
        "globus_auth_client_id": "replaced_with_env_CLIENT_ID",
        "globus_auth_client_secret": "replaced_with_env_CLIENT_SECRET",
        "globus_auth_client_name": "OAuth SSH Auth Client",
        "globus_auth_scope": "replace_with_scope_id",
        # Who can see that this Action Provider is available
        "visible_to": ["public"],
        # Who can use this Action Provider in a flows run
        "runnable_by": ["your_user_uuids"],
        "administered_by": [],
        "admin_contact": "your_email@your.org",
        "PREFERRED_URL_SCHEME": "https",
        "url_prefix": "/",
    }

    ERROR_INVALID_SERVER = "Unknown OAuth SSH Server ({server})"
    ERROR_MISSING_INPUT = "Missing command or server name input"
    ERROR_DEPENDENT_TOKEN = "Could not obtain dependent tokens for ssh server"
