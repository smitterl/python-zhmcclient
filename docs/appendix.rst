.. Copyright 2016-2021 IBM Corp. All Rights Reserved.
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
..

.. _`Appendix`:

Appendix
========

This section contains information that is referenced from other sections,
and that does not really need to be read in sequence.


.. _`Troubleshooting`:

Troubleshooting
---------------

This section describes a few issues and how to address them.

No connection to the HMC
^^^^^^^^^^^^^^^^^^^^^^^^

If you get errors that indicate there is no connection at all to the HMC, for
example one of those errors:

.. code-block:: text

    Error: ConnectionError: HTTPSConnectionPool(host='10.11.12.13', port=6794): Max retries exceeded with url: /api/....
    (Caused by ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed: 403 Forbidden',)))

    Error: ConnectTimeout: HTTPSConnectionPool(host='10.11.12.13', port=6794): Max retries exceeded with url: /api/....
    (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x10a8c3910>, 'Connection to 10.11.12.13 timed out. (connect timeout=30)'))

then check all of the following:

* Does the HMC have its Web Services API enabled?

  Refer to the respective item in :ref:`Setting up the HMC` for how to do that.

  If that is not enabled, the ports used by the Web Services API will be
  inactive on the HMC.

* Do you have direct network connectivity to the HMC?

  You can test this with the following curl command:

  .. code-block:: bash

      $ curl -k https://10.11.12.13:6794/api/version
      {"api-major-version":4, .....

  If the HMC is reachable, this command displays JSON output with information
  about the HMC. Otherwise, it displays an error message. You can use the ``-v``
  option of curl to get more details.

  Using `ping` to verify connectivity is also a possibility, but there are
  network environments in which ICMP traffic is dropped, and there are also
  network environments where ping works but some tunnelling or proxy is set up
  that requires special measures to get IP traffic through. So in order to draw
  conclusions from a ping result, you need to know how the network environment
  is set up between the system where you use the zhmcclient and the targeted HMC.

  Having ping work is at least a good indication. If ping works but the curl
  command above does not, then one possible reason is that the Web Services API
  is not enabled on the HMC.

* Do you have a proxy setup to your HMC?

  In that case, you need to setup the proxy configuration such that you bypass
  the proxy. You need direct IP network connectivity between the system where
  you use the zhmcclient and the targeted HMC.

* Do you have a firewall to your HMC?

  In case of a boundary firewall, you may need to log on to the boundary
  firewall.

  Also, the firewall needs to permit the ports used by the HMC API. For details,
  see :ref:`Setting up firewalls or proxies`.

* Can you get to the HMC GUI via your web browser?

  If you can access the HMC GUI via your web browser but not the HMC API via
  the `curl` command shown above, then possible reasons are:

  - The HMC does not have its Web Services API enabled (see above).
  - There is a firewall to the HMC but it does not permit the ports used by
    the HMC API (see above).

ConnectionError with SSLV3_ALERT_HANDSHAKE_FAILURE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Symptom: The 'zhmcclient' package raises a :exc:`zhmcclient.ConnectionError`
exception with the following message:

.. code-block:: text

    [SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:1123)

The root cause is very likely that the HMC is set to TLS 1.2 only and has
disabled SSLv3 compatibility, and the OpenSSL package used by the Python on your
client system does not support TLS 1.2 yet.

To check which OpenSSL version is used by the Python on your client system,
issue this command (sample output is shown):

.. code-block:: bash

    $ python -c "import ssl; print(ssl.OPENSSL_VERSION)"
    OpenSSL 1.1.1i  8 Dec 2020

using the Python you have used when the 'zhmcclient' package raised the
exception.

To have support for TLS 1.2 you need OpenSSL version 1.0.1 or higher.

See also the :ref:`Security` section.

ConnectionError with CERTIFICATE_VERIFY_FAILED: self signed certificate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Symptom: The 'zhmcclient' package raises a :exc:`zhmcclient.ConnectionError`
exception with the following message:

.. code-block:: text

    [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate (_ssl.c:1125)

The root cause is that the HMC is set up to use a self-signed certificate
and the client has used ``verify_cert=True`` in the :class:`zhmcclient.Session`
initialization, which is the default. That causes the client to use the
Python 'certifi' package for verification of the server certificate and the
'certifi' package provides the CA certificates from the
`Mozilla Included CA Certificate List <https://wiki.mozilla.org/CA/Included_Certificates>`_
which does not include the self-signed certificate.

The issue can be temporarily circumvented by specifying ``verify_cert=False``,
which disables the verification of the server certificate. Since that makes
the connection vulnerable to man-in-the-middle attacks, it should be done
only as a temporary circumvention.

The solution is to have your HMC administrator obtain a CA-verifiable
certificate and to install that in the HMC.

See also the :ref:`Security` section.


.. _`BaseManager`:
.. _`BaseResource`:
.. _`Base classes for resources`:

Base classes for resources
--------------------------

.. automodule:: zhmcclient._manager

.. autoclass:: zhmcclient.BaseManager
   :members:
   :special-members: __str__

.. automodule:: zhmcclient._resource

.. autoclass:: zhmcclient.BaseResource
   :members:
   :special-members: __str__


.. _`Glossary`:

Glossary
--------

This documentation uses a few special terms:

.. glossary::

   HMC
      Hardware Management Console; the node the zhmcclient talks to.

   session-id
      an opaque string returned by the HMC as the result of a successful
      logon, for use by subsequent operations instead of credential data.
      The HMC gives each newly created session-id a lifetime of 10 hours, and
      expires it after that.

   fulfillment
      The act of satisfying requests for creation, modification, or deletion of
      storage volumes in a storage subsystem (i.e. of the actual storage
      backing a :term:`storage volume` object).

      Storage volume objects have a fulfillment state indicating whether the
      volume is fulfilled, which means that the request for creation or
      modification has been carried out and the state of the backing volume is
      now in sync with the storage volume object.

      :term:`Storage group` objects also have a fulfillment state indicating
      whether all of its storage volumes are fulfilled.


.. _`Special type names`:

Special type names
------------------

This documentation uses a few special terms to refer to Python types:

.. glossary::

   string
      a :term:`unicode string` or a :term:`byte string`

   unicode string
      a Unicode string type (:func:`unicode <py2:unicode>` in
      Python 2, and :class:`py3:str` in Python 3)

   byte string
      a byte string type (:class:`py2:str` in Python 2, and
      :class:`py3:bytes` in Python 3). Unless otherwise
      indicated, byte strings in this package are always UTF-8 encoded.

   number
      one of the number types :class:`py:int`, :class:`py2:long` (Python 2
      only), or :class:`py:float`.

   integer
      one of the integer types :class:`py:int` or :class:`py2:long` (Python 2
      only).

   timestamp
      a Timestamp-typed value as used in the HMC API. This is a non-negative
      :term:`integer` value representing a point in time as milliseconds since
      the UNIX epoch (1970-01-01 00:00:00 UTC), or the value -1 to indicate
      special treatment of the value.

   json object
      a :class:`py:dict` object that is a Python representation of a valid JSON
      object. See :ref:`py:py-to-json-table` for details.

   header dict
      a :class:`py:dict` object that specifies HTTP header fields, as follows:

        * `key` (:term:`string`): Name of the header field, in any lexical case.
          Dictionary key lookup is case sensitive, however.
        * `value` (:term:`string`): Value of the header field.

   callable
      a type for callable objects (e.g. a function, calling a class returns a
      new instance, instances are callable if they have a
      :meth:`~py:object.__call__` method).

   DeprecationWarning
      a standard Python warning that indicates the use of deprecated
      functionality. See section :ref:`Deprecations` for details.

   HMC API version
      an HMC API version, as a tuple of (api_major_version, api_minor_version),
      where:

      * `api_major_version` (:term:`integer`): The numeric major version of the
        HMC API.

      * `api_minor_version` (:term:`integer`): The numeric minor version of the
        HMC API.


.. _`Resource model`:

Resource model
--------------

This section lists the resources that are available at the :term:`HMC API`.

The term *resource* in this documentation is used to denote a managed object
in the system. The result of retrieving a resource through the HMC API is
termed a *resource representation*. Python classes for resources are termed to
*represent* a resource.

For resources within a :term:`CPC`, this section covers CPCs in DPM mode and
classic mode, but omits any resources that are available only in ensemble mode.
See section :ref:`CPCs` for a definition of the CPC modes.

Some of the items in this section are qualified as *short terms*. They are not
separate types of resources, but specific usages of resources. For example,
"storage adapter" is a short term for the resource "adapter" when used for
attaching storage.

Resources scoped to the HMC
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. glossary::

  Console
     The HMC itself.

  Group
     TBD - Not yet supported.

  Hardware Message
     TBD - Not yet supported.

     Also scoped to CPCs in any mode.

  Job
     The execution of an asynchronous HMC operation.

  LDAP Server Definition
     The information in an HMC about an LDAP server that may be used for
     HMC user authorization purposes.

  Metrics Context
     A user-created definition of metrics that can be retrieved.

  Password Rule
     A rule which HMC users need to follow when creating a HMC logon password.

  Session
     A session between a client of the HMC API and the HMC.

  Task
     An action that an HMC user with appropriate authority can perform.

  User
     An HMC user.

  User Pattern
     A pattern for HMC user IDs that are not defined on the HMC as users but
     can be verified by an LDAP server for user authentication.

  User Role
     An authority role which can be assigned to one or more HMC users.

Resources scoped to CPCs in any mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. glossary::

  Capacity Record
     TBD - Not yet supported.

  CPC
     Central Processor Complex, a physical IBM Z or LinuxONE computer.

     For details, see section :ref:`CPCs`.

Resources scoped to CPCs in DPM mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. glossary::

  Accelerator Adapter
     Short term for an :term:`Adapter` providing accelerator functions (e.g.
     the z Systems Enterprise Data Compression (zEDC) adapter for data
     compression).

  Adapter
     A physical adapter card (e.g. OSA-Express adapter, Crypto adapter) or a
     logical adapter (e.g. HiperSockets switch).

     For details, see section :ref:`Adapters`.

  Adapter Port
     Synonym for :term:`Port`.

  Capacity Group
     TBD - Not yet supported.

  Crypto Adapter
     Short term for an :term:`Adapter` providing cryptographic functions.

  FCP Adapter
     Short term for a :term:`Storage Adapter` supporting FCP (Fibre Channel
     Protocol).

  FCP Port
     Short term for a :term:`Port` of an :term:`FCP Adapter`.

  HBA
     A logical entity that provides a :term:`Partition` with access to
     external storage area networks (SANs) through an :term:`FCP Adapter`.

     For details, see section :ref:`HBAs`.

     HBA resource objects only exist when the "dpm-storage-management" feature
     is not enabled. See section :ref:`Storage Groups` for details.

  Network Adapter
     Short term for an :term:`Adapter` for attaching networks (e.g. OSA-Express
     adapter).

  Network Port
     Short term for a :term:`Port` of a :term:`Network Adapter`.

  NIC
     Network Interface Card, a logical entity that provides a
     :term:`Partition` with access to external communication networks through a
     :term:`Network Adapter`.

     For details, see section :ref:`NICs`.

  Partition
     A subset of the hardware resources of a :term:`CPC` in DPM mode,
     virtualized as a separate computer.

     For details, see section :ref:`Partitions`.

  Port
     The physical connector port (jack) of an :term:`Adapter`.

     For details, see section :ref:`Ports`.

  Storage Adapter
     Short term for an :term:`Adapter` for attaching storage.

  Storage Group
     A grouping entity for a set of FCP or ECKD (=FICON)
     :term:`storage volumes <storage volume>`. A storage group can be attached
     to a :term:`partition` which will cause its storage volumes to be attached
     to the partition.

     Storage Group objects exist only when the "dpm-storage-management"
     feature is enabled on the CPC.
     For details, see section :ref:`Storage Groups`.

  Storage Group Template
     A template for :term:`Storage Groups <Storage Group>`.

  Storage Port
     Short term for a :term:`Port` of a :term:`Storage Adapter`.

  Storage Volume
     An FCP or ECKD (=FICON) storage volume defined in context of a
     :term:`storage group`. The life cycle of a storage volume includes being
     defined but not :term:`fulfilled <fulfillment>`, being fulfilled but not
     attached, and finally being attached to a :term:`partition`.

     Storage Volume objects exist only when the "dpm-storage-management"
     feature is enabled on the CPC.
     For details, see section :ref:`Storage Groups`.

  Storage Volume Template
     A template for :term:`Storage Volumes <Storage Volume>`.

  vHBA
     Synonym for :term:`HBA`. In this resource model, HBAs are always
     virtualized because they belong to a :term:`Partition`. Therefore, the
     terms vHBA and HBA can be used interchangeably.

  Virtual Function
     A logical entity that provides a :term:`Partition` with access to an
     :term:`Accelerator Adapter`.

     For details, see section :ref:`Virtual functions`.

  Virtual Storage Resource
     A representation of a storage-related z/Architecture device in a
     :term:`partition`. For FCP type storage volumes, a Virtual Storage
     Resource object represents an :term:`HBA` through which the attached
     storage volume is accessed. For FICON (ECKD) type storage volumes, a
     Virtual Storage Resource object represents the attached storage volume
     itself.

     Virtual Storage Resource objects exist only when the
     "dpm-storage-management" feature is enabled on the CPC.
     For details, see section :ref:`Storage Groups`.

  Virtual Switch
     A virtualized networking switch connecting :term:`NICs <NIC>` with a
     :term:`Network Port`.

     For details, see section :ref:`Virtual switches`.

  vNIC
     Synonym for :term:`NIC`. In this resource model, NICs are always
     virtualized because they belong to a :term:`Partition`. Therefore, the
     terms vNIC and NIC can be used interchangeably.

Resources scoped to CPCs in classic (and ensemble) mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. glossary::

  Activation Profile
     A general term for specific types of activation profiles:

     * :term:`Reset Activation Profile`
     * :term:`Image Activation Profile`
     * :term:`Load Activation Profile`

  Group Profile
     TBD

  Image Activation Profile
     A specific :term:`Activation Profile` that defines characteristics of
     an :term:`LPAR`.

  Load Activation Profile
     A specific :term:`Activation Profile` that defines an operating system
     image that can be loaded (booted) into an :term:`LPAR`.

  Logical Partition
  LPAR
     A subset of the hardware resources of a :term:`CPC` in classic mode (or
     ensemble mode), virtualized as a separate computer.

     For details, see section :ref:`LPARs`.

  Reset Activation Profile
     A specific :term:`Activation Profile` that defines characteristics of a
     :term:`CPC`.


.. _`Bibliography`:

Bibliography
------------

.. glossary::

   X.509
      `ITU-T X.509, Information technology - Open Systems Interconnection - The Directory: Public-key and attribute certificate frameworks <http://www.itu.int/rec/T-REC-X.509/en>`_

   RFC2616
      `IETF RFC2616, Hypertext Transfer Protocol - HTTP/1.1, June 1999 <https://tools.ietf.org/html/rfc2616>`_

   RFC2617
      `IETF RFC2617, HTTP Authentication: Basic and Digest Access Authentication, June 1999 <https://tools.ietf.org/html/rfc2617>`_

   RFC3986
      `IETF RFC3986, Uniform Resource Identifier (URI): Generic Syntax, January 2005 <https://tools.ietf.org/html/rfc3986>`_

   RFC6874
      `IETF RFC6874, Representing IPv6 Zone Identifiers in Address Literals and Uniform Resource Identifiers, February 2013 <https://tools.ietf.org/html/rfc6874>`_

   HMC API
       The Web Services API of the z Systems Hardware Management Console, described in the following books:

   HMC API 2.11.1
       `IBM SC27-2616, System z Hardware Management Console Web Services API (Version 2.11.1) <https://www.ibm.com/support/pages/node/6017542>`_

   HMC API 2.12.0
       `IBM SC27-2617, System z Hardware Management Console Web Services API (Version 2.12.0) <https://www.ibm.com/support/pages/node/6019030>`_

   HMC API 2.12.1
       `IBM SC27-2626, System z Hardware Management Console Web Services API (Version 2.12.1) <https://www.ibm.com/support/pages/node/6017614>`_

   HMC API 2.13.0
       `IBM SC27-2627, z Systems Hardware Management Console Web Services API (Version 2.13.0) <https://www.ibm.com/support/pages/node/6018628>`_

   HMC API 2.13.1
       `IBM SC27-2634, z Systems Hardware Management Console Web Services API (Version 2.13.1) <https://www.ibm.com/support/pages/node/6019732>`_

   HMC API 2.14.0
       `IBM SC27-2636, IBM Z Hardware Management Console Web Services API (Version 2.14.0) <https://www.ibm.com/support/pages/node/6020008>`_

   HMC API 2.14.1
       `IBM SC27-2637, IBM Z Hardware Management Console Web Services API (Version 2.14.1) <https://www.ibm.com/support/pages/node/6019768>`_

   HMC API 2.15.0
       `IBM SC27-2638, IBM Z Hardware Management Console Web Services API (Version 2.15.0) <https://www.ibm.com/support/pages/node/6019720>`_
       (covers both GA1 and GA2)

   HMC API 2.16.0
       `IBM SC27-2642, IBM Z Hardware Management Console Web Services API (Version 2.16.0) <https://www.ibm.com/support/pages/node/6591083>`_
       (covers both GA1 and GA2)

   HMC Operations Guide
       The operations guide of the z Systems Hardware Management Console, in the following books (subset):

   HMC Operations Guide 2.11.1
       `IBM SC28-6905, System z Hardware Management Console Operations Guide (Version 2.11.1) <https://www.ibm.com/support/pages/node/6019948>`_

   HMC Operations Guide 2.12.1
       `System z Hardware Management Console Operations Guide (Version 2.12.1) <https://www.ibm.com/support/pages/node/6017692>`_

   HMC Operations Guide 2.13.1
       `z Systems Hardware Management Console Operations Guide (Version 2.13.1) <https://www.ibm.com/support/pages/node/6016846>`_

   HMC Operations Guide 2.14.1
       `Hardware Management Console Operations Guide (Version 2.14.1) <https://www.ibm.com/support/pages/node/6019132>`_

   HMC Operations Guide 2.15.0
       `Hardware Management Console Operations Guide (Version 2.15.0) <https://www.ibm.com/support/pages/node/6018724>`_
       (covers both GA1 and GA2)

   HMC Operations Guide 2.16.0
       `Hardware Management Console Operations Guide (Version 2.16.0) <https://www.ibm.com/support/pages/node/6619013>`_
       (covers both GA1 and GA2)

   HMC Security
       `Hardware Management Console Security <https://www.ibm.com/support/pages/node/6017320>`_


.. _`Related projects`:

Related projects
----------------

.. glossary::

   zhmccli project
      `zhmccli project at GitHub <https://github.com/zhmcclient/zhmccli>`_

   zhmccli package
      `zhmccli package on Pypi <https://pypi.python.org/pypi/zhmccli>`_
