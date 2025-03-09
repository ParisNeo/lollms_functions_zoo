from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails
from datetime import datetime
import yaml
from typing import List, Dict
from ascii_colors import ASCIIColors, trace_exception
from lollms.config import TypedConfig, ConfigTemplate, BaseConfig
import os

class SummarizeFile(FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__("summarize_file", app, FunctionType.CLASSIC, client)
        self.personality = app.personality

    def update_context(self, context: LollmsContextDetails, constructed_context: List[str]):
        # No additional context needed for this function
        return constructed_context

    def execute(self, context: LollmsContextDetails, file_path: str):
        # Read the file content
        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

        # Call the sequential_summarize method
        try:
            summary = self.personality.sequential_summarize(
                text=file_content,
                chunk_processing_prompt="Extract relevant information from the current text chunk and update the memory if needed.",
                chunk_processing_output_format="markdown",
                final_memory_processing_prompt="Create final summary using this memory.",
                final_output_format="markdown",
                ctx_size=4096,  # Adjust based on the context size you want
                chunk_size=None,  # Let's use default chunk size
                bootstrap_chunk_size=None,
                bootstrap_steps=None,
                callback=self.personality.sink,
                debug=False
            )
        except Exception as e:
            return f"Error during summarization: {str(e)}"

        return summary