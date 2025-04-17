import os
import datetime

def ensure_dir(directory):
    """S'assure qu'un répertoire existe, le crée si nécessaire"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_current_date():
    """Retourne la date courante au format YYYY-MM-DD"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def get_current_datetime():
    """Retourne la date et l'heure courantes au format YYYY-MM-DD HH:MM:SS"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_date(date_str):
    """Formate une date au format YYYY-MM-DD en format lisible (DD/MM/YYYY)"""
    if not date_str:
        return ""
    
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def validate_email(email):
    """Vérifie si une adresse email est valide"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_price(price):
    """Formate un prix avec 2 décimales et le symbole €"""
    return f"{price:.2f} €"

def get_color_hex(color_name):
    """Retourne le code hexadécimal d'une couleur à partir de son nom"""
    color_map = {
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
    
    return color_map.get(color_name, "#CCCCCC")  # Gris par défaut