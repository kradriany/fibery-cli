"""Shared fixtures for fibery-tests.

Loads the fibery CLI script as a Python module so unit tests can call its
functions directly. Integration/sandbox tests invoke the CLI via subprocess
instead.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "fibery"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_WORKSPACE = os.environ.get("FIBERY_TEST_WORKSPACE", "myworkspace")
TEST_WORKSPACE_HOST = os.environ.get("FIBERY_TEST_WORKSPACE_HOST")
TEST_TOKEN = os.environ.get("FIBERY_TEST_TOKEN") or os.environ.get("FIBERY_TOKEN")
TEST_SANDBOX_SPACE = os.environ.get("FIBERY_TEST_SANDBOX_SPACE", "Sandbox")
TEST_SANDBOX_DB = os.environ.get("FIBERY_TEST_SANDBOX_DB", f"{TEST_SANDBOX_SPACE}/Database 1")
TEST_TASK_TYPE = os.environ.get("FIBERY_TEST_TASK_TYPE", "Task Management/Task")


@pytest.fixture(scope="session")
def fibery_cli():
    """Load the repo-local fibery script as a module so internals can be unit-tested.

    The file has no .py extension, so spec_from_file_location returns None
    unless we pass an explicit loader.
    """
    loader = SourceFileLoader("fibery_cli", str(CLI_PATH))
    spec = importlib.util.spec_from_loader("fibery_cli", loader)
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules so @dataclass can resolve type annotations via
    # sys.modules.get(cls.__module__). Without this, dataclass introspection
    # of the Ctx class fails during module load.
    sys.modules["fibery_cli"] = module
    loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def cli_run():
    """Return a callable that runs the repo-local fibery CLI."""
    def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(CLI_PATH), *args],
            capture_output=True,
            text=True,
            check=check,
            timeout=60,
        )
    return _run


@pytest.fixture(scope="session")
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def workspace_cli_run(cli_run):
    """Run the CLI against the configured live test workspace."""
    def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
        prefix = [TEST_WORKSPACE]
        if TEST_WORKSPACE_HOST:
            prefix.extend(["--workspace-host", TEST_WORKSPACE_HOST])
        if TEST_TOKEN:
            prefix.extend(["--token", TEST_TOKEN])
        return cli_run(*prefix, *args, check=check)
    return _run


@pytest.fixture(scope="session")
def live_test_settings():
    return {
        "workspace": TEST_WORKSPACE,
        "workspace_host": TEST_WORKSPACE_HOST,
        "sandbox_space": TEST_SANDBOX_SPACE,
        "sandbox_db": TEST_SANDBOX_DB,
        "task_type": TEST_TASK_TYPE,
    }


def pytest_collection_modifyitems(config, items):
    """Skip destructive sandbox tests unless PYTEST_FIBERY_SANDBOX=1 is set."""
    if os.environ.get("PYTEST_FIBERY_SANDBOX") == "1":
        return
    skip_sandbox = pytest.mark.skip(reason="Set PYTEST_FIBERY_SANDBOX=1 to run")
    for item in items:
        if "sandbox" in item.keywords or "test_sandbox" in item.nodeid:
            item.add_marker(skip_sandbox)
