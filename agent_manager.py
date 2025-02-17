#agent_manager.py
import json
import logging
import threading
from typing import Dict, List, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from roles import *

class AgentManager:
    VALID_ROLES = {
        'recherche': ("🔍 Recherches", Recherche),
        'conseil': ("💬 Conseil Personnel", Conseil),
        'organisation': ("📅 Organisation", Organisation),
        'créatif': ("🎨 Générateur d'Idées", Créatif),               
        'coach': ("🏋️ Coaching Personnel", Coach),                   
        'coachpro': ("🚀 Coaching Professionnel", CoachPro), 
        'connecteur': ("🔗 Synthèse des Idées", Connecteur)           
    }

    def __init__(self, max_workers: Optional[int] = None, model_config: Optional[dict] = None):
        self.DetecteurBesoins = DetecteurBesoins()
        self.model_config = model_config or {}
        self.agents = self._initialize_agents()
        self.max_workers = max_workers or 3
        self.executor = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._init_executor()

    def _init_executor(self):
        """Initialise ou réinitialise l'executor si nécessaire"""
        if self.executor is None or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
            self.logger.info("Initialisation pour une demande")

    def _initialize_agents(self) -> Dict[str, object]:
        agents = {}
        for role, (display_name, agent_class) in self.VALID_ROLES.items():
            if not issubclass(agent_class, BaseRole):
                raise TypeError(f"{agent_class.__name__} n'est pas un rôle valide")
            agents[role] = agent_class(**self.model_config.get(role, {}))
        return agents
    
    def detect_roles(self, input_text: str):
        """Traite la détection des besoins"""
        try:
            required_roles = self.DetecteurBesoins.detect_roles(input_text)
            self.logger.info(f"Rôles détectés : {required_roles}")
            
            return required_roles
        except Exception as e:
            self.logger.error(f"Erreur globale du traitement : {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
            
    def process_request(self, input_text: str, required_roles: List[str], on_progress: Optional[Callable] = None) -> Tuple[Dict[str, str], List[str]]:
        """Traite une requête de manière parallèle avec gestion d'erreurs améliorée"""
        if not required_roles:
            self.logger.warning("Aucun rôle détecté, utilisation du fallback")
            required_roles = ['recherche']
        try:
            results = self._execute_parallel_processing(input_text, required_roles, on_progress)
            
            if len(required_roles) > 1:
                try:
                    on_progress(f"📝 Résumé en cours...")
                except Exception as e:
                    self.logger.error(f"Erreur lors de la mise à jour de la progression : {str(e)}")
                connecteur_result = self._run_connecteur(input_text, results)
                results['connecteur'] = connecteur_result
            
            return results, required_roles
            
        except Exception as e:
            self.logger.error(f"Erreur globale du traitement : {str(e)}", exc_info=True)
            return self._create_error_response(str(e))
            
    def _run_connecteur(self, input_text: str, agent_results: Dict[str, str]) -> str:
        """Exécute le Connecteur en synthétisant les réponses des autres rôles"""
        try:
            connecteur = self.agents.get('connecteur')
            if not connecteur:
                raise ValueError("Agent Connecteur non configuré")
            
            # Préparer les réponses sous forme de liste de dictionnaires
            responses = [
                {"role": self.VALID_ROLES.get(role, (role, None))[0], "response": content}
                for role, content in agent_results.items() if role != 'connecteur'
            ]
            
            # Exécuter le Connecteur avec les réponses des autres agents
            result = connecteur.execute(input_text, responses)
            self.logger.info("Le Connecteur a terminé avec succès")
            return result

        except Exception as e:
            self.logger.error(f"Erreur de traitement Connecteur : {str(e)}", exc_info=True)
            return f"Erreur Connecteur : {str(e)}"

    def _execute_parallel_processing(self, input_text: str, roles: List[str], on_progress: Optional[Callable] = None) -> Dict[str, str]:
        futures = {}
        results = {}
        
        with self.lock:
            self._init_executor()

            try:
                # Soumission des tâches
                for role in roles:
                    if role in self.VALID_ROLES:
                        if on_progress:
                            role_name = self.VALID_ROLES[role][0]
                            on_progress(f"🚀 Démarrage {role_name}...")
                        
                        future = self.executor.submit(
                            self._run_agent_task,
                            role,
                            input_text,
                            on_progress
                        )
                        futures[future] = role
                        self.logger.debug(f"Tâche soumise pour {role}")

                # Collecte des résultats avec gestion du timeout
                try:
                    for future in as_completed(futures, timeout=200):
                        role = futures[future]
                        try:
                            result = future.result()
                            results[role] = result
                        except Exception as e:
                            results[role] = f"Erreur {role}: {str(e)}"
                            self.logger.error(f"Erreur avec {role} : {str(e)}", exc_info=True)
                
                except TimeoutError:
                    self.logger.warning("Timeout : certains agents n'ont pas terminé à temps")
                    for future in futures:
                        if not future.done():
                            role = futures[future]
                            results[role] = f"Timeout : {role} n'a pas terminé dans les 200 secondes"
                
            finally:
                # Réinitialisation sélective de l'executor
                if self.executor._work_queue.empty():  # pylint: disable=protected-access
                    self.logger.debug("Nettoyage de l'executor")
                    self.executor.shutdown(wait=False)
                    self.executor = None

        return self._format_results(results)

    def _run_agent_task(self, role: str, input_text: str, on_progress: Optional[Callable] = None) -> str:
        """Exécute une tâche avec notifications de progression"""
        self.logger.info(f"Début du traitement par {role}")
        try:
            role_name = self.VALID_ROLES[role][0]
            
            # Notifie le début du traitement
            if on_progress:
                on_progress(f"⚙️ {role_name} en cours...")
            
            agent = self.agents.get(role)
            result = agent.execute(input_text)
            
            # Notifie la réussite
            if on_progress:
                on_progress(f"✅ {role_name} terminé !")
            
            return result
        except Exception as e:
            # Notifie l'erreur
            if on_progress:
                on_progress(f"❌ Erreur {self.VALID_ROLES[role][0]} : {str(e)}")
            raise

    def _format_results(self, raw_results: Dict[str, str]) -> Dict[str, str]:
        """Formate les résultats pour l'affichage final"""
        return {
            self.VALID_ROLES.get(role, ("Autre", None))[0]: content
            for role, content in raw_results.items()
        }

    def _create_error_response(self, error_msg: str) -> Dict[str, str]:
        """Crée une réponse d'erreur standardisée"""
        return {
            "🚨 Erreur Système": (
                "Une erreur critique est survenue. "
                f"Détails techniques : {error_msg[:200]}..."
            )
        }

    def list_agents(self) -> Dict[str, str]:
        """Retourne la liste des agents disponibles avec description"""
        return {
            role: details[0] 
            for role, details in self.VALID_ROLES.items()
        }

    def shutdown(self):
        """Nettoie les ressources de manière sécurisée"""
        if self.executor and not self.executor._shutdown:
            self.logger.info("Arrêt propre de l'executor")
            self.executor.shutdown(wait=True)