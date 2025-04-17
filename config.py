"""Configuration globale de l'application Plasmik3D"""

import os

# Informations sur l'application
APP_NAME = "Plasmik3D"
APP_VERSION = "0.1.0"
COMPANY_NAME = "Plasmik3D"

# Chemins des fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
DATABASE_PATH = os.path.join(BASE_DIR, "data.db")
DEFAULT_EXPORT_DIR = os.path.expanduser("~/Documents/Plasmik3D")

# S'assurer que les répertoires existent
os.makedirs(RESOURCES_DIR, exist_ok=True)
os.makedirs(os.path.join(RESOURCES_DIR, "icons"), exist_ok=True)
os.makedirs(os.path.join(RESOURCES_DIR, "styles"), exist_ok=True)
os.makedirs(os.path.join(RESOURCES_DIR, "sample_data"), exist_ok=True)
os.makedirs(DEFAULT_EXPORT_DIR, exist_ok=True)

# Couleurs disponibles
COLORS = [
    "Rouge", "Bleu", "Vert", "Jaune", "Orange", "Violet", 
    "Noir", "Blanc", "Gris", "Rose", "Marron", "Cyan", 
    "Sky Blue", "Sakura Pink", "Lavande",
    "Satin couleur Or", "Satin couleur Or/Noir", "Satin couleurs Noir/Violet",
    "Aléatoire"
]

# Produits disponibles
PRODUCTS = [
    "SpinRing", "Triggo", "StarNest", "OctoTwist", 
    "Infinity Cube", "FlexiRex", "GyroToy", "ClickyPaw",
    "CableCatch", "SkullyClick"
]

# Statuts des commandes
ORDER_STATUSES = ["En attente", "En cours", "Prêt", "Expédié", "Annulé"]

# Statuts des produits
ITEM_STATUSES = ["À imprimer", "En impression", "Imprimé"]

# Priorités
PRIORITIES = ["Haute", "Moyenne", "Basse"]

# Paramètres de l'interface utilisateur
UI_SETTINGS = {
    "refresh_interval": 5 * 60,  # Intervalle de rafraîchissement en secondes
    "theme": "light",            # Thème (light ou dark)
    "font_size": 10,             # Taille de police par défaut
    "date_format": "%d/%m/%Y",   # Format de date
    "time_format": "%H:%M:%S"    # Format d'heure
}

# Correspondance entre les noms de couleurs et les codes HEX pour l'interface
COLOR_HEX_MAP = {
    "Rouge": "#FF0000",
    "Bleu": "#0000FF",
    "Vert": "#00FF00",
    "Jaune": "#FFFF00",
    "Orange": "#FFA500",
    "Violet": "#800080",
    "Noir": "#000000",
    "Blanc": "#FFFFFF",
    "Gris": "#808080",
    "Rose": "#FFC0CB",
    "Marron": "#A52A2A",
    "Cyan": "#00FFFF",
    "Sky Blue": "#87CEEB",
    "Sakura Pink": "#FFB7C5",
    "Lavande": "#E6E6FA",
    "Satin couleur Or": "#D4AF37",
    "Satin couleur Or/Noir": "#8B7D37",
    "Satin couleurs Noir/Violet": "#4B0082",
    "Aléatoire": "#CCCCCC"
}

# Couleurs de l'interface utilisateur
UI_COLORS = {
    "primary": "#366092",      # Couleur principale
    "secondary": "#4F81BD",    # Couleur secondaire
    "success": "#4CAF50",      # Succès
    "warning": "#FFC107",      # Avertissement
    "danger": "#F44336",       # Danger
    "info": "#2196F3",         # Information
    "background": "#FFFFFF",   # Arrière-plan
    "text": "#333333",         # Texte
    "border": "#DDDDDD"        # Bordures
}