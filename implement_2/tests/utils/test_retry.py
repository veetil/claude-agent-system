"""Tests for retry utilities"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch

from claude_multi_agent.utils.retry import retry_with_backoff


class TestRetryDecorator:
    """Test retry_with_backoff decorator"""
    
    def test_sync_function_success_first_try(self):
        """Test successful sync function on first attempt"""
        @retry_with_backoff(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_sync_function_success_after_retries(self):
        """Test sync function succeeds after failures"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 3
    
    def test_sync_function_max_attempts_exceeded(self):
        """Test sync function fails after max attempts"""
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def always_failing_function():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_failing_function()
    
    @pytest.mark.asyncio
    async def test_async_function_success_first_try(self):
        """Test successful async function on first attempt"""
        @retry_with_backoff(max_attempts=3)
        async def async_successful_function():
            return "async_success"
        
        result = await async_successful_function()
        assert result == "async_success"
    
    @pytest.mark.asyncio
    async def test_async_function_success_after_retries(self):
        """Test async function succeeds after failures"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        async def async_flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "async_success"
        
        result = await async_flaky_function()
        assert result == "async_success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_function_max_attempts_exceeded(self):
        """Test async function fails after max attempts"""
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        async def async_always_failing_function():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await async_always_failing_function()
    
    def test_specific_exceptions_only(self):
        """Test retry only on specific exception types"""
        call_count = 0
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exceptions=(ConnectionError,)
        )
        def selective_retry_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Retryable error")
            elif call_count == 2:
                raise ValueError("Non-retryable error")
            return "success"
        
        with pytest.raises(ValueError, match="Non-retryable error"):
            selective_retry_function()
        
        assert call_count == 2  # Should have retried once, then failed
    
    def test_exponential_backoff_timing(self):
        """Test exponential backoff delays"""
        delays = []
        
        @retry_with_backoff(
            max_attempts=4,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False  # Disable jitter for predictable testing
        )
        def timing_test_function():
            start_time = time.time()
            delays.append(start_time)
            raise ConnectionError("Test timing")
        
        with pytest.raises(ConnectionError):
            timing_test_function()
        
        # Should have 4 attempts total
        assert len(delays) == 4
        
        # Check that delays are approximately exponential
        # Note: We can't check exact timing due to test execution overhead
        # but we can verify the function was called the right number of times
    
    @patch('time.sleep')
    def test_sync_delay_calculation(self, mock_sleep):
        """Test sync delay calculation with mocked sleep"""
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        def delay_test_function():
            raise ConnectionError("Test delay")
        
        with pytest.raises(ConnectionError):
            delay_test_function()
        
        # Should have called sleep twice (between 3 attempts)
        assert mock_sleep.call_count == 2
        
        # Check delay progression: 1.0, 2.0
        expected_delays = [1.0, 2.0]
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays
    
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_async_delay_calculation(self, mock_sleep):
        """Test async delay calculation with mocked sleep"""
        mock_sleep.return_value = None  # asyncio.sleep is async
        
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False
        )
        async def async_delay_test_function():
            raise ConnectionError("Test delay")
        
        with pytest.raises(ConnectionError):
            await async_delay_test_function()
        
        # Should have called sleep twice (between 3 attempts)
        assert mock_sleep.call_count == 2
        
        # Check delay progression: 1.0, 2.0
        expected_delays = [1.0, 2.0]
        actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert actual_delays == expected_delays
    
    def test_max_delay_cap(self):
        """Test that delays are capped at max_delay"""
        @retry_with_backoff(
            max_attempts=5,
            initial_delay=10.0,
            max_delay=15.0,
            exponential_base=2.0,
            jitter=False
        )
        def max_delay_test():
            raise ConnectionError("Test max delay")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(ConnectionError):
                max_delay_test()
            
            # Get all delay values
            delays = [call.args[0] for call in mock_sleep.call_args_list]
            
            # All delays should be <= max_delay
            for delay in delays:
                assert delay <= 15.0
    
    def test_jitter_variation(self):
        """Test that jitter creates variation in delays"""
        delays = []
        
        def capture_delay_function():
            @retry_with_backoff(
                max_attempts=2,
                initial_delay=1.0,
                jitter=True
            )
            def jitter_test():
                raise ConnectionError("Test jitter")
            
            with patch('time.sleep') as mock_sleep:
                try:
                    jitter_test()
                except ConnectionError:
                    pass
                
                if mock_sleep.call_args_list:
                    delays.append(mock_sleep.call_args_list[0].args[0])
        
        # Run multiple times to check jitter variation
        for _ in range(10):
            capture_delay_function()
        
        # With jitter, delays should vary (not all the same)
        unique_delays = set(delays)
        assert len(unique_delays) > 1, "Jitter should create variation in delays"
    
    def test_function_with_arguments(self):
        """Test retry decorator with function arguments"""
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        def function_with_args(x, y, z="default"):
            if x < 2:
                raise ValueError("x too small")
            return f"{x}-{y}-{z}"
        
        # Should succeed on first try
        result = function_with_args(5, "test", z="custom")
        assert result == "5-test-custom"
        
        # Should fail after retries
        with pytest.raises(ValueError):
            function_with_args(1, "test")
    
    @pytest.mark.asyncio
    async def test_async_function_with_arguments(self):
        """Test retry decorator with async function arguments"""
        @retry_with_backoff(max_attempts=2, initial_delay=0.01)
        async def async_function_with_args(x, y, z="default"):
            if x < 2:
                raise ValueError("x too small")
            return f"async-{x}-{y}-{z}"
        
        # Should succeed on first try
        result = await async_function_with_args(5, "test", z="custom")
        assert result == "async-5-test-custom"
        
        # Should fail after retries
        with pytest.raises(ValueError):
            await async_function_with_args(1, "test")


class TestRetryConfiguration:
    """Test different retry configurations"""
    
    def test_single_attempt_no_retry(self):
        """Test with max_attempts=1 (no retry)"""
        call_count = 0
        
        @retry_with_backoff(max_attempts=1)
        def no_retry_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Should not retry")
        
        with pytest.raises(ValueError):
            no_retry_function()
        
        assert call_count == 1
    
    def test_zero_initial_delay(self):
        """Test with zero initial delay"""
        @retry_with_backoff(max_attempts=2, initial_delay=0.0)
        def zero_delay_function():
            raise ConnectionError("Test zero delay")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(ConnectionError):
                zero_delay_function()
            
            # Should still call sleep with 0.0
            mock_sleep.assert_called_once_with(0.0)
    
    def test_custom_exponential_base(self):
        """Test with custom exponential base"""
        @retry_with_backoff(
            max_attempts=3,
            initial_delay=1.0,
            exponential_base=3.0,
            jitter=False
        )
        def custom_base_function():
            raise ConnectionError("Test custom base")
        
        with patch('time.sleep') as mock_sleep:
            with pytest.raises(ConnectionError):
                custom_base_function()
            
            # Should use base 3: delays should be 1.0, 3.0
            expected_delays = [1.0, 3.0]
            actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
            assert actual_delays == expected_delays