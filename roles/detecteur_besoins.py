from .base_role import BaseRole
from pathlib import Path
from typing import List
import json
import logging
import re

class DetecteurBesoins(BaseRole):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        #self.logger.setLevel(logging.DEBUG)
        self.roles_file = Path(__file__).parent / "roles.json"  

    def detect_roles(self, text: str) -> List[str]:
        """Détection des rôles avec gestion d'erreur améliorée"""
        try:
            # Chargement des rôles
            with open(self.roles_file, "r", encoding="utf-8") as f:
                roles = json.load(f)
            
            # Construction dynamique du prompt
            detection_sections = [
                role["detection"] 
                for role in roles 
                if "detection" in role and role["detection"].strip()
            ]
            
            self.logger.debug(f"Nombre de sections de détection trouvées : {len(detection_sections)}")
            if not detection_sections:
                self.logger.error("Aucune section de détection trouvée dans roles.json !")
            
            prompt = (
                "Analyse cette demande utilisateur pour identifier le type de support requis selon ces critères :\n\n"
                f"{'\n\n'.join(detection_sections)}\n\n"
                f'Texte à analyser : "{text}"\n\n'
                "Réponds UNIQUEMENT en JSON valide avec une clé 'roles' contenant la liste des services pertinents par ordre de priorité.\n"
                'Exemple de réponse valide : {"roles": ["organisation", "coach"]}'
            )

            response = self.generate_response(prompt, temp=0.2, mode='local')
            return self._parse_response(response)
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Erreur de configuration : {str(e)}")
            return self._fallback_detection(text)
        except Exception as e:
            self.logger.error(f"Erreur inattendue : {str(e)}", exc_info=True)
            return []

    def _parse_response(self, response: str) -> List[str]:
        """Parse la réponse du modèle avec validation renforcée"""
        try:
            clean_res = self._clean_response(response)
            json_str = self._extract_json(clean_res)
            self.logger.debug(f"JSON extrait: {json_str}")  
            
            data = json.loads(json_str)
            
            valid_roles = self._get_valid_roles()
            detected_roles = [
                self._normalize_role(role) 
                for role in data.get('roles', [])
                if self._normalize_role(role) in valid_roles
            ]
            
            self.logger.debug(f"Rôles détectés après validation: {detected_roles}")
            return list(dict.fromkeys(detected_roles))[:6]

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Échec du parsing JSON: {str(e)}")
            return self._fallback_detection(clean_res)
            
    def _get_valid_roles(self) -> set:
        """Récupère dynamiquement les noms de rôles valides"""
        with open(self.roles_file, "r", encoding="utf-8") as f:
            roles = json.load(f)
        return {role["name"].strip().lower() for role in roles}

    @staticmethod
    def _normalize_role(role_name: str) -> str:
        """Normalise le nom du rôle"""
        return role_name.strip().lower().rstrip('s')

    def _clean_response(self, text: str) -> str:
        """Nettoie la réponse du modèle"""
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return text.lower().strip()

    def _extract_json(self, text: str) -> str:
        """Extrait le JSON de la réponse avec une regex compatible Python."""
        # D'abord essayer de trouver un bloc JSON formel
        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        # Sinon chercher le JSON le plus profond dans le texte
        deepest_json = None
        for match in re.finditer(r'{([^{}]*|(?R))*}', text, re.DOTALL):
            current = match.group(0)
            try:
                json.loads(current)  # Validation syntaxique
                if not deepest_json or len(current) > len(deepest_json):
                    deepest_json = current
            except:
                continue

        return deepest_json or text.strip()

    def _fallback_detection(self, text: str) -> List[str]:
        """Détection de secours basée sur des mots-clés pondérés."""
        # Mapping des rôles avec leurs mots-clés et poids associés
        keyword_mapping = {
            'recherche': {
                'keywords': ['information', 'données', 'étude', 'recherche', 'statistiques', 'faits'],
                'weight': 1.0
            },
            'conseil': {
                'keywords': ['stress', 'moral', 'émotion', 'confiance', 'solitude', 'soutien', 'relation'],
                'weight': 1.2  # Poids plus élevé pour les termes émotionnels
            },
            'organisation': {
                'keywords': ['plan', 'organisation', 'temps', 'projet', 'logistique', 'routine'],
                'weight': 1.0
            },
            'créatif': {
                'keywords': ['idée', 'créatif', 'innovation', 'inspiration', 'concept', 'brainstorming'],
                'weight': 1.0
            },
            'coach': {
                'keywords': ['productivité', 'efficacité', 'procrastination', 'motivation', 'discipline'],
                'weight': 1.0
            },
            'coachpro': {
                'keywords': ['carrière', 'leadership', 'professionnel', 'compétences', 'performance'],
                'weight': 1.0
            }
        }

        # Calcul des scores pour chaque rôle
        scores = {role: 0 for role in keyword_mapping}
        text_lower = text.lower()

        for role, data in keyword_mapping.items():
            for keyword in data['keywords']:
                if keyword in text_lower:
                    scores[role] += data['weight']

        # Filtrage des rôles avec un score > 0
        detected_roles = [role for role, score in scores.items() if score > 0]

        # Tri par score décroissant
        detected_roles.sort(key=lambda x: scores[x], reverse=True)

        # Retourne les 3 rôles les plus pertinents (ou un fallback par défaut)
        return detected_roles[:3] or ['conseil']