Changelog
=========

8.12.1.4b1 (2025-03-01)
-----------------------
- Add support for Python 3.12 and 3.13
- Drop support for Python 3.7 and 3.8
- Add support for PyPy 3.10 and 3.11
- Drop support for PyPy 3.7, 3.8 and 3.9
- Upgrade: libcurl v.7.84.0 -> v.8.12.1
- Bugfix for type of version_info_data.feature_names.
- Bugfix for write_to_fd.
- | Previously unavailable obsoleted strequal() and strnequal()
  | are curently available.
- | Previously unavailable deprecated escape() and unescape()
  | are curently available.
- | Tox configuration has been moved to pyproject.toml
  | and now based on tox >= 4.0
- Many bugs fixed.
- Copyright year update.
- 100% code linting.
- Cleanup.
- Setup (dependencies) update.

7.84.0a2 (2022-08-27)
---------------------
- Upgrade: libcurl v.7.81.0 -> v.7.84.0
- Add support for Linux.
- Add support for Python 3.10 and 3.11
- Add support for PyPy 3.7, 3.8 and 3.9
- Added a performance util tests/sprinter.py
- Setup update (currently based mainly on pyproject.toml).

7.81.0a2 (2022-01-26)
---------------------
- Rename PyPi package to libcurl-ct due to name conflict.

7.81.0a1 (2022-01-26)
---------------------
- First release.

0.0.1 (2021-06-16)
------------------
- Initial release.
