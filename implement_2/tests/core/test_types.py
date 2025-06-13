"""Tests for core types"""

import pytest
from pathlib import Path
from dataclasses import fields

from claude_multi_agent.core.types import (
    AgentConfig, TaskInput, AgentResponse, FileMapping, 
    FolderMapping, OrchestrationResult, ExecutionStrategy
)
from claude_multi_agent.core.exceptions import ValidationError


class TestFileMapping:
    """Test FileMapping dataclass"""
    
    def test_file_mapping_creation(self):
        """Test basic FileMapping creation"""
        mapping = FileMapping(
            name="test.txt",
            src_path="/source/test.txt",
            dest_path="dest/test.txt"
        )
        
        assert mapping.name == "test.txt"
        assert mapping.src_path == "/source/test.txt"
        assert mapping.dest_path == "dest/test.txt"
    
    def test_file_mapping_required_fields(self):
        """Test that all fields are required"""
        # Should not be able to create without required fields
        with pytest.raises(TypeError):
            FileMapping()
        
        with pytest.raises(TypeError):
            FileMapping(name="test.txt")


class TestFolderMapping:
    """Test FolderMapping dataclass"""
    
    def test_folder_mapping_creation(self):
        """Test basic FolderMapping creation"""
        mapping = FolderMapping(
            src_path="/source/folder",
            dest_path="dest/folder",
            include_patterns=["*.py", "*.md"],
            exclude_patterns=["__pycache__"]
        )
        
        assert mapping.src_path == "/source/folder"
        assert mapping.dest_path == "dest/folder"
        assert mapping.include_patterns == ["*.py", "*.md"]
        assert mapping.exclude_patterns == ["__pycache__"]
    
    def test_folder_mapping_defaults(self):
        """Test default values for optional fields"""
        mapping = FolderMapping(
            src_path="/source",
            dest_path="dest"
        )
        
        assert mapping.include_patterns is None
        assert mapping.exclude_patterns is None


class TestAgentConfig:
    """Test AgentConfig dataclass"""
    
    def test_agent_config_minimal(self, temp_workspace):
        """Test minimal AgentConfig creation"""
        config = AgentConfig(
            id="test-agent",
            system_prompt="Test prompt",
            working_dir=temp_workspace
        )
        
        assert config.id == "test-agent"
        assert config.system_prompt == "Test prompt"
        assert config.working_dir == temp_workspace
        assert config.allowed_tools == []
        assert config.max_turns == 10
        assert config.timeout_seconds == 300
        assert config.environment_vars == {}
    
    def test_agent_config_full(self, temp_workspace):
        """Test full AgentConfig creation"""
        config = AgentConfig(
            id="test-agent",
            system_prompt="Test prompt",
            working_dir=temp_workspace,
            allowed_tools=["read_file", "write_file"],
            max_turns=5,
            timeout_seconds=600,
            environment_vars={"TEST_VAR": "value"}
        )
        
        assert config.allowed_tools == ["read_file", "write_file"]
        assert config.max_turns == 5
        assert config.timeout_seconds == 600
        assert config.environment_vars == {"TEST_VAR": "value"}
    
    def test_agent_config_validation(self, temp_workspace):
        """Test AgentConfig field validation"""
        # Test invalid max_turns
        with pytest.raises(ValidationError, match="max_turns must be positive"):
            AgentConfig(
                id="test",
                system_prompt="test",
                working_dir=temp_workspace,
                max_turns=0
            )
        
        # Test invalid timeout
        with pytest.raises(ValidationError, match="timeout_seconds must be positive"):
            AgentConfig(
                id="test",
                system_prompt="test", 
                working_dir=temp_workspace,
                timeout_seconds=-1
            )


