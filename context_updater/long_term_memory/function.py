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
        super().__init__("long_term_memory", app, FunctionType.CONTEXT_UPDATE, client)
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
                    "--------- Long term memory -------\n"
                    "Long term memory contains important things you may need to know\n"
                    "It depicts important past information you need to know.\n"
                    "It will be automatically updated from the user prompt and your text.\n"
                    "Useless or irrelevant information can be removed just by saying so.\n"
                    "If the user asks to change the momory or to remove an entry confirm and it will be updated/removed by the system.\n"
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
            self.personality.step_start("Updating long term memory")
            # Read existing memory
            with open(self.memory_path, "r", encoding="utf-8") as f:
                current_memory = f.read().strip()

            if not current_memory:
                current_memory="No memories found yet."
            # Create memory update prompt
            update_prompt = f"""{self.app.template.system_full_header}Act as a memory shaping assistant. Use the existing memory as well as the cirrent interaction to build the new memory.
{self.app.template.system_custom_header('Existing Memory')}
{current_memory}

{self.app.template.system_custom_header('New Interaction')}
date:{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
prompt:{context.prompt}
response:{llm_output}

{self.app.template.system_custom_header('Instructions')}
As a memory manager, update the long-term memory by:
1. Adding important new information (facts, preferences, unique details)
2. Removing redundant/irrelevant information
3. Maintaining chronological order
4. Keeping entries concise
5. Preserving crucial historical context

Example of memory entry
--
Date: the date 
Information: interesting information extracted either from previous memories or current one
--

Output ONLY the updated memory content, without any additional commentary or formatting.
{self.app.template.ai_custom_header('assistant')}"""

            # Generate updated memory using AI
            updated_memory = self.personality.fast_gen(update_prompt, max_generation_size=2000,callback=self.personality.sink)
            
            # Save the AI-curated memory
            with open(self.memory_path, "w", encoding="utf-8") as f:
                f.write(updated_memory.strip())
            self.personality.step_end("Updating long term memory")

        except Exception as e:
            self.app.error(f"Error updating memory file: {e}")
            self.personality.step_end("Updating long term memory", False)

        return llm_output