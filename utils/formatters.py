"""
Prompt formatting and template processing utilities
"""

from typing import Any, Dict


class PromptFormatter:
    """Handles prompt formatting and template processing"""
    
    @staticmethod
    def format_user_input(
        template: str,
        user_input: Any,
        input_data: Dict[str, Any] | None = None
    ) -> str:
        """
        Format user input with template
        
        Args:
            template: Prompt template with placeholders
            user_input: User's input (string, dict, or other types)
            input_data: Additional structured data for template
            
        Returns:
            Formatted prompt string
        """
        input_data = input_data or {}
        
        try:
            if isinstance(user_input, str):
                return template.format(user_input=user_input, **input_data)
            elif isinstance(user_input, dict):
                return template.format(
                    user_input=str(user_input),
                    **user_input,
                    **input_data
                )
            else:
                return template.format(user_input=str(user_input), **input_data)
        except (KeyError, TypeError):
            # Fallback if template formatting fails
            return f"用户输入：{user_input}\n{template}"
    
    @staticmethod
    def add_tool_guidance(system_prompt: str, has_tools: bool) -> str:
        """
        Add tool usage guidance to system prompt
        
        Args:
            system_prompt: Original system prompt
            has_tools: Whether the agent has tools available
            
        Returns:
            Enhanced system prompt with tool guidance
        """
        if not has_tools:
            return system_prompt
        
        tool_guidance = (
            "\n\n重要指导原则："
            "\n1. 当需要使用工具时，调用相应的工具获取信息。"
            "\n2. 工具返回结果后，基于结果给出最终答案，不要重复调用同一工具。"
            "\n3. 如果工具已经提供了答案，直接使用该答案回复用户，不要再次调用工具。"
            "\n4. 一旦得到所需信息，立即给出完整的最终回复，结束对话。"
        )
        
        return system_prompt + tool_guidance
