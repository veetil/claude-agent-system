"""Robust JSON parsing utilities for Claude CLI responses"""

import json
import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RobustJSONParser:
    """Handles various JSON parsing scenarios from Claude CLI output"""
    
    @staticmethod
    def parse_mixed_output(text: str) -> Dict[str, Any]:
        """Parse JSON from mixed shell/JSON output
        
        Args:
            text: Raw output that may contain shell artifacts and JSON
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If no valid JSON found
        """
        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Try to find JSON object with regex
        json_match = re.search(r'\{.*?\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
                
        # Try line by line for multiline JSON
        lines = text.split('\n')
        
        # Find first line that starts with '{'
        json_start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                json_start_idx = i
                break
                
        if json_start_idx is not None:
            # Extract JSON lines
            json_lines = []
            brace_count = 0
            
            for line in lines[json_start_idx:]:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    break
                    
            json_text = '\n'.join(json_lines)
            try:
                return json.loads(json_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse extracted JSON: {json_text[:100]}...")
                
        # Try each line individually
        for line in lines:
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
                    
        raise ValueError("No valid JSON found in output")
    
    @staticmethod
    def extract_session_id(response: Dict) -> Optional[str]:
        """Safely extract session ID from response
        
        Args:
            response: Parsed JSON response
            
        Returns:
            Session ID if found, None otherwise
        """
        # Try different field names
        for field in ['session_id', 'sessionId', 'sid']:
            if field in response:
                return str(response[field])
        return None
    
    @staticmethod
    def extract_result(response: Dict) -> str:
        """Extract result text from various response formats
        
        Args:
            response: Parsed JSON response
            
        Returns:
            Result text
        """
        # Try different field names in order of preference
        for field in ['result', 'message', 'response', 'output', 'text']:
            if field in response and response[field]:
                return str(response[field])
        
        # If no standard field, return full response as JSON
        return json.dumps(response, indent=2)
    
    @staticmethod
    def extract_metadata(response: Dict) -> Optional[Dict[str, Any]]:
        """Extract metadata from response
        
        Args:
            response: Parsed JSON response
            
        Returns:
            Metadata dictionary if found, None otherwise
        """
        for field in ['metadata', 'meta', 'info']:
            if field in response and isinstance(response[field], dict):
                return response[field]
        
        # Create metadata from known fields
        metadata = {}
        for field in ['tokens_used', 'duration_ms', 'model', 'timestamp']:
            if field in response:
                metadata[field] = response[field]
                
        return metadata if metadata else None