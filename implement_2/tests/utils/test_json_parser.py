"""Tests for JSON parser utilities"""

import json
import pytest

from claude_multi_agent.utils.json_parser import RobustJSONParser


class TestRobustJSONParser:
    """Test RobustJSONParser functionality"""
    
    def test_parse_clean_json(self):
        """Test parsing clean JSON"""
        clean_json = '{"session_id": "abc123", "result": "Hello world"}'
        result = RobustJSONParser.parse_mixed_output(clean_json)
        
        assert result["session_id"] == "abc123"
        assert result["result"] == "Hello world"
    
    def test_parse_json_with_shell_prefix(self):
        """Test parsing JSON with shell output prefix"""
        mixed_output = '''Loading configuration...
Starting Claude CLI...
{"session_id": "xyz789", "result": "Task completed"}'''
        
        result = RobustJSONParser.parse_mixed_output(mixed_output)
        assert result["session_id"] == "xyz789"
        assert result["result"] == "Task completed"
    
    def test_parse_multiline_json(self):
        """Test parsing multiline JSON"""
        multiline_json = '''Shell output here
{
  "session_id": "multi123",
  "result": "Complex result",
  "metadata": {
    "tokens": 150
  }
}
More shell output'''
        
        result = RobustJSONParser.parse_mixed_output(multiline_json)
        assert result["session_id"] == "multi123"
        assert result["result"] == "Complex result"
        assert result["metadata"]["tokens"] == 150
    
    def test_parse_json_single_line_mixed(self):
        """Test parsing single line JSON mixed with other text"""
        mixed_line = 'prefix text {"session_id": "line123", "result": "success"} suffix text'
        
        result = RobustJSONParser.parse_mixed_output(mixed_line)
        assert result["session_id"] == "line123"
        assert result["result"] == "success"
    
    def test_parse_no_json_raises_error(self):
        """Test that parsing non-JSON text raises ValueError"""
        no_json_text = '''This is just plain text
with no JSON content
at all'''
        
        with pytest.raises(ValueError, match="No valid JSON found"):
            RobustJSONParser.parse_mixed_output(no_json_text)
    
    def test_parse_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_json = '{"session_id": "bad", "result": incomplete'
        
        with pytest.raises(ValueError, match="No valid JSON found"):
            RobustJSONParser.parse_mixed_output(malformed_json)
    
    def test_extract_session_id_standard(self):
        """Test extracting session ID from standard response"""
        response = {"session_id": "std123", "result": "test"}
        session_id = RobustJSONParser.extract_session_id(response)
        assert session_id == "std123"
    
    def test_extract_session_id_alternative_names(self):
        """Test extracting session ID with alternative field names"""
        test_cases = [
            ({"sessionId": "alt123"}, "alt123"),
            ({"sid": "short123"}, "short123"),
            ({"session_id": "primary123", "sid": "backup123"}, "primary123")  # should prefer session_id
        ]
        
        for response, expected in test_cases:
            session_id = RobustJSONParser.extract_session_id(response)
            assert session_id == expected
    
    def test_extract_session_id_none(self):
        """Test extracting session ID when none present"""
        response = {"result": "test", "other_field": "value"}
        session_id = RobustJSONParser.extract_session_id(response)
        assert session_id is None
    
    def test_extract_session_id_numeric(self):
        """Test extracting numeric session ID"""
        response = {"session_id": 12345}
        session_id = RobustJSONParser.extract_session_id(response)
        assert session_id == "12345"
    
    def test_extract_result_standard(self):
        """Test extracting result from standard response"""
        response = {"result": "Standard result text"}
        result = RobustJSONParser.extract_result(response)
        assert result == "Standard result text"
    
    def test_extract_result_alternative_names(self):
        """Test extracting result with alternative field names"""
        test_cases = [
            ({"message": "Message text"}, "Message text"),
            ({"response": "Response text"}, "Response text"),
            ({"output": "Output text"}, "Output text"),
            ({"text": "Text content"}, "Text content"),
            ({"result": "primary", "message": "backup"}, "primary")  # should prefer result
        ]
        
        for response, expected in test_cases:
            result = RobustJSONParser.extract_result(response)
            assert result == expected
    
    def test_extract_result_fallback_to_json(self):
        """Test extracting result falls back to full JSON when no standard field"""
        response = {"unknown_field": "value", "other_data": 123}
        result = RobustJSONParser.extract_result(response)
        
        # Should return formatted JSON
        parsed_result = json.loads(result)
        assert parsed_result == response
    
    def test_extract_result_empty_fields(self):
        """Test extracting result when standard fields are empty"""
        response = {"result": "", "message": "Fallback message"}
        result = RobustJSONParser.extract_result(response)
        assert result == "Fallback message"
    
    def test_extract_metadata_standard(self):
        """Test extracting metadata from standard response"""
        metadata = {"tokens_used": 150, "duration_ms": 2000}
        response = {"result": "test", "metadata": metadata}
        
        extracted = RobustJSONParser.extract_metadata(response)
        assert extracted == metadata
    
    def test_extract_metadata_alternative_names(self):
        """Test extracting metadata with alternative field names"""
        test_cases = [
            ({"meta": {"key": "value"}}, {"key": "value"}),
            ({"info": {"duration": 1000}}, {"duration": 1000}),
            ({"metadata": {"primary": True}, "meta": {"backup": True}}, {"primary": True})
        ]
        
        for response, expected in test_cases:
            metadata = RobustJSONParser.extract_metadata(response)
            assert metadata == expected
    
    def test_extract_metadata_from_known_fields(self):
        """Test extracting metadata from known top-level fields"""
        response = {
            "result": "test",
            "tokens_used": 100,
            "duration_ms": 1500,
            "model": "claude-opus-4",
            "unknown_field": "ignored"
        }
        
        metadata = RobustJSONParser.extract_metadata(response)
        expected = {
            "tokens_used": 100,
            "duration_ms": 1500,
            "model": "claude-opus-4"
        }
        assert metadata == expected
    
    def test_extract_metadata_none(self):
        """Test extracting metadata when none present"""
        response = {"result": "test", "session_id": "123"}
        metadata = RobustJSONParser.extract_metadata(response)
        assert metadata is None
    
    def test_extract_metadata_invalid_type(self):
        """Test extracting metadata when field is not a dict"""
        response = {"metadata": "not a dict", "result": "test"}
        metadata = RobustJSONParser.extract_metadata(response)
        assert metadata is None


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_string(self):
        """Test parsing empty string"""
        with pytest.raises(ValueError):
            RobustJSONParser.parse_mixed_output("")
    
    def test_whitespace_only(self):
        """Test parsing whitespace-only string"""
        with pytest.raises(ValueError):
            RobustJSONParser.parse_mixed_output("   \n  \t  ")
    
    def test_nested_json_objects(self):
        """Test parsing with deeply nested JSON"""
        nested_json = '''{
  "session_id": "nested123",
  "result": {
    "data": {
      "items": [
        {"id": 1, "name": "item1"},
        {"id": 2, "name": "item2"}
      ]
    }
  }
}'''
        
        result = RobustJSONParser.parse_mixed_output(nested_json)
        assert result["session_id"] == "nested123"
        assert len(result["result"]["data"]["items"]) == 2
        assert result["result"]["data"]["items"][0]["name"] == "item1"
    
    def test_json_with_escaped_characters(self):
        """Test parsing JSON with escaped characters"""
        escaped_json = '{"result": "Message with \\"quotes\\" and \\n newlines"}'
        
        result = RobustJSONParser.parse_mixed_output(escaped_json)
        assert '"quotes"' in result["result"]
        assert '\n' in result["result"]