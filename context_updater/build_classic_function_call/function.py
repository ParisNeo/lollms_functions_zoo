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
category: custom
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
#Use pipmaster to check and install any missing module by its name
import pipmaster as pm
if not pm.is_installed("module name"):
    pm.install("module name")


class MyFunction(FunctionCall): #use the same name as class_name from the yaml file
    def __init__(self, app: LollmsApplication, client: Client, static_parameters:dict):
        super().__init__(FunctionType.CLASSIC, client)
        self.app = app
        # extract the static parameters from the dictionary here. these are parameters that can be set by the user in the settings of the function call in the ui.
        # it is a simple dictionary
        self.personality = app.personality # Personlity has many usefil LLM tools
        # Here are some of the functionalities of personality
        # 1 we can call an LLM and make it generate text using fastgen method
        # text = self.personality.fastgen(prompt, callback=None)
        # callback is optional if used then it must be a function that takes the generated chunk, the chunk_type and a dict containing information
        #use self.personality.sink to prevent showing the generation chunks to the user.
        # summary = self.personality.sequential_summarize(
        #   text, # The text to summerize
        #   summary_context="", # this is a prompt to the ai when it is extracting information from the chunks and updating its memory content before doing the final extraction
        #   task="Create final summary using this memory.", # the final text synthesis after recovering all important informations from the text
        #   format="bullet points", #The output format
        #   tone="neutral", # The tone
        #   ctx_size=4096, #the size of context
        #   callback = None)
        # Ask the AI yes no question. Very useful to understand some text if we have two possibilities
        # answer = self.personality.yesno(
        #   question: str, # the question
        #   context:str="", # context about which the question is asked
        #   max_answer_length: int = None, conditionning="", return_explanation=False, callback = None)
        # 2 we can ask the ai to generate code 
        # self.personality.fastgen(prompt)
    def execute(self, *args, **kwargs):
        # You can recover the parameters stated in the yaml from kwargs
        #use kwargs.get("the parameter name",default value)
        return "Your output as a string"
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