"""Snowflake connection helpers for RetailIQ."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

import snowflake.connector
from snowflake.connector import SnowflakeConnection
from snowflake.connector.errors import Error as SnowflakeError

from src.utils.config import AppConfig, SNOWFLAKE_REQUIRED_CONFIG, get_config


logger = logging.getLogger(__name__)


class SnowflakeConfigurationError(RuntimeError):
    """Raised when required Snowflake settings are missing."""


def get_snowflake_connection(config: AppConfig | None = None) -> SnowflakeConnection:
    """Create a reusable Snowflake connection from environment configuration."""
    config = config or get_config()
    missing = config.missing(SNOWFLAKE_REQUIRED_CONFIG)
    authenticator = (config.snowflake_authenticator or "snowflake").lower()
    if authenticator in {"snowflake", "username_password_mfa"} and not config.snowflake_password:
        missing.append("snowflake_password")
    if missing:
        readable = ", ".join(missing)
        raise SnowflakeConfigurationError(f"Missing Snowflake configuration: {readable}")

    connection_kwargs = {
        "account": config.snowflake_account,
        "user": config.snowflake_user,
        "warehouse": config.snowflake_warehouse,
        "database": config.snowflake_database,
        "schema": config.snowflake_schema,
    }
    if config.snowflake_password:
        connection_kwargs["password"] = config.snowflake_password
    if config.snowflake_authenticator:
        connection_kwargs["authenticator"] = config.snowflake_authenticator
    if config.snowflake_passcode:
        connection_kwargs["passcode"] = config.snowflake_passcode
    if config.snowflake_passcode_in_password:
        connection_kwargs["passcode_in_password"] = True
    if config.snowflake_role:
        connection_kwargs["role"] = config.snowflake_role

    try:
        return snowflake.connector.connect(**connection_kwargs)
    except SnowflakeError as exc:
        logger.exception("Snowflake connection failed")
        raise ConnectionError(f"Unable to connect to Snowflake: {exc}") from exc


@contextmanager
def snowflake_connection(config: AppConfig | None = None) -> Iterator[SnowflakeConnection]:
    """Context manager that closes the Snowflake connection after use."""
    connection = get_snowflake_connection(config)
    try:
        yield connection
    finally:
        connection.close()


def test_snowflake_connection(config: AppConfig | None = None) -> tuple[bool, str]:
    """Return a lightweight connection status tuple for the Streamlit app."""
    try:
        with snowflake_connection(config) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()")
                database, schema, warehouse = cursor.fetchone()
        return True, f"Connected to {database}.{schema} using warehouse {warehouse}."
    except SnowflakeConfigurationError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001 - status checks should never crash the app
        logger.warning("Snowflake status check failed: %s", exc)
        return False, f"Snowflake connection check failed: {exc}"
