"""
Query objects tool - for graph database queries
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import Tool as LangChainTool
from .base import BaseTool
import json


class QueryObjectsInput(BaseModel):
    """Input schema for query objects tool"""
    query: str = Field(
        description="Query string for searching objects in the graph database"
    )


class QueryObjectsTool(BaseTool):
    """Tool for querying objects from graph database"""
    
    @classmethod
    def from_config(cls, tool_config: Dict[str, Any]) -> LangChainTool:
        """
        Create query objects tool from configuration
        
        Args:
            tool_config: Dictionary containing tool configuration
                - name: Tool name (default: "query_objects")
                - description: Tool description
                - objects: List of queryable objects with their schemas
                    - object_code: Object identifier
                    - object_description: Object description
                    - fields: List of object fields
                        - field_name: Field name
                        - field_description: Field description
                        - field_type: Field data type
                
        Returns:
            LangChain Tool instance
        """
        # Capture objects configuration for closure
        objects = tool_config.get('objects', [])
        
        async def query_func(query: str) -> str:
            return await cls.execute(objects=objects, query=query)
        
        # Build detailed description with object schemas
        description = tool_config.get('description', 'Query objects from graph database')
        
        if objects:
            description += "\n\nAvailable objects:"
            for obj in objects:
                obj_code = obj.get('object_code', 'unknown')
                obj_desc = obj.get('object_description', '')
                description += f"\n- {obj_code}: {obj_desc}"
                
                fields = obj.get('fields', [])
                if fields:
                    field_names = [f.get('field_name', '') for f in fields]
                    description += f" (Fields: {', '.join(field_names)})"
        
        return LangChainTool(
            name=tool_config.get('name', 'query_objects'),
            description=description,
            func=query_func,
            args_schema=QueryObjectsInput,
            coroutine=query_func
        )
    
    @staticmethod
    def get_input_schema() -> type[BaseModel]:
        """Get the input schema for query objects tool"""
        return QueryObjectsInput
    
    @staticmethod
    async def execute(objects: List[Dict[str, Any]] | None = None, query: str = '', **kwargs) -> str:
        """
        Execute graph database query
        
        Args:
            objects: List of queryable object schemas
            query: Search query string
            
        Returns:
            Query results as formatted string
        """
        if not objects:
            objects = []
        
        # TODO: Implement actual graph database integration
        # This is a placeholder that returns object schema information
        
        result_parts = [
            f"Graph Database Query: '{query}'",
            "\n=== Available Objects ===\n"
        ]
        
        for obj in objects:
            obj_code = obj.get('object_code', 'unknown')
            obj_desc = obj.get('object_description', 'No description')
            
            result_parts.append(f"\n**{obj_code}**")
            result_parts.append(f"Description: {obj_desc}")
            
            fields = obj.get('fields', [])
            if fields:
                result_parts.append("Fields:")
                for field in fields:
                    field_name = field.get('field_name', 'unknown')
                    field_desc = field.get('field_description', 'No description')
                    field_type = field.get('field_type', 'string')
                    result_parts.append(f"  - {field_name} ({field_type}): {field_desc}")
        
        result_parts.append("\n=== Query Results ===")
        result_parts.append("(Placeholder: Graph database integration pending)")
        result_parts.append(f"Query matched {len(objects)} object type(s)")
        
        return "\n".join(result_parts)
    
    @staticmethod
    def format_object_schema(objects: List[Dict[str, Any]]) -> str:
        """
        Format object schemas for display
        
        Args:
            objects: List of object schemas
            
        Returns:
            Formatted schema string
        """
        schema_parts = []
        
        for obj in objects:
            obj_info = {
                'object_code': obj.get('object_code'),
                'object_description': obj.get('object_description'),
                'fields': [
                    {
                        'name': f.get('field_name'),
                        'type': f.get('field_type'),
                        'description': f.get('field_description')
                    }
                    for f in obj.get('fields', [])
                ]
            }
            schema_parts.append(json.dumps(obj_info, ensure_ascii=False, indent=2))
        
        return "\n\n".join(schema_parts)
