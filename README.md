SSH Action Provider
===================

Overview
--------

This repository contains an example `Action Provider <https://globus-automate-client.readthedocs.io/en/latest/globus_action_providers.html>`_ for usage in Globus Automate flows.

It makes use of the `Globus Action Provider Tools library<https://github.com/globus/action-provider-tools>`_ and the `Globus SDK <https://github.com/globus/globus-sdk-python>`_ and requires access to an `OAuth enabled SSH server<https://github.com/XSEDE/oauth-ssh>`_ endpoint on which to execute commands.

New Action Provider Setup
-------------------------
Setup: Go to :code:`developers.globus.org`, create a new client and secret as
outlined `here <https://docs.globus.org/api/auth/developer-guide/#register-app>`_

Export this secret into the SSH_AP_CLIENT_SECRET environment variable like so:

.. code-block:: BASH

    export SSH_AP_CLIENT_SECRET=<Globus Auth secret>


Database Dependencies
*********************

Automate testing and development relies on DynamoDB being locally available.
There is a helper docker-compose.yml definition in /scripts that,
when run, can start and stop these dependencies for you. These same definitions
can be used for local development and local testing.

To start the databases:

.. code-block:: bash

    make dev-env-up

To stop the databases:

.. code-block:: bash

    make dev-env-down

.. note::
    For these make commands to succeed, the Docker daemon must be
    installed and running. docker-compose should also be installed. Installation
    instructions can be found `here <https://docs.docker.com/get-docker/>`_.


Development
-----------

To run the Action Provider locally for development and testing:

.. code-block:: bash

    poetry shell
    ./localstach.sh
    ./run.sh

.. note::

TBD

Testing
*******

See /docs/testing.rst.

Running
*******

TBD
