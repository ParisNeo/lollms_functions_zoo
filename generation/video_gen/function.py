import datetime
from lollms.app import LollmsApplication
from lollms.personality import AIPersonality
from lollms.function_call import FunctionCall, FunctionType
from lollms.prompting import LollmsContextDetails
from datetime import datetime
from typing import List, Optional, Dict, Any
from lollms.utilities import discussion_path_to_url
from lollms.client_session import Client
from lollms.personality import APScript
from ascii_colors import trace_exception


def build_negative_prompt(image_generation_prompt:str, llm:LollmsApplication):
    start_header_id_template    = llm.config.start_header_id_template
    end_header_id_template      = llm.config.end_header_id_template
    system_message_template     = llm.config.system_message_template        

    return "\n".join([
                    f"{start_header_id_template}{system_message_template}{end_header_id_template}",
                    f"{llm.config.negative_prompt_generation_prompt}",
                    f"{start_header_id_template}image_generation_prompt{end_header_id_template}",
                    f"{image_generation_prompt}",
                    f"{start_header_id_template}negative_prompt{end_header_id_template}",
                ])    

def build_video(    app:LollmsApplication,
                    prompt, 
                    negative_prompt, 
                    height: int = 512,
                    width: int = 512,
                    steps: int = 20,
                    seed: int = -1,
                    guidance_scale: Optional[float] = None,
                    loras: Optional[List[Dict[str, Any]]] = None,
                    embeddings: Optional[List[Dict[str, Any]]] = None,
                    closed_loop: Optional[bool] = None,
                    clip_skip: Optional[int] = None,                    
                    personality:AIPersonality=None, client:Client=None, return_format="markdown"):
    try:
        personality = app.personality
        if app.ttv!=None:
            personality.step_start("Generating video (this can take a long while, be patient please ...)")
            file = app.ttv.generate_video(
                            prompt,
                            negative_prompt,
                            height=height,
                            width=width,
                            
                        )
            personality.step_end("Generating video (this can take a long while, be patient please ...)")
            
            escaped_url =  discussion_path_to_url(file)

            if return_format == "markdown":
                return f'\n![]({escaped_url})'
            elif return_format == "url":
                return escaped_url
            elif return_format == "path":
                return file
            elif return_format == "url_and_path":
                return {"url": escaped_url, "path": file}
            else:
                return f"Invalid return_format: {return_format}. Supported formats are 'markdown', 'url', 'path', and 'url_and_path'."
        else:
            return "No text to video service is configured. Please configure a service in the settings."
    except Exception as ex:
        trace_exception(ex)
        if return_format == "markdown":
            return f"\nCouldn't generate image. Make sure {personality.config.active_tti_service} service is installed"
        elif return_format == "url":
            return None
        elif return_format == "path":
            return None
        elif return_format == "url_and_path":
            return {"url": None, "path": None, "error":ex}
        else:
            return f"Couldn't generate image. Make sure {personality.config.active_tti_service} service is installed"


class VideoGen (FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client, static_parameters:dict={}):
        super().__init__(FunctionType.CLASSIC, client)
        self.app = app
        self.personality = app.personality
        self.model = app.model

    def execute(self, context, *args, **kwargs):
        prompt = kwargs.get("prompt","")
        negative_prompt = kwargs.get("negative_prompt","")
        width = kwargs.get("width",1024)
        height = kwargs.get("height",512)
        
        return build_video(self.app, prompt, negative_prompt, width, height, self.personality, self.client)
    
        