from .base_role import BaseRole
from .detecteur_besoins import DetecteurBesoins
from .connecteur import Connecteur
from .recherche import Recherche
from .role_class import create_role_class

import json
import os

# Chargement des rôles dynamiques depuis roles.json
dynamic_roles = {}
ROLES_JSON_PATH = os.path.join(os.path.dirname(__file__), 'roles.json')

if os.path.exists(ROLES_JSON_PATH):
    with open(ROLES_JSON_PATH, "r", encoding="utf-8") as file:
        roles_data = json.load(file)
    for role_data in roles_data:
        role_name = role_data["name"]
        dynamic_roles[role_name] = create_role_class(role_data)

# Export des rôles statiques + dynamiques
__all__ = [
    'BaseRole',
    'DetecteurBesoins',
    'Connecteur',
    'Recherche'
] + list(dynamic_roles.keys())

# Injecter les rôles dynamiques dans le namespace global
globals().update(dynamic_roles)
