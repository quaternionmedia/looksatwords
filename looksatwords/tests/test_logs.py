"""Tests for the logs module."""
import logging
from looksatwords.logs import log


def test_log_exists():
    """Test that log object is created."""
    assert log is not None
    assert isinstance(log, logging.Logger)


def test_log_name():
    """Test that log has the correct name."""
    assert log.name == "rich"


def test_log_can_log():
    """Test that log can write messages."""
    # Test that logging methods exist and don't raise errors
    log.debug("Test debug message")
    log.info("Test info message")
    log.warning("Test warning message")
    assert True  # If we get here, logging worked
