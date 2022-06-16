SSH Action Provider
===================

Overview
--------

This repository contains an example [Action Provider](https://globus-automate-client.readthedocs.io/en/latest/globus_action_providers.html) for usage in Globus Automate flows.

It makes use of the [Globus Action Provider Tools library](https://github.com/globus/action-provider-tools) and the [Globus SDK](https://github.com/globus/globus-sdk-python) and requires access to an [OAuth enabled SSH server](https://github.com/XSEDE/oauth-ssh) endpoint on which to execute commands.

New Action Provider Setup
-------------------------

The Action Provider is an [OAuth Confidential Application](https://auth0.com/docs/get-started/applications/confidential-and-public-applications)

Setup: Go to [developers.globus.org](https://developers.globus.org/), create a new client and secret as
outlined [here](https://docs.globus.org/api/auth/developer-guide/#register-app)

Export the id and secret into the SSH_AP_CLIENT_ID/SECRET environment variable like so:

```
    export SSH_AP_CLIENT_ID="Globus Auth Client Id"
    export SSH_AP_CLIENT_SECRET="Globus Auth Client Secret"
```

Adding OAuth-SSH to a server
----------------------------

If you do not yet have an OAuth-SSH capable server that you wish to execute commands on,
please refer to the OAuth-SSH Server Setup [documentation](https://github.com/XSEDE/oauth-ssh/tree/master/server)

Pay particular attention to the 'Configure PAM to Use OAuth SSH' section 3.2
and its example configuration lines:

```
auth        required      pam_sepermit.so
auth        required      pam_env.so
auth        [success=done maxtries=die new_authtok_reqd=done default=ignore]    pam_oauth_ssh.so
auth        requisite     pam_succeed_if.so uid >= 1000 quiet_success
auth        required      pam_deny.so
```

And add the mappings of email/globus-account-UUID to local user account names, both the email and UUIDs to the desired account:

```
joe227@foo.com                        joe
8229a82e-d04c-478b-b2a9-f86219eee3d8  joe
94855e14-2b0d-4d85-861b-4e7d155625a2  jane
user123@example.com                   bob
2927e521-5582-4caf-897d-f978ec9a1c21  suzy
```

To test OAuth-SSH, issue the following commands and ensure that one is able
to get to a command prompt on the remote server:

```sh

    # This will redirect you to a browser to obtain your consent token
    #  and store it in a local file cache
    oauth-ssh-token authorize my.ssh.server.com

    # The following should yield a command prompt on the remote server
    oauth-ssh my.ssh.server.com
```


Adding an OAuth Static Dependency
*********************************

A dependency needs to be added to the SSH Action Provider Server to
the OAuth-SSH enabled server itself.

This allows Globus Auth to add the dependency to the list presented to the
user when the OAuth Grant Request is presented in the UI.

More information is available [here](https://docs.globus.org/api/auth/reference/#dependent_token_grant_post_v2oauth2token)

This dependency needs to be added only once per server, so is not part of the everyday usage code path.

One way to accomplish it is using the SDK.  A transcript follows:

```
$ python3
Python 3.8.9 (default, Apr 13 2022, 08:48:06)
[Clang 13.1.6 (clang-1316.0.21.2.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import os
>>> import sys
>>> from globus_sdk import ConfidentialAppAuthClient
>>> from paramiko import AutoAddPolicy
>>> from paramiko.client import SSHClient

>>> # Obtained from developers.globus.org confidential client creation
>>> MY_SSH_FQDN_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" 
>>> MY_SSH_FQDN_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx="
>>> c = ConfidentialAppAuthClient(
...     MY_SSH_FQDN_UUID, MY_SSH_FQDN_SECRET
... )
>>> resp = c.post('/v2/api/clients/xxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid/fqdns', json_body={"fqdn":"ssh.mydomain.org"})

>>> # Confirm creation of client scopes etc
>>> print(c.get(/v2/api/scopes))
>>> scope_resp = c.get('v2/api/scopes/xxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid')

>>> # Start constructing the scope dependency
>>> acmod = {'scope': scope_resp['scope']}
>>> acmod
{'scope': {'required_domains': [], 'dependent_scopes': [{'scope': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid', 'optional': False, 'requires_refresh_token': True}], 'description': 'Scope for all actions on SSH server', 'allows_refresh_token': True, 'client': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid', 'id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid', 'advertised': False, 'scope_string': 'https://auth.globus.org/scopes/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid/ssh', 'name': 'ssh'}}
>>> acmod['scope']['dependent_scopes']
[{'scope': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid', 'optional': False, 'requires_refresh_token': True}]
>>> acmod['scope']['dependent_scopes'].append({'optional':False,'requires_refresh_token': True,'scope':'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid'})
>>> acmod['scope']['dependent_scopes']
[{'scope': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid', 'optional': False, 'requires_refresh_token': True}, {'optional': False, 'requires_refresh_token': True, 'scope': '4c917f4e-9b38-49c3-a1b3-bc81cf79ae64'}, {'optional': False, 'requires_refresh_token': True, 'scope': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-uuid'}]
>>> c.put('/v2/api/scopes/v2/api/scopes/xxxxxxxxxxxxxxxxxxxxxxxxxx-uuid',data=acmod)

>>> # Check to see that the scopes were modified as desired
>>> result_scope = c.get('v2/api/scopes')
>>> print(result_scope)
```


Database Dependencies
*********************

No database dependencies are currently required, as task status are stored
in single node supported setup using sqlite3.

.. note::

    For dev-env-XX make commands to succeed, the Docker daemon must be
    installed and running. docker-compose should also be installed.


Development
-----------

To run the Action Provider locally for development and testing:

```sh
    ./run_local.sh
```

Testing
*******
    # for more information, see /docs/testing.rst.

```sh
    make test
```