class TestTaskInput:
    """Test TaskInput dataclass"""
    
    def test_task_input_minimal(self):
        """Test minimal TaskInput creation"""
        task = TaskInput(prompt="Test prompt")
        
        assert task.prompt == "Test prompt"
        assert task.text_input is None
        assert task.files == []
        assert task.folders == []
        assert task.dependencies == []
    
    def test_task_input_with_files(self):
        """Test TaskInput with file mappings"""
        file_mapping = FileMapping(
            name="test.txt",
            src_path="/src/test.txt",
            dest_path="test.txt"
        )
        
        task = TaskInput(
            prompt="Process file",
            files=[file_mapping]
        )
        
        assert len(task.files) == 1
        assert task.files[0].name == "test.txt"
    
    def test_task_input_with_folders(self):
        """Test TaskInput with folder mappings"""
        folder_mapping = FolderMapping(
            src_path="/src/data",
            dest_path="data"
        )
        
        task = TaskInput(
            prompt="Process folder",
            folders=[folder_mapping]
        )
        
        assert len(task.folders) == 1
        assert task.folders[0].src_path == "/src/data"


class TestAgentResponse:
    """Test AgentResponse dataclass"""
    
    def test_agent_response_creation(self):
        """Test basic AgentResponse creation"""
        response = AgentResponse(
            agent_id="test-agent",
            result="Test result",
            session_id="session-123"
        )
        
        assert response.agent_id == "test-agent"
        assert response.result == "Test result"
        assert response.session_id == "session-123"
        assert response.success is True
        assert response.error is None
        assert response.metadata == {}
    
    def test_agent_response_with_error(self):
        """Test AgentResponse with error"""
        response = AgentResponse(
            agent_id="test-agent",
            result="",
            session_id="session-123",
            success=False,
            error="Something went wrong"
        )
        
        assert response.success is False
        assert response.error == "Something went wrong"
    
    def test_agent_response_with_metadata(self):
        """Test AgentResponse with metadata"""
        metadata = {
            "tokens_used": 150,
            "duration_ms": 2000
        }
        
        response = AgentResponse(
            agent_id="test-agent",
            result="Test result",
            session_id="session-123",
            metadata=metadata
        )
        
        assert response.metadata == metadata


class TestExecutionStrategy:
    """Test ExecutionStrategy enum"""
    
    def test_execution_strategy_values(self):
        """Test ExecutionStrategy enum values"""
        assert ExecutionStrategy.SEQUENTIAL.value == "sequential"
        assert ExecutionStrategy.PARALLEL.value == "parallel"
        assert ExecutionStrategy.PIPELINE.value == "pipeline"
        assert ExecutionStrategy.HIERARCHICAL.value == "hierarchical"
    
    def test_execution_strategy_from_string(self):
        """Test creating ExecutionStrategy from string"""
        assert ExecutionStrategy("sequential") == ExecutionStrategy.SEQUENTIAL
        assert ExecutionStrategy("parallel") == ExecutionStrategy.PARALLEL
        assert ExecutionStrategy("pipeline") == ExecutionStrategy.PIPELINE
        assert ExecutionStrategy("hierarchical") == ExecutionStrategy.HIERARCHICAL


class TestOrchestrationResult:
    """Test OrchestrationResult dataclass"""
    
    def test_orchestration_result_empty(self):
        """Test empty OrchestrationResult"""
        result = OrchestrationResult()
        
        assert result.responses == []
        assert result.success is True
        assert result.error is None
        assert result.metadata == {}
    
    def test_orchestration_result_with_responses(self):
        """Test OrchestrationResult with agent responses"""
        response1 = AgentResponse(
            agent_id="agent-1",
            result="Result 1",
            session_id="session-1"
        )
        response2 = AgentResponse(
            agent_id="agent-2", 
            result="Result 2",
            session_id="session-2"
        )
        
        result = OrchestrationResult(
            responses=[response1, response2]
        )
        
        assert len(result.responses) == 2
        assert result.responses[0].agent_id == "agent-1"
        assert result.responses[1].agent_id == "agent-2"
    
    def test_orchestration_result_failed(self):
        """Test failed OrchestrationResult"""
        result = OrchestrationResult(
            success=False,
            error="Orchestration failed"
        )
        
        assert result.success is False
        assert result.error == "Orchestration failed"