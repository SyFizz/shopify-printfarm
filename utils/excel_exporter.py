import pandas as pd
import os
from datetime import datetime
from config import DEFAULT_EXPORT_DIR
from utils.helpers import ensure_dir

def export_orders_to_excel(orders, filename=None):
    """
    Exporte la liste des commandes vers un fichier Excel
    """
    # S'assurer que le répertoire d'export existe
    ensure_dir(DEFAULT_EXPORT_DIR)
    
    # Générer un nom de fichier par défaut si non spécifié
    if not filename:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Commandes_Plasmik3D_{date_str}.xlsx"
    
    file_path = os.path.join(DEFAULT_EXPORT_DIR, filename)
    
    # Préparer les données pour le format Excel
    data = []
    
    for order in orders:
        # Créer une ligne pour chaque produit dans la commande
        for item in order.items:
            data.append({
                'ID Commande': order.id,
                'Date': order.date,
                'Client': order.client,
                'Email': order.email,
                'Produit': item['product'],
                'Couleur': item['color'],
                'Quantité': item['quantity'],
                'Statut Produit': item['status'],
                'Statut Commande': order.status,
                'Priorité': order.priority,
                'Notes': order.notes
            })
    
    # Convertir en DataFrame pandas
    df = pd.DataFrame(data)
    
    # Exporter vers Excel
    df.to_excel(file_path, index=False)
    
    return file_path

def export_print_plan_to_excel(print_plan, filename=None):
    """
    Exporte le plan d'impression vers un fichier Excel
    """
    # S'assurer que le répertoire d'export existe
    ensure_dir(DEFAULT_EXPORT_DIR)
    
    # Générer un nom de fichier par défaut si non spécifié
    if not filename:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Plan_Impression_Plasmik3D_{date_str}.xlsx"
    
    file_path = os.path.join(DEFAULT_EXPORT_DIR, filename)
    
    # Préparer les données pour le format Excel
    data = []
    
    for color, products in print_plan.items():
        for product_info in products:
            data.append({
                'Couleur': color,
                'Produit': product_info['product'],
                'Quantité': product_info['quantity'],
                'Commandes': ', '.join(product_info['order_ids']),
                'Priorité': product_info['priority']
            })
    
    # Convertir en DataFrame pandas
    df = pd.DataFrame(data)
    
    # Exporter vers Excel
    df.to_excel(file_path, index=False)
    
    return file_path

def export_inventory_to_excel(inventory, filename=None):
    """
    Exporte l'inventaire vers un fichier Excel
    """
    # S'assurer que le répertoire d'export existe
    ensure_dir(DEFAULT_EXPORT_DIR)
    
    # Générer un nom de fichier par défaut si non spécifié
    if not filename:
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Inventaire_Plasmik3D_{date_str}.xlsx"
    
    file_path = os.path.join(DEFAULT_EXPORT_DIR, filename)
    
    # Convertir en DataFrame pandas
    df = pd.DataFrame(inventory)
    
    # Exporter vers Excel
    df.to_excel(file_path, index=False)
    
    return file_path