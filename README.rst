libcurl-ct
==========

Python binding for the *libcurl* C library.

Overview
========

| Python |package_bold| module is a low-level binding for *libcurl* C library.
| It is an effort to allow python programs full access to the API implemented
  and provided by the well known `*libcurl* <https://curl.se/libcurl/>`__ library.

`PyPI record`_.

`Documentation`_.

| |package_bold| is a lightweight Python package, based on the *ctypes* library.
| It is fully compliant implementation of the original C *libcurl* API
  by implementing whole its functionality in a clean Python instead of C.
|
| *libcurl* API documentation can be found at:

  `libcurl API overview <https://curl.se/libcurl/c/libcurl.html>`__

|package_bold| uses the underlying *libcurl* C shared library as specified in
libcurl.cfg (included libcurl-X.X.* is the default), but there is also ability
to specify it programmatically by one of the following ways:

.. code:: python

  import libcurl
  libcurl.config(LIBCURL="libcurl C shared library absolute path")
  # or
  libcurl.config(LIBCURL=None)  # included libcurl-X.X.* will be use

About original libcurl:
-----------------------

Borrowed from the `original website <https://curl.se/libcurl/>`__:

**libcurl** - the multiprotocol file transfer library

**Overview**

**libcurl** is a free and easy-to-use client-side URL transfer library,
supporting DICT, FILE, FTP, FTPS, GOPHER, GOPHERS, HTTP, HTTPS, IMAP, IMAPS,
LDAP, LDAPS, MQTT, POP3, POP3S, RTMP, RTMPS, RTSP, SCP, SFTP, SMB, SMBS,
SMTP, SMTPS, TELNET and TFTP.

**libcurl** supports SSL certificates, HTTP POST, HTTP PUT, FTP uploading,
HTTP form based upload, proxies, HTTP/2, HTTP/3, cookies, user+password
authentication (Basic, Digest, NTLM, Negotiate, Kerberos), file transfer
resume, http proxy tunneling and more!

**libcurl** is highly portable, it builds and works identically on numerous
platforms, including Solaris, NetBSD, FreeBSD, OpenBSD, Darwin, HPUX, IRIX,
AIX, Tru64, Linux, UnixWare, HURD, Windows, Amiga, OS/2, BeOs, Mac OS X,
Ultrix, QNX, OpenVMS, RISC OS, Novell NetWare, DOS and more...

**libcurl** is free, thread-safe, IPv6 compatible, feature rich, well
supported, fast, thoroughly documented and is already used by many known,
big and successful companies. 

Requirements
============

- | It is a fully independent package.
  | All necessary things are installed during the normal installation process.
- ATTENTION: currently works and tested only for Windows.

Installation
============

Prerequisites:

+ Python 3.7 or higher

  * https://www.python.org/
  * 3.7 with C libcurl 7.84.0 is a primary test environment.

+ pip and setuptools

  * https://pypi.org/project/pip/
  * https://pypi.org/project/setuptools/

To install run:

  .. parsed-literal::

    python -m pip install --upgrade |package|

Development
===========

Prerequisites:

+ Development is strictly based on *tox*. To install it run::

    python -m pip install --upgrade tox

Visit `development page`_.

Installation from sources:

clone the sources:

  .. parsed-literal::

    git clone |respository| |package|

and run:

  .. parsed-literal::

    python -m pip install ./|package|

or on development mode:

  .. parsed-literal::

    python -m pip install --editable ./|package|

License
=======

  | Copyright (c) 2021-2022 Adam Karpierz
  | Licensed under the MIT License
  | https://opensource.org/licenses/MIT
  | Please refer to the accompanying LICENSE file.

Authors
=======

* Adam Karpierz <adam@karpierz.net>

.. |package| replace:: libcurl-ct
.. |package_bold| replace:: **libcurl-ct**
.. |respository| replace:: https://github.com/karpierz/libcurl.git
.. _development page: https://github.com/karpierz/libcurl
.. _PyPI record: https://pypi.org/project/libcurl-ct/
.. _Documentation: https://libcurl.readthedocs.io/
