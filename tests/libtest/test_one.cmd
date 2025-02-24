@echo off
pushd "%~dp0"
py test_one.py %*
popd
