"""Agent lifecycle management (CRUD operations)"""

from typing import Dict, List, Optional
from models import AgentConfig
from storage import AgentStorage


class AgentManager:
    """Manage agent lifecycle and configuration"""
    
    def __init__(self, storage: Optional[AgentStorage] = None):
        """Initialize agent manager
        
        Args:
            storage: Agent storage instance (creates default if None)
        """
        self.storage = storage or AgentStorage()
        self._agents: Dict[str, AgentConfig] = {}
        self._load_persisted_agents()
    
    def _load_persisted_agents(self):
        """Load all persisted agents from storage into memory"""
        for agent_data in self.storage.get_agent_list():
            agent_id = agent_data["id"]
            
            # Handle both old and new storage formats
            # Old format: {id, config: {...}, created_at}
            # New format: {id, name, description, ...} (direct config)
            if "config" in agent_data:
                # Old format - extract the config object
                config_data = agent_data["config"]
            else:
                # New format - use agent_data directly
                config_data = agent_data
            
            config = AgentConfig(**config_data)
            self._agents[agent_id] = config
    
    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent
        
        Args:
            config: Agent configuration
            
        Returns:
            agent_id: Unique identifier for the created agent
        """
        if not config.id:
            raise ValueError("Agent config must have an id")
        
        agent_id = config.id
        
        # Save to memory
        self._agents[agent_id] = config
        
        # Persist to storage
        self.storage.save_agent(agent_id, config)
        
        return agent_id
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            AgentConfig if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def get_agent_list(self) -> List[Dict]:
        """Get list of all agents
        
        Returns:
            List of agent configuration dictionaries
        """
        return [
            {
                "id": agent_id,
                **config.dict()
            }
            for agent_id, config in self._agents.items()
        ]
    
    def update_agent(self, agent_id: str, config: AgentConfig) -> bool:
        """Update agent configuration
        
        Args:
            agent_id: Unique identifier for the agent
            config: New configuration
            
        Returns:
            True if updated, False if not found
        """
        if agent_id not in self._agents:
            return False
        
        # Update memory
        self._agents[agent_id] = config
        
        # Persist to storage
        self.storage.save_agent(agent_id, config)
        
        return True
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete agent
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if deleted, False if not found
        """
        if agent_id not in self._agents:
            return False
        
        # Remove from memory
        del self._agents[agent_id]
        
        # Remove from storage
        self.storage.delete_agent(agent_id)
        
        return True
    
    def agent_exists(self, agent_id: str) -> bool:
        """Check if agent exists
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            True if exists, False otherwise
        """
        return agent_id in self._agents
