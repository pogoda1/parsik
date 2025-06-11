from typing import Dict
from src.config import PROMPT_FILE, JSON_SCHEME_FILE, FEW_SHOT_FILE, SCHEME_HINTS_FILE

class PromptManager:
    def __init__(self):
        self.prompt = self._load_file(PROMPT_FILE)
        self.json_scheme = self._load_file(JSON_SCHEME_FILE)
        # Remove few_shot examples and scheme_hints to reduce token count
        self.few_shot = self._load_file(FEW_SHOT_FILE)
        self.scheme_hints = self._load_file(SCHEME_HINTS_FILE)

    @staticmethod
    def _load_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replaces variables in text with actual data"""
        for var_name, var_value in variables.items():
            text = text.replace(f"{{{{ {var_name} }}}}", str(var_value))
        return text

    def prepare_prompt(self, message: str) -> str:
        """Prepares the full prompt with all variables"""
        variables = {
            "json_schema": self.json_scheme,
            "schema_hints": self.scheme_hints,
            "few_shot_examples": self.few_shot,
            "message": message
        }
        return self.replace_variables(self.prompt, variables) 