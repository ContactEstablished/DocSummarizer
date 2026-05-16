"""Shared pytest fixtures."""

import os

import pytest

# Provide a dummy API key so Settings() can be instantiated without a real .env
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-key")


@pytest.fixture()
def anyio_backend():
    return "asyncio"
