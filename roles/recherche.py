from .base_role import BaseRole

class Recherche(BaseRole):
    def __init__(self, model_name='deepseek-ai/DeepSeek-R1'):
        """
        Classe spécialisée pour la recherche d'informations synthétiques.
        """
        super().__init__(model_name=model_name, mode="external")

    def execute(self, prompt: str) -> str:
        """Effectue une recherche ciblée et synthétique avec une structure claire."""
        full_prompt = (
            "Vous êtes un assistant de recherche expert. "
            "Fournissez une réponse structurée en 5 parties concises :\n\n"
            "**1. Objectif** : Reformulation claire de la demande\n"
            "**2. Sources fiables** : 3-5 sources web crédibles\n"
            "**3. Faits clés** : Chiffres, statistiques et données vérifiables\n"
            "**4. Analyse synthèse** : Principaux enseignements en 3 points\n"
            "**5. Pistes d'action** : Recommandations pratiques\n\n"
            "Gardez chaque partie en 2-3 phrases maximum. "
            "Priorisez les données récentes (derniers 2 ans). "
            "Évitez le jargon trop technique.\n\n"
            f"**Demande** : {prompt}"
        )
        
        return self.generate_response(full_prompt)
