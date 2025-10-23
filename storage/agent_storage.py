"""Agent persistence storage implementation"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from models import AgentConfig


class AgentStorage:
    """Handle agent configuration persistence to JSON file"""
    
    def __init__(self, storage_file: str = "agents_storage.json"):
        """Initialize storage with file path
        
        Args:
            storage_file: Path to the JSON storage file
        """
        self.storage_file = Path(storage_file)
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        if not self.storage_file.exists():
            self.storage_file.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding='utf-8')
    
    def save_agent(self, agent_id: str, config: AgentConfig) -> None:
        """Save agent configuration to storage
        
        Args:
            agent_id: Unique identifier for the agent
            config: Agent configuration to save
        """
        agents = self.load_all_agents()
        agents[agent_id] = config.model_dump()
        self.storage_file.write_text(
            json.dumps(agents, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def load_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Load agent configuration from storage
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            AgentConfig if found, None otherwise
        """
        agents = self.load_all_agents()
        if agent_id in agents:
            return AgentConfig(**agents[agent_id])
        return None
    
    def load_all_agents(self) -> Dict[str, dict]:
        """Load all agent configurations from storage
        
        Returns:
            Dictionary mapping agent_id to configuration dict
        """
        try:
            return json.loads(self.storage_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent configuration from storage
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if deleted, False if not found
        """
        agents = self.load_all_agents()
        if agent_id in agents:
            del agents[agent_id]
            self.storage_file.write_text(
                json.dumps(agents, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            return True
        return False
    
    def get_agent_list(self) -> List[Dict]:
        """Get list of all agent configurations
        
        Returns:
            List of agent configuration dictionaries
        """
        agents = self.load_all_agents()
        result = []
        for agent_id, data in agents.items():
            # Handle both old and new storage formats
            # New format: {name, description, ...} (direct config fields)
            if "config" in data and isinstance(data["config"], dict):
                # Old format - extract config and add id
                agent_data = {"id": agent_id, **data["config"]}
            else:
                # New format - use data directly with id
                agent_data = {"id": agent_id, **data}
            result.append(agent_data)
        return result
    
    def agent_exists(self, agent_id: str) -> bool:
        """Check if agent exists in storage
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if agent exists, False otherwise
        """
        agents = self.load_all_agents()
        return agent_id in agents
