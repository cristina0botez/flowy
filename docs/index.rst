Flowy Library Documentation
===========================


`Flowy`_ is a library that makes it easy to write distributed asynchronous
workflows. It uses `Amazon SWF`_ as backend. It is ideal for applications that
deal with media encoding, long-running tasks or background processing.

A simple registration workflow using Flowy looks like this::

    @workflow(name='subscribe', version='v1', task_list='my_list')
    class Subscribe(Workflow):

            register = ActivityProxy(name='register', version='v0.1')
            wait_for_confirmation = ActivityProxy(name='wait_for_confirmation',
                                                  version=3)
            send_welcome_message = ActivityProxy(name='welcome', version="1")

            def run(self, address):
                    register(address)
                    if wait_for_confirmation(address):
                       return send_welcome_message(address)
                    return False

See the :ref:`tutorial <tutorial>` for a narrative introduction of the Flowy
features.


Installation
------------

Flowy is available on the Python Package Index - to install it use `pip`_::

    pip install flowy


Tutorial
--------

.. toctree::
    :maxdepth: 2

    tutorial/tutorial


In Depth
--------

.. toctree::
    :maxdepth: 2

    indepth/activity
    indepth/workflow
    indepth/error
    indepth/settings
    indepth/transport
    indepth/versioning
    indepth/production
    indepth/contribute



.. _Flowy: http://github.com/pbs/flowy/
.. _Amazon SWF: http://aws.amazon.com/swf/
.. _pip: http://www.pip-installer.org/
