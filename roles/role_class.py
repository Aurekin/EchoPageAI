import json
from .base_role import BaseRole

def create_role_class(role_data):
    class_name = role_data["name"]
    prompt_template = role_data["prompt"]
    temperature = role_data.get("temperature", 1.0)
    model_name = role_data.get("model", "deepseek-r1:14b")
    mode = role_data.get("mode", "local")
    
    # Classe dynamique avec des paramètres personnalisés
    class DynamicRole(BaseRole):
        def __init__(self):
            super().__init__(model_name=model_name, mode=mode)
        
        def execute(self, user_input: str) -> str:
            full_prompt = prompt_template.replace("{input}", user_input)
            return self.generate_response(full_prompt, temp=temperature)
    
    DynamicRole.__name__ = class_name 
    return DynamicRole