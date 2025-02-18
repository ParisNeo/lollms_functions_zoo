import datetime
from pathlib import Path
from lollms.app import LollmsApplication
from lollms.personality import AIPersonality
from lollms.function_call import FunctionCall, FunctionType
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails
from datetime import datetime
from typing import List

class LongTermMemoryFunction(FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__(FunctionType.CONTEXT_UPDATE, client)
        self.app = app
        self.personality = app.personality
        self.model = app.model
        
        # Set up memory file path
        self.memory_path = Path.home() / "memory.txt"
        if not self.memory_path.exists():
            self.memory_path.touch()

    def update_context(self, context: LollmsContextDetails, constructed_context: List[str]):
        """Add long-term memory to the context"""
        try:
            # Read memory file and add to context
            with open(self.memory_path, "r", encoding="utf-8") as f:
                memory_content = f.read().strip()
            
            if memory_content:
                constructed_context.append(
                    f"Long-term memory (last updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n"
                    f"{memory_content}\n"
                    "----------------------"
                )
        except Exception as e:
            self.app.error(f"Error reading memory file: {e}")
        
        return constructed_context

    def process_output(self, context: LollmsContextDetails, llm_output: str):
        """Use AI to curate and update memory with important information"""
        try:
            # Read existing memory
            with open(self.memory_path, "r", encoding="utf-8") as f:
                current_memory = f.read().strip()

            # Create memory update prompt
            update_prompt = f"""## Existing Memory:
{current_memory}

## New Interaction:
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]
Prompt: {context.prompt}
Response: {llm_output}

## Instructions:
As a memory manager, update the long-term memory by:
1. Adding important new information (facts, preferences, unique details)
2. Removing redundant/irrelevant information
3. Maintaining chronological order
4. Keeping entries concise
5. Preserving crucial historical context

Output ONLY the updated memory content, without any additional commentary or formatting."""

            # Generate updated memory using AI
            updated_memory = self.personality.fast_gen(update_prompt, max_generation_size=2000)
            
            # Save the AI-curated memory
            with open(self.memory_path, "w", encoding="utf-8") as f:
                f.write(updated_memory.strip())

        except Exception as e:
            self.app.error(f"Error updating memory file: {e}")
        
        return llm_output