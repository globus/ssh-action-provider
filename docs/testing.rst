Testing
=======

These tests assume that the DynamoDB database is locally accessible.

.. note::
   To make it easy to startup the database for local development, there's a
   helper script in :code:`scripts/setup-local-dev.py` which will create the
   database locally and configure its ports. Using this script to setup the test
   environment is optional.

This repo supports local testing in a development environment.


Local Development Testing Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No AWS Dependencies
-------------------

Setup: Go to :code:`developers.globus.org`, create a new client and secret as
outlined `here <https://docs.globus.org/api/auth/developer-guide/#register-app>`_

Export this secret into the SSH_AP_CLIENT_SECRET environment variable like so:

.. code-block:: BASH

    export SSH_AP_CLIENT_SECRET=<Globus Auth secret>


Then, run the tests:

.. code-block:: bash

    make test


Appendix
^^^^^^^^

TBD
