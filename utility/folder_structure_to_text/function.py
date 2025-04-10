# -*- coding: utf-8 -*-
"""
=========================================================================
 Lollms Function Call: Folder Structure to Text
=========================================================================
Developed by: ParisNeo
Creation Date: 2025-03-03
Last Update: 2024-05-22 # Adjusted date
Version: 1.3.0
Description:
  Takes a folder path and generates a Markdown-formatted text representation.
  First, it displays the folder structure as a tree view (`|-`, `L-`).
  Second, it lists each included text file with its relative path and
  full content within Markdown code blocks. Allows specifying additional
  files or folders to exclude using wildcard patterns.
=========================================================================
"""
import fnmatch
import datetime
from pathlib import Path
from typing import List, Set, Tuple, Optional

# Use Lollms imports
from lollms.function_call import FunctionCall, FunctionType
from lollms.app import LollmsApplication
from lollms.client_session import Client
from lollms.prompting import LollmsContextDetails

# --- Configuration Constants (Keep previous constants: DEFAULT_EXCLUDED_FOLDERS, etc.) ---
DEFAULT_EXCLUDED_FOLDERS: Set[str] = {
    ".git", "__pycache__", "node_modules", "target", "dist", "build", "venv",
    ".vscode", ".idea", "logs", "temp", "tmp", "bin", "obj",
    "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis"
}
DEFAULT_EXCLUDED_EXTENSIONS: Set[str] = {
    ".pyc", ".pyo", ".o", ".obj", ".class", ".dll", ".so", ".exe", ".bin",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".jar", ".war",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg",
    ".mp3", ".wav", ".ogg", ".mp4", ".avi", ".mov", ".webm",
    ".db", ".sqlite", ".sqlite3", ".lock",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp",
    ".ttf", ".otf", ".woff", ".woff2",
    ".DS_Store", ".ipynb_checkpoints",
}
ALLOWED_TEXT_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".markdown", ".rst", ".adoc", ".asciidoc",
    ".py", ".java", ".js", ".ts", ".jsx", ".tsx", ".html", ".htm", ".css", ".scss", ".sass", ".less",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".swift", ".kt", ".kts",
    ".php", ".rb", ".pl", ".pm", ".lua", ".sh", ".bash", ".zsh", ".bat", ".ps1", ".psm1",
    ".sql", ".r", ".dart", ".groovy", ".scala", ".clj", ".cljs", ".cljc", ".edn",
    ".vb", ".vbs", ".f", ".for", ".f90", ".f95",
    ".json", ".yaml", ".yml", ".xml", ".toml", ".ini", ".cfg", ".conf", ".properties",
    ".csv", ".tsv", ".env",
    ".dockerfile", "dockerfile", ".tf", ".tfvars", ".hcl",
    ".gradle", ".pom", ".csproj", ".vbproj", ".sln",
    ".gitignore", ".gitattributes", ".npmrc", ".yarnrc", ".editorconfig",
    ".babelrc", ".eslintrc", ".prettierrc", ".stylelintrc",
    ".makefile", "makefile", "Makefile", "CMakeLists.txt",
    ".tex", ".bib", ".sty",
    ".graphql", ".gql", ".vue", ".svelte", ".astro", ".liquid", ".njk", ".jinja", ".jinja2",
    ".patch", ".diff",
}
TREE_BRANCH = "├─ "
TREE_LAST = "└─ "
TREE_VLINE = "│  "
TREE_SPACE = "   "
FOLDER_ICON = "📁"
FILE_ICON = "📄"
# --- End Constants ---


