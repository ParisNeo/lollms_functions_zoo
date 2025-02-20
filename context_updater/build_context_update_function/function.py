from pathlib import Path
from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails
from datetime import datetime
import yaml
from typing import List
from ascii_colors import ASCIIColors, trace_exception

class BuildAFunction(FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__(FunctionType.CONTEXT_UPDATE, client)
        self.app = app
        self.personality = app.personality

    def update_context(self, context: LollmsContextDetails, constructed_context: List[str]):
        """Add instructions for building a function call to the context"""
        instructions = """
### How to Build a Function Call

To create a new function call, provide the following details:
1. **Function Name**: A unique name for the function (e.g., `my_function`).
2. **Description**: A brief description of what the function does.
3. **Parameters**: A list of parameters the function accepts (name, description, and type).
4. **Return Value**: A description of what the function returns.

The AI will generate the Python and YAML files for you. Here’s an example:


```yaml
author: The user name (default to ParisNeo)
category: custom # must be custom as this is a custom function
class_name: MyFunction
name: my_function
description: A custom function.
static_parameters: #static parameters are parameters set by the user not by the LLM and in general they don't change that much
- name: the static parameter name
  type: the type
  description: the description
  ...
parameters: # Parameters are parameters that do change depending on the request
- name: param1
  description: The first parameter.
  type: str (supported types are all default python types)
  ...
returns:
  status:
    description: The output of the function.
    type: str (only supports str)
version: 1.0.0
```

```python
from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
# Use pipmaster to check and install any missing module by its name
import pipmaster as pm
if not pm.is_installed("module name"):
    pm.install("module name")


class MyFunction(FunctionCall): #use the same name as class_name from the yaml file
    def __init__(self, app: LollmsApplication, client: Client, static_parameters:dict={}):
        super().__init__(FunctionType.CONTEXT_UPDATE, client)
        self.app = app
        # Make sur to use app.lollms_paths.personal_outputs_path for any output files the function will output unless secified by the user
        self.personality = app.personality # Personlity has many usefil LLM tools
        # Here are some of the functionalities of personality
        # 1 we can extract all code blocks from a string (useful if we need to make the AI build a code to execute or save)
        # self.personality.extract_code_blocks(llm_output)
        
    def update_context(self, context: LollmsContextDetails, constructed_context: List[str]):
        # Here you can add more instructions to the AI so that it can perform the task provided by the user correctly
        # You need to update the constructed_context list by adding extra information
        # You have access to all these informations from the context parameter:
        # --
        # client (str): Unique identifier for the client or user interacting with the LLM.
        # conditionning (Optional[str]): Optional field to store conditioning information or context for the LLM.
        # internet_search_infos (Optional[Dict]): Dictionary to store metadata or details about internet searches performed by the LLM.
        # internet_search_results (Optional[List]): List to store the results of internet searches performed by the LLM.
        # documentation (Optional[str]): Optional field to store documentation or reference material for the LLM.
        # documentation_entries (Optional[List]): List to store individual entries or sections of documentation.
        # user_description (Optional[str]): Optional field to store a description or profile of the user.
        # discussion_messages (Optional[List]): List to store the history of messages in the current discussion or conversation.
        # positive_boost (Optional[float]): Optional field to store a positive boost value for influencing LLM behavior.
        # negative_boost (Optional[float]): Optional field to store a negative boost value for influencing LLM behavior.
        # current_language (Optional[str]): Optional field to store the current language being used in the interaction.
        # fun_mode (Optional[bool]): Optional boolean field to enable or disable "fun mode" for the LLM.
        # think_first_mode (Optional[bool]): Optional boolean field to enable or disable "think first mode" for the LLM.
        # ai_prefix (Optional[str]): Optional field to store a prefix or identifier for the AI in the conversation.
        # extra (Optional[str]): Optional field to store additional custom or extra information.
        # available_space (Optional[int]): Optional field to store the available space or capacity for the context.
        # skills (Optional[Dict]): Dictionary to store skills or capabilities of the LLM.
        # is_continue (Optional[bool]): Optional boolean field to indicate if the LLM is continuing from a previous chunk or context.
        # previous_chunk (Optional[str]): Optional field to store the previous chunk of text or context.
        # prompt (Optional[str]): Optional field to store the current prompt or input for the LLM.
        # function_calls (Optional[List]): List to store function calls or actions performed by the LLM.
        # debug (bool): Enable or disable debug mode.
        # ctx_size (int): The maximum context size for the LLM.
        # max_n_predict (Optional[int]): The maximum number of tokens to generate.
        # model : The model (required to perform tokenization)
        # --
        # return the updated constructed_context

    def process_output(self, context: LollmsContextDetails, llm_output: str):
        # After the AI finish writing its answer we can post process it or do an extra thing after the end of the generation
        # llm_output contains the AI output, we still have access to the context if needed.
        # return a string 
```


"""
        constructed_context.append(instructions)
        return constructed_context

    def process_output(self, context: LollmsContextDetails, llm_output: str):
        """Generate Python and YAML files based on the AI's output"""
        try:
            # Extract code blocks from the AI's output
            codes = self.personality.extract_code_blocks(llm_output)
            if len(codes) >= 2:  # Expecting one Python and one YAML block
                python_code = None
                yaml_code = None

                for code in codes[:2]:
                    if code["type"] == "python":
                        python_code = code["content"]
                    elif code["type"] == "yaml":
                        yaml_code = code["content"]
                        yaml_data = yaml.safe_load(yaml_code)

                folder:Path = self.app.lollms_paths.custom_function_calls_path / yaml_data["name"]
                folder.mkdir(exist_ok=True, parents=True)
                with open(folder / f"function.py", "w", encoding="utf-8") as f:
                    f.write(python_code)

                with open(folder / f"config.yaml", "w", encoding="utf-8") as f:
                    f.write(yaml_code)

                return f"Function '{yaml_data['name']}' created successfully in '{folder}'!"
            else:
                return "Error: The AI was not smart enough to generate the required code blocks. Please try again."
        except Exception as e:
            trace_exception(e)
            return f"Error: {e}"