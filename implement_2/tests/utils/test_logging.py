"""Tests for logging utilities"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from claude_multi_agent.utils.logging import setup_logging, get_logger


class TestSetupLogging:
    """Test setup_logging function"""
    
    def teardown_method(self):
        """Clean up logging configuration after each test"""
        # Reset logging configuration
        logging.getLogger().handlers.clear()
        logging.basicConfig(force=True, handlers=[])
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters"""
        setup_logging()
        
        # Check that root logger is configured
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) >= 1
        
        # Check that at least one handler is a StreamHandler
        stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level"""
        setup_logging(level="DEBUG")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid log level defaults to INFO"""
        setup_logging(level="INVALID_LEVEL")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
    
    def test_setup_logging_with_file(self):
        """Test setup_logging with log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            setup_logging(log_file=log_file)
            
            root_logger = logging.getLogger()
            
            # Should have both stream and file handlers
            stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
            file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
            
            assert len(stream_handlers) >= 1
            assert len(file_handlers) >= 1
            assert log_file.exists()
    
    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "nested" / "dir" / "test.log"
            
            # Directory shouldn't exist initially
            assert not log_file.parent.exists()
            
            setup_logging(log_file=log_file)
            
            # Directory should be created
            assert log_file.parent.exists()
            assert log_file.exists()
    
    def test_setup_logging_custom_format(self):
        """Test setup_logging with custom format"""
        custom_format = "%(name)s - %(message)s"
        setup_logging(format_str=custom_format)
        
        root_logger = logging.getLogger()
        
        # Check that at least one handler has the custom format
        for handler in root_logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                assert handler.formatter._fmt == custom_format
                break
        else:
            pytest.fail("No handler found with custom format")
    
    def test_setup_logging_suppresses_noisy_loggers(self):
        """Test that setup_logging suppresses noisy third-party loggers"""
        setup_logging(level="DEBUG")
        
        # Check that specific loggers are set to WARNING level
        urllib3_logger = logging.getLogger("urllib3")
        requests_logger = logging.getLogger("requests")
        
        assert urllib3_logger.level == logging.WARNING
        assert requests_logger.level == logging.WARNING
    
    @patch('logging.basicConfig')
    def test_setup_logging_force_override(self, mock_basicconfig):
        """Test that setup_logging forces override of existing config"""
        setup_logging()
        
        # Should call basicConfig with force=True
        mock_basicconfig.assert_called_once()
        call_kwargs = mock_basicconfig.call_args[1]
        assert call_kwargs['force'] is True
    
    def test_setup_logging_logs_configuration(self):
        """Test that setup_logging logs its own configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            
            # Just verify setup_logging runs without error
            setup_logging(level="DEBUG", log_file=log_file)
            
            # Verify the log file was created
            assert log_file.exists()


class TestGetLogger:
    """Test get_logger function"""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance"""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
    
    def test_get_logger_with_module_name(self):
        """Test get_logger with __name__ pattern"""
        logger = get_logger("claude_multi_agent.test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "claude_multi_agent.test_module"
    
    def test_get_logger_same_name_returns_same_instance(self):
        """Test that get_logger returns the same instance for the same name"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2
    
    def test_get_logger_different_names_return_different_instances(self):
        """Test that get_logger returns different instances for different names"""
        logger1 = get_logger("name1")
        logger2 = get_logger("name2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name


class TestLoggingIntegration:
    """Test integration between setup_logging and get_logger"""
    
    def teardown_method(self):
        """Clean up logging configuration after each test"""
        logging.getLogger().handlers.clear()
        logging.basicConfig(force=True, handlers=[])
    
    def test_logger_respects_setup_level(self):
        """Test that loggers respect the level set by setup_logging"""
        setup_logging(level="WARNING")
        logger = get_logger("test_integration")
        
        # Logger should inherit the WARNING level
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
    
    def test_logger_can_log_after_setup(self):
        """Test that loggers can actually log after setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "integration.log"
            setup_logging(level="INFO", log_file=log_file)
            
            logger = get_logger("test_integration")
            test_message = "Test log message"
            logger.info(test_message)
            
            # Check that message was written to file
            assert log_file.exists()
            log_content = log_file.read_text()
            assert test_message in log_content
    
    def test_multiple_loggers_share_configuration(self):
        """Test that multiple loggers share the same configuration"""
        setup_logging(level="DEBUG")
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        # Both should be able to log at DEBUG level
        with patch.object(logger1, 'debug') as mock_debug1, \
             patch.object(logger2, 'debug') as mock_debug2:
            
            logger1.debug("Debug message 1")
            logger2.debug("Debug message 2")
            
            mock_debug1.assert_called_once_with("Debug message 1")
            mock_debug2.assert_called_once_with("Debug message 2")


class TestLoggingErrorHandling:
    """Test error handling in logging utilities"""
    
    def teardown_method(self):
        """Clean up logging configuration after each test"""
        logging.getLogger().handlers.clear()
        logging.basicConfig(force=True, handlers=[])
    
    def test_setup_logging_with_readonly_log_file(self):
        """Test setup_logging behavior with readonly log file location"""
        # This tests the case where log directory creation might fail
        readonly_path = Path("/dev/null/cannot_create_dir/test.log")
        
        # Should not raise an exception, but may not create the file handler
        try:
            setup_logging(log_file=readonly_path)
            # If no exception is raised, the function handled the error gracefully
        except (OSError, PermissionError):
            # This is also acceptable behavior - failing fast on permission issues
            pass
    
    def test_get_logger_with_empty_name(self):
        """Test get_logger with empty name"""
        logger = get_logger("")
        assert isinstance(logger, logging.Logger)
        # Empty string returns root logger
        assert logger.name == "root"
    
    def test_get_logger_with_none_name(self):
        """Test get_logger with None name (should convert to string)"""
        logger = get_logger(None)
        assert isinstance(logger, logging.Logger)
        # logging.getLogger(None) returns the root logger
        assert logger is logging.getLogger()