#main.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import sys
import subprocess
import time
import psutil
import requests
from agent_manager import AgentManager
import threading
from typing import Dict
import logging
import queue
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuration globale du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Écrit dans un fichier
        logging.StreamHandler()          # Affiche dans la console
    ]
)

class AIAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Assistance")
        self.root.geometry("1000x500")
        self.agent_manager = AgentManager()
        self.output_dir = os.path.expanduser("~/Assistant_Outputs")
        
        self.setup_ui()
        self.setup_styles()
        self.create_output_dir()
        self.loading = False
        self.check_and_start_ollama()
        self.setup_status()

    def setup_status(self):
        """Configure la barre de statut initiale"""
        self._update_status("Prêt - Entrez votre demande ci-dessus")

    def _update_status(self, message: str):
        """Met à jour la barre de statut de manière thread-safe"""
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()
        
    def check_and_start_ollama(self):
        """Vérifie si Ollama est en cours d'exécution et le démarre si nécessaire"""
        if not self.is_ollama_running():
            self.status_bar['text'] = "Démarrage d'Ollama..."
            self.root.update()
            
            try:
                # Démarrer Ollama en mode serveur
                ollama_path = "ollama"  # Adapter si nécessaire
                subprocess.Popen([ollama_path, "serve"],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)

                # Vérifier que le serveur répond bien
                if self.wait_for_ollama():
                    self.status_bar['text'] = "Ollama prêt !"
                else:
                    raise Exception("Le serveur Ollama ne répond pas après démarrage.")

            except Exception as e:
                messagebox.showerror(
                    "Erreur Ollama", 
                    f"Impossible de démarrer Ollama : {str(e)}\n"
                    "Veuillez vous assurer qu'il est installé et accessible."
                )
                self.root.destroy()
        else:
            self.status_bar['text'] = "Prêt !"

    def is_ollama_running(self):
        """Vérifie si le processus Ollama est en cours d'exécution"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                return True
        return False

    def wait_for_ollama(self, timeout=10):
        """Attente active jusqu'à ce qu'Ollama réponde sur le port 11434"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    return True
            except requests.ConnectionError:
                time.sleep(1)  # Attendre avant de réessayer
        return False
        
    def check_ollama_connection(self):
        """Vérifie la connexion et la disponibilité des modèles"""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                return False
            
            # Vérifier la présence d'au moins un modèle
            models = response.json().get('models', [])
            if not models:
                messagebox.showwarning(
                    "Aucun modèle installé",
                    "Veuillez installer au moins un modèle Ollama (ex: llama2)."
                )
                return False
            
            return True
        except requests.ConnectionError:
            return False

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configuration des styles modernes
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('Header.TLabel', 
                           font=('Segoe UI', 14, 'bold'), 
                           foreground='#2c3e50',
                           background='#f0f0f0')
        
        self.style.map('Accent.TButton',
                     foreground=[('active', '#ffffff'), ('!active', '#ffffff')],
                     background=[('active', '#3498db'), ('!active', '#2980b9')])

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=(20, 15))
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(header_frame, 
                text="Assistant Personnel", 
                style='Header.TLabel').pack(side=tk.LEFT)

        # Zone de saisie
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame,
            wrap=tk.WORD,
            font=('Segoe UI', 12),
            padx=10,
            pady=10,
            height=6,
            bg='white',
            fg='#2c3e50'
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # Contrôles
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=20)
        
        self.execute_btn = ttk.Button(
            control_frame,
            text="Analyser la Demande",
            command=self.execute_request,
            style='Accent.TButton',
            width=20
        )
        self.execute_btn.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            control_frame,
            text="Ouvrir le Dossier",
            command=self.open_output_dir,
            width=15
        ).pack(side=tk.RIGHT, padx=10)

        # Barre de statut
        self.status_bar = ttk.Label(
            main_frame,
            text="Prêt • Dossier de sortie : " + self.output_dir,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(8, 0),
            font=('Segoe UI', 10)
        )
        self.status_bar.pack(fill=tk.X, pady=(10,0), ipady=5)

    def create_output_dir(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de créer le dossier de sortie : {str(e)}")

    def open_output_dir(self):
        try:
            os.startfile(self.output_dir)
        except:
            messagebox.showerror("Erreur", "Dossier introuvable !")

    def execute_request(self):
        if self.loading:
            return
        
        if not self.check_ollama_connection():
            messagebox.showerror("Erreur", "Ollama n'est pas disponible. Veuillez démarrer le service.")
            return

        prompt = self.input_text.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("Requête vide", "Veuillez décrire vos besoins dans la zone de texte.")
            return
            
        self.toggle_loading(True)
        
        def processing_task():
            try:
                # Version thread-safe de update_status
                def update_status(message: str):
                    def _safe_update():
                        try:
                            self._update_status(message)
                            self.root.update_idletasks()
                        except Exception as e:
                            logging.error(f"Erreur d'affichage : {str(e)}")
                    
                    self.root.after(0, _safe_update)

                # Étape 1 : Détection des rôles
                update_status("🔍 Analyse de la demande...")
                required_roles = self.agent_manager.detect_roles(prompt)
                
                # Affichage des rôles détectés
                if required_roles:
                    roles_str = ", ".join([self.agent_manager.VALID_ROLES.get(role, ("Inconnu",))[0] for role in required_roles])
                    update_status(f"⚙️ {len(required_roles)} besoins détectés, utilisation de: {roles_str}")
                else:
                    update_status("⚠️ Aucun rôle détecté, utilisation du mode par défaut")
                
                time.sleep(0.5)  # Pause courte pour le feedback visuel
                
                # Étape 2 : Traitement avec suivi temps réel
                results = {}
                try:
                    results, _ = self.agent_manager.process_request(
                        prompt,
                        required_roles,
                        on_progress=update_status  
                    )
                except Exception as e:
                    raise e
                
                # Étape 3 : Synthèse finale
                update_status("🧠 Intégration des résultats...")
                filename = self.save_to_html(prompt, results)
                
                self.root.after(0, lambda: self.show_success_message(filename))
                
            except Exception as e:
                error_msg = f"Erreur : {str(e)}"
                self.root.after(0, lambda: self._update_status("❌ " + error_msg))
                self.root.after(0, lambda: messagebox.showerror("Erreur", error_msg))
                
            finally:
                self.root.after(100, lambda: self.toggle_loading(False))
        
        threading.Thread(target=processing_task, daemon=True).start()

    def save_to_html(self, prompt: str, responses: Dict[str, str]) -> str:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output_dir, f"{timestamp}.html")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{timestamp}</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', sans-serif; 
                    line-height: 1.6;
                    margin: 20px;
                    background-color: #f5f6fa;
                }}
                .header {{ 
                    color: #2c3e50; 
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .prompt {{ 
                    background: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin: 15px 0;
                }}
                .response {{
                    white-space: pre-wrap;
                    margin-top: 20px;
                    background: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                think {{
                    display: inline-block;
                    background-color: #ffeaa7;
                    color: #2d3436;
                    padding: 8px 15px;
                    border-radius: 6px;
                    font-style: italic;
                    border: 1px dashed #fdcb6e;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    overflow: hidden;
                    max-height: 500px;
                    position: relative;
                    vertical-align: top;
                    margin: 3px 0;
                    line-height: 1.4;
                }}
                think.hidden {{
                    max-height: 28px;
                    background-color: #dfe6e9;
                    border: 1px solid #b2bec3;
                    border-left: 4px solid #ffeaa7;
                    padding: 3px 12px 3px 30px;
                    color: transparent;
                }}
                think.hidden::before {{
                    content: "▶";
                    position: absolute;
                    left: 12px;
                    top: 50%;
                    transform: translateY(-50%);
                    color: #636e72;
                    font-size: 14px;
                    transition: transform 0.2s;
                }}
                think:hover {{
                    filter: brightness(0.98);
                    transform: translateY(-1px);
                }}
                .timestamp {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
                h2 {{
                    color: #3498db;
                    margin-top: 25px;
                }}
                .response-section {{
                    margin: 20px 0;
                    padding: 15px;
                    background: #ffffff;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                }}
                h3 {{
                    color: #3498db;
                    margin-top: 0;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 8px;
                }}
                
                .response-content {{
                    padding: 15px;
                    line-height: 1.7;
                    color: #2c3e50;
                    background: #f9f9f9;
                    border-left: 4px solid #3498db;
                    margin: 10px 0;
                }}
                .response-content pre {{
                    background: #2c3e50;
                    color: #f9f9f9;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                .response-content code {{
                    font-family: 'Courier New', Courier, monospace;
                    background: #2c3e50;
                    color: #f9f9f9;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                .response-content blockquote {{
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                    color: #7f8c8d;
                    font-style: italic;
                    margin: 10px 0;
                }}
                .response-content ul, .response-content ol {{
                    padding-left: 20px;
                    margin: 10px 0;
                }}
                .response-content li {{
                    margin-bottom: 5px;
                }}
                .response-content a {{
                    color: #3498db;
                    text-decoration: none;
                }}
                .response-content a:hover {{
                    text-decoration: underline;
                }}
                /* Transition pour les interactions */
                .response-content, .response-section, .prompt {{
                    transition: all 0.3s ease;
                }}
                .response-section:hover, .prompt:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
            </style>
            <script>
                function toggleThink(event) {{
                    const thinkElement = event.currentTarget;
                    thinkElement.classList.toggle('hidden');
                    
                    // Rotate arrow
                    const arrow = window.getComputedStyle(thinkElement, '::before').getPropertyValue('content');
                    if(thinkElement.classList.contains('hidden')) {{
                        thinkElement.style.setProperty('--arrow-rotation', '0deg');
                    }} else {{
                        thinkElement.style.setProperty('--arrow-rotation', '90deg');
                    }}
                }}

                document.addEventListener('DOMContentLoaded', function() {{
                    document.querySelectorAll('think').forEach(element => {{
                        element.addEventListener('click', toggleThink);
                        // Initialize rotation property
                        element.style.setProperty('--arrow-rotation', '90deg');
                    }});
                }});
            </script>
        </head>
        <body>
            <div class="container">
                <h1 class="header">Résultats:</h1>
                <p class="timestamp">{time.strftime("%d/%m/%Y %H:%M:%S")}</p>

                <h2>Demande initiale :</h2>
                <div class="prompt">{prompt}</div>

                <h2>Réponse générée :</h2>
            """
        
        for role, content in responses.items():
            formatted_content = content
            
            # Lignes de séparation : --- → <hr>
            formatted_content = re.sub(r'^---+(\s*)$', r'<hr>\1', formatted_content, flags=re.MULTILINE)

            # Titres : ### Titre
            formatted_content = re.sub(r'^(#{3})\s*(.*)$', r'<h3>\2</h3>', formatted_content, flags=re.MULTILINE)

            # Gras : **texte**
            formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_content)

            # Italique : *texte*
            formatted_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted_content)

            # Code inline : `texte`
            formatted_content = re.sub(r'`(.*?)`', r'<code>\1</code>', formatted_content)

            # Listes à puces : - texte (à traiter AVANT les sauts de ligne)
            def list_replacer(match):
                items = match.group(0).strip().split("\n")
                items = [f"<li>{item[2:]}</li>" for item in items]
                return f"<ul>{''.join(items)}</ul>"

            formatted_content = re.sub(r'(?:^-\s.*\n?)+', list_replacer, formatted_content, flags=re.MULTILINE)

            # Gestion des sauts de ligne hors des balises HTML block-level
            formatted_content = re.sub(
                r'(</(?:li|h[1-6]|p|blockquote)>)?\n(?!<)',
                lambda m: (m.group(1) + "\n") if m.group(1) is not None else '<br>',
                formatted_content
            )

            # Envelopper le tout dans une section
            html_content += f"""
                <div class="response-section">
                    <h3>{role}</h3>
                    <div class="response-content">
                        {formatted_content}
                    </div>
                </div>
            """

        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename

    def _update_status(self, message: str):
        """Met à jour la barre de statut de manière thread-safe"""
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()

    def show_success_message(self, filename: str):
        """Affiche un message de succès avec options supplémentaires"""
        self._update_status(f"✅ Rapport généré : {os.path.basename(filename)}")
        
        # Ajouter un bouton "Ouvrir"
        open_btn = ttk.Button(
            self.status_bar,
            text="📂 Ouvrir",
            command=lambda: os.startfile(filename)
        )
        open_btn.pack(side=tk.RIGHT, padx=5)
        
        # Réinitialiser après 5 secondes
        self.root.after(5000, lambda: self._reset_status(open_btn))

    def _reset_status(self, button: ttk.Button):
        """Réinitialise la barre de statut"""
        button.destroy()  # Supprime le bouton
        self._update_status("Prêt • Entrez une nouvelle demande")

    def toggle_loading(self, state: bool):
        """Active/désactive l'état de chargement"""
        self.loading = state
        self.execute_btn['state'] = 'disabled' if state else 'normal'

if __name__ == "__main__":
    root = tk.Tk()
    app = AIAssistantApp(root)
    root.mainloop()