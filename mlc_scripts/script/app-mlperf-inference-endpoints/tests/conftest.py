# SPDX-License-Identifier: Apache-2.0
"""Pytest configuration for the endpoints workflow tests."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: end-to-end workflow tests that invoke mlcr against the "
        "bundled echo server",
    )
