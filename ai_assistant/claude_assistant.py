"""
Claude AI Assistant Integration
Conversational interface for Excel automation
"""
import anthropic
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class ClaudeAssistant:
    """AI Assistant for natural language data operations"""
    
    def __init__(self, api_key: str, conversation_log_dir: Path = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history = []
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Conversation logging
        if conversation_log_dir is None:
            conversation_log_dir = Path(__file__).parent.parent / "logs" / "conversations"
        self.log_dir = conversation_log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # System prompt for Excel operations
        self.system_prompt = """You are an expert Excel automation assistant. Your role is to help users clean and process their CSV/Excel data.

Available operations include:
- Text operations: uppercase, lowercase, concatenate, split, find/replace, trim
- Data operations: VLOOKUP, remove duplicates, sort, filter
- Cleaning: remove blanks, fill missing values
- Math: add columns, multiply, divide, round
- Dates: format dates, extract parts
- Validation: check emails, phones, required fields
- Conditional: flag if contains, IF/THEN rules

When a user requests an operation:
1. Clarify any ambiguities in their request
2. Confirm column names and parameters
3. Suggest the specific operation(s) needed
4. Explain what will happen in simple terms

Always be helpful, clear, and ask clarifying questions when needed."""
    
    def chat(self, user_message: str, df_info: Optional[Dict] = None) -> str:
        """
        Send message to Claude and get response
        
        Args:
            user_message: User's message
            df_info: Optional info about current DataFrame (columns, shape, etc.)
        
        Returns:
            Assistant's response
        """
        # Add data context if available
        context = ""
        if df_info:
            context = f"\n\nCurrent data file info:\n"
            context += f"- Rows: {df_info.get('rows', 'unknown')}\n"
            context += f"- Columns: {', '.join(df_info.get('columns', []))}\n"
        
        full_message = user_message + context
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": full_message
        })
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=self.system_prompt,
                messages=self.conversation_history
            )
            
            assistant_message = response.content[0].text
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            # Log conversation
            self._log_conversation(user_message, assistant_message, df_info)
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"Error communicating with AI: {str(e)}"
            self._log_error(error_msg)
            return error_msg
    
    def clear_conversation(self):
        """Clear conversation history and start fresh"""
        # Save current conversation before clearing
        if self.conversation_history:
            self._save_conversation_summary()
        
        self.conversation_history = []
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _log_conversation(self, user_msg: str, assistant_msg: str, df_info: Optional[Dict]):
        """Log conversation turn to file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.current_session_id,
            "user_message": user_msg,
            "assistant_response": assistant_msg,
            "data_context": df_info
        }
        
        # Append to session log
        log_file = self.log_dir / f"session_{self.current_session_id}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_error(self, error: str):
        """Log error"""
        error_log = self.log_dir / "errors.log"
        with open(error_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {error}\n")
    
    def _save_conversation_summary(self):
        """Save conversation summary for training analysis"""
        summary = {
            "session_id": self.current_session_id,
            "start_time": self.conversation_history[0].get("timestamp") if self.conversation_history else None,
            "end_time": datetime.now().isoformat(),
            "total_turns": len(self.conversation_history) // 2,
            "conversation": self.conversation_history
        }
        
        summary_file = self.log_dir / f"summary_{self.current_session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def get_conversation_history(self) -> List[Dict]:
        """Get current conversation history"""
        return self.conversation_history.copy()
    
    def suggest_operations(self, user_intent: str, df: pd.DataFrame) -> Dict:
        """
        Analyze user intent and suggest specific operations
        
        Returns:
            Dict with suggested operations and parameters
        """
        df_info = {
            "rows": len(df),
            "columns": list(df.columns),
            "sample": df.head(3).to_dict()
        }
        
        prompt = f"""Based on this request: "{user_intent}"

And this data:
{json.dumps(df_info, indent=2)}

Suggest specific operations to accomplish the task. Format as JSON:
{{
  "operations": [
    {{
      "operation_id": "text_uppercase",
      "operation_name": "Convert to UPPERCASE",
      "parameters": {{"columns": ["Company Name"]}}
    }}
  ],
  "explanation": "This will convert company names to uppercase for consistency"
}}"""
        
        response = self.chat(prompt, df_info)
        
        try:
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "operations": [],
            "explanation": response
        }
