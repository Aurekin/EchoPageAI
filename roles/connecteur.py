from .base_role import BaseRole
import re

class Connecteur(BaseRole):
    def __init__(self, model_name='deepseek-r1:14b', mode='external'):
        """
        Initialise un Connecteur qui peut fonctionner en mode local ou externe.
        """
        super().__init__(model_name, mode)
    
    def execute(self, prompt: str, responses: list) -> str:
        """Relie et synthétise les idées des différents rôles pour créer une vision cohérente."""
        if self.mode == 'local':
            # Résumer chaque réponse individuellement
            partial_summaries = []
            for resp in responses:
                individual_prompt = self.build_individual_prompt(prompt, resp)
                
                partial_summary = self.generate_response(individual_prompt, temp=1.2)
                partial_summary = self.clean_think_tags(partial_summary)
                
                partial_summaries.append(f"Résumé du rôle {resp['role']} : {partial_summary}")
        
            # Résumer l'ensemble des mini-résumés
            final_prompt = self.build_final_prompt(prompt, partial_summaries)
            self.save_summary_to_file("\n\n".join(partial_summaries))
            return self.generate_response(final_prompt, temp=1.2)
        
        else:
            # Mode externe : tout en une seule fois
            formatted_responses = "\n".join(
                [f"Réponse de l'aidant {resp['role']}: {resp['response']}" for resp in responses]
            )
            full_prompt = self.build_final_prompt(prompt, [formatted_responses])
            return self.generate_response(full_prompt, temp=1.1)
            
    def clean_think_tags(self, text: str) -> str:
        """Supprime les balises <think> et leur contenu du texte."""
        return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            
    def save_summary_to_file(self, summary: str, filename: str = "resumesConnecteur.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(summary)
        
    def build_individual_prompt(self, prompt: str, response: dict) -> str:
        """Construit un prompt pour résumer une réponse individuelle."""
        return f"""Tu es une experte en synthèse de texte. 
            Ton rôle est de résumer la réponse d'une personne aidant pour la problématique d'une autre.

            Voici la demande initiale : "{prompt}"

            Réponse de l'aidant {response['role']} :
            {response['response']}

            Ta mission est d'identifier les points clés et résumer en quelques phrases l'essence de cette réponse.
            """

    def build_final_prompt(self, prompt: str, summaries: list) -> str:
        """Construit un prompt pour synthétiser les résumés partiels."""
        combined_summaries = "\n".join(summaries)
        return f"""Tu es le Connecteur, un expert en analyse et en intégration d'idées. 
            Ton rôle est de faire le lien entre des perspectives variées pour en extraire l'essentiel et résumer les aides venant de différents rôles.

            Voici la demande initiale : "{prompt}"

            Résumés des aidants:
            {combined_summaries}

            Ta mission :
            1. Identifier les idées clés et les points communs entre les différents résumés.
            2. Mettre en lumière les complémentarités et la richesse des approches proposées.
            3. Créer un résumé final cohérent et fluide qui garde l'esprit des réponses originales.
            Tes réponses sont naturelles évitant un effet de listing.
            """
     