from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails
from datetime import datetime
import yaml
from typing import List, Dict, Optional
from ascii_colors import ASCIIColors, trace_exception
from lollms.config import TypedConfig, ConfigTemplate, BaseConfig
import os

class SummarizeFile(FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        static_parameters = TypedConfig(
            ConfigTemplate([
                {
                    "name": "chunk_processing_format",
                    "type": "str",
                    "value": "bullet points",
                    "options": ["bullet points", "article meta data", "paragraph", "key-value pairs"],
                    "help": """Defines how chunks are processed and stored in memory during summarization. 
                    - 'bullet points': List format
                    - 'article meta data': Extracts metadata-like information
                    - 'paragraph': Narrative format
                    - 'key-value pairs': Structured key-value format"""
                },
                {
                    "name": "contextual_summary_information",
                    "type": "str",
                    "value": "",
                    "help": """Custom instructions for filtering or extracting specific information from chunks. 
                    Examples: 'Focus on statistical data', 'Extract only quotes', 'Prioritize conclusions'"""
                },
                {
                    "name": "summary_style",
                    "type": "str",
                    "value": "concise",
                    "options": ["concise", "detailed", "executive", "technical"],
                    "help": """Controls the final summary style:
                    - 'concise': Short and to the point
                    - 'detailed': Comprehensive with more context
                    - 'executive': High-level overview for decision-making
                    - 'technical': Focus on technical details"""
                },
                {
                    "name": "context_size",
                    "type": "int",
                    "value": 128000,
                    "min": 1024,
                    "max": 256000,
                    "help": """The maximum context size for the language model."""
                },
                {
                    "name": "chunk_size",
                    "type": "int",
                    "value": 4096,
                    "min": 512,
                    "max": 16384,
                    "help": """Size of each text chunk to process."""
                },
                {
                    "name": "language_level",
                    "type": "str",
                    "value": "standard",
                    "options": ["simple", "standard", "advanced"],
                    "help": """Adjusts the complexity of language in the summary:
                    - 'simple': Basic vocabulary
                    - 'standard': Average readability
                    - 'advanced': Sophisticated terminology"""
                },
                {
                    "name": "include_timestamps",
                    "type": "bool",
                    "value": False,
                    "help": """If True, adds approximate location references (e.g., 'from page 1') to summary points."""
                },
            ]),
            BaseConfig(config={})
        )
        super().__init__("summarize_file", app, FunctionType.CLASSIC, client, static_parameters)
        self.personality = app.personality

    def execute(self, context: LollmsContextDetails, file_path: str) -> str:
        # Validate file existence
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found."

        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()
            if not file_content.strip():
                return "Error: File is empty."
        except Exception as e:
            return f"Error reading file: {str(e)}"

        # Build chunk processing prompt with enhanced instructions
        chunk_processing_prompt = (
            "Analyze the current text chunk and extract relevant information to update the memory.\n"
            f"Processing format: {self.static_parameters.chunk_processing_format}.\n"
            "Instructions:\n"
            "- Identify key points, facts, or insights relevant to the document's purpose.\n"
            "- Ignore redundant or trivial details unless specified otherwise.\n"
        )
        
        if self.static_parameters.chunk_processing_format == "bullet points":
            chunk_processing_prompt += "- Organize memory as concise bullet points.\n"
        elif self.static_parameters.chunk_processing_format == "article meta data":
            chunk_processing_prompt += "- Extract metadata such as author, date, title, or source if present.\n"
        elif self.static_parameters.chunk_processing_format == "paragraph":
            chunk_processing_prompt += "- Store information as coherent paragraphs.\n"
        elif self.static_parameters.chunk_processing_format == "key-value pairs":
            chunk_processing_prompt += "- Structure memory as key-value pairs (e.g., 'Topic: Summary').\n"

        if self.static_parameters.contextual_summary_information:
            chunk_processing_prompt += f"Additional focus: {self.static_parameters.contextual_summary_information}\n"
        
        if self.static_parameters.include_timestamps:
            chunk_processing_prompt += "- Include approximate location references (e.g., 'near chunk start') where relevant.\n"
        
        chunk_processing_prompt += (
            "- If no new information is found, preserve the existing memory unchanged.\n"
            "- Ensure clarity and relevance in all extracted data.\n"
        )

        # Build final summary prompt based on style and language level
        final_memory_processing_prompt = (
            "Synthesize the memory into a final summary.\n"
            f"Summary style: {self.static_parameters.summary_style}.\n"
            f"Language level: {self.static_parameters.language_level}.\n"
            "Instructions:\n"
        )
        
        if self.static_parameters.summary_style == "concise":
            final_memory_processing_prompt += "- Provide a brief, high-level summary with minimal elaboration.\n"
        elif self.static_parameters.summary_style == "detailed":
            final_memory_processing_prompt += "- Include comprehensive details and context for each key point.\n"
        elif self.static_parameters.summary_style == "executive":
            final_memory_processing_prompt += "- Focus on high-level insights and implications, suitable for decision-makers.\n"
        elif self.static_parameters.summary_style == "technical":
            final_memory_processing_prompt += "- Emphasize technical details, data, and specifics.\n"

        if self.static_parameters.language_level == "simple":
            final_memory_processing_prompt += "- Use simple words and short sentences.\n"
        elif self.static_parameters.language_level == "advanced":
            final_memory_processing_prompt += "- Use precise, sophisticated language where appropriate.\n"

        # Perform summarization
        try:
            summary = self.personality.sequential_summarize(
                text=file_content,
                chunk_processing_prompt=chunk_processing_prompt,
                chunk_processing_output_format="markdown",
                final_memory_processing_prompt=final_memory_processing_prompt,
                final_output_format="markdown",
                ctx_size=self.static_parameters.context_size,
                chunk_size=self.static_parameters.chunk_size,
                bootstrap_chunk_size=None,
                bootstrap_steps=None,
                callback=self.personality.sink,
                debug=False
            )
            return summary if summary else "No summary generated."
        except Exception as e:
            trace_exception(e)  # Log the exception for debugging
            return f"Error during summarization: {str(e)}"