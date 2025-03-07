import datetime
from lollms.app import LollmsApplication
from lollms.personality import AIPersonality
from lollms.function_call import FunctionCall, FunctionType
from lollms.prompting import LollmsContextDetails
from datetime import datetime
from typing import List, Optional, Dict, Any
from lollms.utilities import outputs_path_to_url
from lollms.client_session import Client
from lollms.personality import APScript
from ascii_colors import trace_exception
from lollms.config import TypedConfig, ConfigTemplate, BaseConfig


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
                    width: int = 512,
                    height: int = 512,
                    steps: int = 20,
                    seed: int = -1,
                    guidance_scale: Optional[float] = None,
                    loras: Optional[List[Dict[str, Any]]] = None,
                    embeddings: Optional[List[Dict[str, Any]]] = None,
                    closed_loop: Optional[bool] = None,
                    clip_skip: Optional[int] = None,                    
                    personality:AIPersonality=None, client:Client=None):
    try:
        personality = app.personality
        if app.ttv!=None:
            personality.step_start("Generating video (this can take a long while, be patient please ...)")
            file = app.ttv.generate_video(
                            prompt,
                            negative_prompt,
                            width=width,
                            height=height,
                            
                        )
            personality.step_end("Generating video (this can take a long while, be patient please ...)")
            url = outputs_path_to_url(file)
            
            app.personality.set_message_html(f"""<div style="width: 100%; max-width: 800px; margin: 0 auto;">
  <video controls style="width: 100%; height: auto;">
    <source src="{url}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>
""")
        return f"Generated video saved to : {file}"
    except Exception as ex:
        trace_exception(ex)


class VideoGen (FunctionCall):
    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__("video_gen", app, FunctionType.CLASSIC, client)

    def execute(self, context, *args, **kwargs):
        prompt = kwargs.get("prompt","")
        negative_prompt = kwargs.get("negative_prompt","")
        width = kwargs.get("width",1024)
        height = kwargs.get("height",512)
        
        return build_video(self.app, prompt, negative_prompt, width, height, self.personality, self.client)
    
        