class FolderStructureToText(FunctionCall):
    """
    (Class Docstring serves as the 'header' in the code)
    =========================================================================
     Lollms Function Call: Folder Structure to Text
    =========================================================================
    Developed by: ParisNeo
    Creation Date: 2025-03-03
    Last Update: 2024-05-22 # Adjusted date
    Version: 1.3.0
    Description:
      Takes a folder path and generates a Markdown-formatted text representation.
      First, it displays the folder structure as a tree view (`|-`, `L-`).
      Second, it lists each included text file with its relative path and
      full content within Markdown code blocks. Allows specifying additional
      files or folders to exclude using wildcard patterns.
    =========================================================================
    """
    BASE_EXCLUDED_FOLDERS = DEFAULT_EXCLUDED_FOLDERS
    BASE_EXCLUDED_EXTENSIONS = DEFAULT_EXCLUDED_EXTENSIONS
    ALLOWED_TEXT_EXTENSIONS = ALLOWED_TEXT_EXTENSIONS

    def __init__(self, app: LollmsApplication, client: Client):
        super().__init__(
            function_name="folder_structure_to_text",
            app=app,
            function_type=FunctionType.CLASSIC,
            client=client
        )

    def update_context(
        self,
        context: LollmsContextDetails,
        constructed_context: List[str]
    ) -> List[str]:
        """ Optional context update (no-op here). """
        return constructed_context

    def _is_excluded(self, item: Path, exclude_patterns: List[str]) -> bool:
        """ Checks if an item should be excluded. """
        item_name_lower = item.name.lower()
        item_suffix_lower = item.suffix.lower()

        if item.is_dir() and item_name_lower in self.BASE_EXCLUDED_FOLDERS:
            return True
        if item.is_file() and item_suffix_lower in self.BASE_EXCLUDED_EXTENSIONS:
            return True
        for pattern in exclude_patterns:
            # Using fnmatchcase for consistent behavior across OS regarding case sensitivity
            if fnmatch.fnmatchcase(item.name, pattern):
                return True
        return False

    def _is_text_file(self, file: Path) -> bool:
        """ Determines if file extension is in the allowed text list. """
        return file.suffix.lower() in self.ALLOWED_TEXT_EXTENSIONS

    def _read_file_content(self, file: Path) -> str:
        """ Reads file content, handling errors and basic encoding. """
        try:
            if file.stat().st_size > 1 * 1024 * 1024: # 1MB limit
                 return "[File content omitted: Exceeds size limit (1MB)]"
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                self.app.info(f"File {file.name} not UTF-8, trying latin-1.")
                with open(file, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as read_err:
                self.app.warning(f"Error reading file {file.name}: {str(read_err)}")
                return f"[Error reading file: {str(read_err)}]"
            return content.strip() if content else "[Empty file]"
        except OSError as os_err:
            self.app.warning(f"OS error accessing file {file.name}: {str(os_err)}")
            return f"[Error accessing file: {str(os_err)}]"
        except Exception as e:
            self.app.error(f"Unexpected error reading file {file.name}: {str(e)}")
            return f"[Unexpected error reading file: {str(e)}]"

    def _build_tree_and_collect_files(
        self,
        folder: Path,
        exclude_patterns: List[str],
        prefix: str = ""
    ) -> Tuple[List[str], List[Path]]:
        """
        Recursively builds the Markdown tree structure string and collects
        paths of text files to include.

        Args:
            folder: The current Path object for the folder.
            exclude_patterns: List of user-defined exclusion patterns.
            prefix: The string prefix representing the tree lines.

        Returns:
            A tuple containing:
            - list[str]: Lines representing the Markdown tree structure.
            - list[Path]: Paths of text files found within this structure.
        """
        tree_lines = []
        found_files = []
        try:
            items = [
                item for item in folder.iterdir()
                if not self._is_excluded(item, exclude_patterns)
            ]
            items.sort(key=lambda x: (x.is_file(), x.name.lower()))
        except OSError as e:
            tree_lines.append(f"{prefix}[Error listing directory: {e}]")
            return tree_lines, found_files

        num_items = len(items)
        for i, item in enumerate(items):
            is_last = (i == num_items - 1)
            connector = TREE_LAST if is_last else TREE_BRANCH
            line_prefix = prefix + connector
            child_prefix = prefix + (TREE_SPACE if is_last else TREE_VLINE)

            if item.is_dir():
                tree_lines.append(f"{line_prefix}{FOLDER_ICON} {item.name}/")
                # Recursive call
                sub_tree_lines, sub_found_files = self._build_tree_and_collect_files(
                    item, exclude_patterns, child_prefix
                )
                tree_lines.extend(sub_tree_lines)
                found_files.extend(sub_found_files)
            elif item.is_file():
                # Add file entry to the tree
                tree_lines.append(f"{line_prefix}{FILE_ICON} {item.name}")
                # If it's a text file, add its path to the collection
                if self._is_text_file(item):
                    found_files.append(item) # Add the Path object

        return tree_lines, found_files

    def _generate_file_contents_markdown(
        self,
        root_folder: Path,
        file_paths: List[Path]
    ) -> List[str]:
        """
        Generates the Markdown section for displaying file contents.

        Args:
            root_folder: The starting folder path (for relative paths).
            file_paths: A list of Path objects for the files to include.

        Returns:
            A list of strings representing the Markdown content section.
        """
        content_lines = ["", "---", "", "## File Contents"] # Separator and header

        if not file_paths:
            content_lines.append("\n*No text files found or included.*")
            return content_lines

        # Sort files by path for consistent output
        file_paths.sort()

        for file_path in file_paths:
            try:
                relative_path = file_path.relative_to(root_folder)
            except ValueError:
                 # Should not happen if logic is correct, but handle defensively
                 relative_path = file_path.name
            content_lines.append(f"\n### `{relative_path}`") # Use backticks for path

            file_content = self._read_file_content(file_path)
            lang = file_path.suffix[1:].lower() if file_path.suffix else "text"
            lang = "".join(c for c in lang if c.isalnum()) or "text"

            content_lines.append(f"```{lang}")
            # Add content line by line, handling empty/error markers
            if file_content == "[Empty file]" or "[Error" in file_content or "[File content omitted" in file_content:
                 content_lines.append(file_content)
            else:
                content_lines.extend(file_content.splitlines())
            content_lines.append("```")

        return content_lines

    def execute(self, context: LollmsContextDetails, **kwargs) -> str:
        """
        Executes the function call. Generates a two-part Markdown output:
        1. Folder tree structure.
        2. Included text file contents with relative paths.
        """
        self.app.InfoMessage(f"Executing {self.function_name}...")

        folder_path_str = kwargs.get("folder_path", "")
        exclude_patterns = kwargs.get("exclude_patterns", [])

        # --- Parameter Validation ---
        if not folder_path_str:
            self.app.error("Parameter 'folder_path' is missing.")
            return "```error\nError: No folder path provided.\n```"
        if not isinstance(exclude_patterns, list):
            self.app.warning("'exclude_patterns' parameter was not a list, using defaults.")
            exclude_patterns = []
        else:
            exclude_patterns = [str(p) for p in exclude_patterns if isinstance(p, (str, Path))]

        try:
            # --- Path Resolution and Validation ---
            folder = Path(folder_path_str).resolve()
            if not folder.exists():
                self.app.error(f"Folder not found: {folder}")
                return f"```error\nError: Folder not found: {folder}\n```"
            if not folder.is_dir():
                self.app.error(f"Path is not a directory: {folder}")
                return f"```error\nError: The provided path is not a valid directory: {folder}\n```"

            # --- Generation ---
            self.app.InfoMessage(f"Generating structure for: {folder}")

            # -- Part 1: Build Tree and Collect Files --
            tree_lines, found_files = self._build_tree_and_collect_files(
                folder, exclude_patterns, prefix=""
            )

            # Prepare structure output
            structure_output_lines = [
                f"# Folder Structure: {folder.name}",
                "",
                "```text", # Use a text block for the tree for consistent rendering
                f"{FOLDER_ICON} {folder.name}/", # Root folder entry
            ]
            structure_output_lines.extend(tree_lines)
            structure_output_lines.append("```") # Close the text block

            # -- Part 2: Generate File Contents --
            content_output_lines = self._generate_file_contents_markdown(
                folder, found_files
            )

            # -- Combine Outputs --
            full_output = "\n".join(structure_output_lines) + "\n" + "\n".join(content_output_lines)

            self.app.InfoMessage(f"Folder structure and content generation complete for: {folder}")
            return full_output.strip() # Remove any trailing whitespace

        except Exception as e:
            self.app.error(f"An unexpected error occurred during folder processing: {str(e)}")
            # import traceback # Optional for detailed debugging
            # self.app.error(traceback.format_exc())
            return f"```error\nError: An unexpected error occurred: {str(e)}\n```"