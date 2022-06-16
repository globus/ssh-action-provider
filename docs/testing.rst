Testing
=======

These tests use local file storage for Action status using sqlite3


Local Development Testing Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setup: Go to :code:`developers.globus.org`, create a new client and secret as
outlined `here <https://docs.globus.org/api/auth/developer-guide/#register-app>`_

Export this secret into the SSH_AP_CLIENT_SECRET environment variable like so:

.. code-block:: BASH

    export SSH_AP_CLIENT_SECRET=<Globus Auth secret>


Then, run the tests from the root directory:

.. code-block:: bash

    make test

