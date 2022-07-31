#!/usr/bin/env bash
#
# Helper script to build python packages
#

# Stop script on first error
set -e

VENV_CMD="pipenv run"
PACKAGES=promsrv

# Helper function to run one of the build functions declared in this file.
function _run_func {
    local FUNC=$1

    declare -F | grep -q ${FUNC}
    if [ $? != 0 ]; then
        echo "ERROR: Build function '${FUNC}' not found"
        exit 1
    else
        echo
        echo "INFO: Starting build function '${FUNC}'"
        ${FUNC}
        echo "INFO: Completed build function '${FUNC}'"
        echo
    fi
}


# Run pytest unit tests
function pytest() {
    ${VENV_CMD} pytest \
                --cov=promsrv \
                --cov-report html:build/pytest-cov \
                --verbose \
                ${PACKAGES}
}

# Run mypy static code analysis
function mypy() {
    for PKG in ${PACKAGES}; do
        MYPY_PKGS="${MYPY_PKGS} -p ${PKG}"
    done

    ${VENV_CMD} mypy ${MYPY_PKGS}
}

# Run pylint code linter
function pylint() {
    ${VENV_CMD} pylint ${PACKAGES}
}

# Build a wheel
function wheel() {
    ${VENV_CMD} python setup.py bdist_wheel
}

# Build a source distribution
function sdist() {
    ${VENV_CMD} python setup.py sdist
}

# Check if we are on valid tag
function check_git_version() {
    VERSION=$(git describe || true)
    if [ -z "${VERSION}" ]; then
        echo "ERROR: You are not on a git tag. No release build possible."
        exit 1
    fi

    echo ${VERSION} | egrep -q '[0-9]+\.[0-9]+\.[0-9]+(rc[0-9]+)?'
    if [ ! $? ]; then
        echo "ERROR: The version '${VERSION}' does not match the allowed versioning pattern."
        exit 1
    fi
}

# Set version in setup.cfg
function set_version() {
    VERSION=$(git describe)

    sed -E -i -e "s/^version = .*$/version = ${VERSION}/" setup.cfg
}

# Publish to pypi
function publish() {
    ${VENV_CMD} twine upload -r testpypi dist/*
}

# Run all QA tasks
function qa() {
    _run_func pytest
    _run_func mypy
    _run_func pylint
}

# Run all QA tasks, then build the package and publish it
function release() {
    _run_func check_git_version
    _run_func set_version
    _run_func pytest
    _run_func mypy
    _run_func pylint
    _run_func wheel
    _run_func sdist
    _run_func publish
}


CMD=$1
if [ -z "${CMD}" ]; then
    echo "ERROR: No build command specified"
    exit 1
fi

_run_func $CMD
