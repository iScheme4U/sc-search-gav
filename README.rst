.. image:: https://badge.fury.io/py/sc-search-gav.svg
    :target: https://badge.fury.io/py/sc-search-gav
.. image:: https://img.shields.io/pypi/pyversions/sc-search-gav
    :alt: PyPI - Python Version

A simple Python project sample structure
========================================

This project provides a sample structure for creating python project.


Installation
------------

It is possible to install the tool with `pip`::

    pip install sc-search-gav

Configuration
-------------

First, make sure /var/opt/sc directory exists, if not create this directory and make sure current user has the right
to create files in this directory.

You can copy `default.yml <https://github.com/Scott-Lau/sc-search-gav/blob/master/sc_gav/tests/sample_config/default.yml>`_
to /var/opt/sc/.sc-search-gav/production.yml to initialize the production configuration.

The default configuration file looks like this::

    dev:
      # whether this program is running is development mode
      dev_mode: False


Dependencies
------------

* `sc-utilities <https://github.com/Scott-Lau/sc-utilities>`_ >= 0.0.2
* `sc-config <https://github.com/Scott-Lau/sc-config>`_ >= 0.0.3

Changes
-------

Version 0.0.1
    * Initial version

License
-------

The script is released under the MIT License.  The MIT License is registered
with and approved by the Open Source Initiative [1]_.

.. [1] https://opensource.org/licenses/MIT
