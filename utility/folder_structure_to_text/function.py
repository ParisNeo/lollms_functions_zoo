from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails
from pathlib import Path
from typing import List

class FolderStructureToText(FunctionCall):
    EXCLUDED_FOLDERS = {".git", "__pycache__", "node_modules", "target", "dist", "build", "venv"}
    EXCLUDED_EXTENSIONS = {".pyc", ".pyo", ".o", ".obj", ".class"}

    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__("folder_structure_to_text", app,FunctionType.CLASSIC, client)

    def update_context(self, context: LollmsContextDetails, constructed_context: List[str]):
        return constructed_context

    def execute(self, context: LollmsContextDetails, *args, **kwargs):
        try:
            folder_path = kwargs.get("folder_path", "")
            if not folder_path:
                return "Error: No folder path provided."

            folder = Path(folder_path)
            if not folder.exists() or not folder.is_dir():
                return "Error: The provided path is not a valid directory."

            output = self._generate_folder_structure(folder)
            return f"Folder Structure:\n{output}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _generate_folder_structure(self, folder: Path, indent: str = "") -> str:
        output = [f"{indent}- {folder.name}/"]
        
        for item in sorted(folder.iterdir()):
            if item.is_dir():
                if item.name not in self.EXCLUDED_FOLDERS:
                    subfolder_content = self._generate_folder_structure(item, indent + "  ")
                    output.append(subfolder_content)
            elif item.is_file() and self._is_text_file(item):
                output.append(f"{indent}  - {item.name}")
                file_content = self._read_file_content(item, indent + "    ")
                output.append(f"{indent}    ```{item.suffix[1:] if item.suffix else 'txt'}\n{file_content}\n{indent}    ```")
                output.append(f"{indent}    {'-' * 40}")
        
        return "\n".join(output).strip()

    def _is_text_file(self, file: Path) -> bool:
        return file.suffix.lower() not in self.EXCLUDED_EXTENSIONS and file.suffix.lower() in {".md", ".py", ".c", ".cpp", ".h", ".js", ".ts", ".json", ".yaml", ".txt", ".rs"}

    def _read_file_content(self, file: Path, indent: str) -> str:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            formatted_content = "\n".join([f"{indent}{line}" for line in content.splitlines()])
            return formatted_content if formatted_content else f"{indent}[Empty file]"
        except Exception as e:
            return f"{indent}Error reading file: {str(e)}"
