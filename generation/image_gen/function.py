import datetime
from lollms.app import LollmsApplication
from lollms.personality import AIPersonality
from lollms.function_call import FunctionCall, FunctionType
from lollms.prompting import LollmsContextDetails
from datetime import datetime
from typing import List
from lollms.utilities import discussion_path_to_url
from lollms.client_session import Client
from lollms.personality import APScript
from ascii_colors import trace_exception
from functools import partial
from lollms.functions.prompting.image_gen_prompts import get_image_gen_prompt, get_random_image_gen_prompt

def build_image(prompt, negative_prompt, width, height, personality:AIPersonality, client:Client, return_format="markdown"):
    try:
        if personality.app.tti!=None:
            personality.step_start("Painting")
            file, infos = personality.app.tti.paint(
                            prompt,
                            negative_prompt,
                            width = width,
                            height = height,
                            output_path=client.discussion.discussion_folder
                        )
            personality.step_end("Painting")
            
        file = str(file)
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


class ImageGen (FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__("image_gen", app, FunctionType.CLASSIC, client)

    def execute(self, context, *args, **kwargs):
        prompt = kwargs.get("prompt","")
        negative_prompt = kwargs.get("negative_prompt","")
        width = kwargs.get("width",1024)
        height = kwargs.get("height",512)
        
        return build_image(prompt, negative_prompt,width, height, self.personality, self.client)
    
        