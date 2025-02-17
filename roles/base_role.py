# base_role.py
from ollama import Client
import requests
import together 
from together import Together
from dotenv import load_dotenv
import os

load_dotenv()

class BaseRole:
    def __init__(self, model_name='deepseek-r1:14b', mode='local'):
        """
        Classe de base pour tous les rôles.
        
        :param model_name: Nom du modèle à utiliser.
        :param mode: 'local' pour Ollama, 'external' pour une API externe.
        """
        self.model = model_name
        self.ext_model = 'deepseek-ai/DeepSeek-R1'
        self.mode = mode
        self.api_key = os.getenv("TOGETHER_API_KEY")
        
        if self.mode == 'local':
            self.client = Client(host='http://localhost:11434')
        elif self.mode == 'external':
            if not self.api_key:
                raise ValueError("Une clé API est nécessaire pour le mode externe (.env).")
            
    def generate_response(self, prompt: str, temp: float = 1.0, mode: str = None) -> str:
        mode = mode or self.mode

        if mode == 'local':
            return self._generate_local(prompt, temp)
        elif mode == 'external':
            return self._generate_external(prompt, temp)
        else:
            return "Mode non reconnu. Utilisez 'local' ou 'external'."
    
    def _generate_local(self, prompt: str, temp: float) -> str:
        """Génération via Ollama en local"""
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={'temperature': temp}
            )
            return response['response']
        except Exception as e:
            return f"Erreur lors de la génération locale : {str(e)}"

    def _generate_external(self, prompt: str, temp: float) -> str:
        """Génération via l'API Together"""
        try:
            client = Together(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.ext_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=2600
            )
            return response.choices[0].message.content
        except together.error.AuthenticationError:
            return "Erreur d'authentification : vérifiez votre clé API"
        except together.error.RateLimitError:
            return "Limite de requêtes dépassée"
        except Exception as e:
            return f"Erreur inattendue : {str(e)}"
            