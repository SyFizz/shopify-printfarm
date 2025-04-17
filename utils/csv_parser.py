import pandas as pd
import re
import os
from PyQt5.QtCore import QObject, pyqtSignal
from models.order import Order

class CSVParserSignals(QObject):
    """Signaux pour le processus d'analyse CSV"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)

class ShopifyCSVParser:
    """Classe pour analyser les fichiers CSV exportés de Shopify"""
    
    def __init__(self):
        self.signals = CSVParserSignals()
    
    def parse_file(self, file_path):
        """
        Parse un fichier CSV exporté de Shopify et retourne une liste de commandes
        """
        if not os.path.exists(file_path):
            self.signals.status.emit(f"Erreur: Le fichier {file_path} n'existe pas")
            return []
        
        self.signals.status.emit("Lecture du fichier CSV...")
        self.signals.progress.emit(10)
        
        # Lire le fichier CSV
        try:
            df = pd.read_csv(file_path)
            self.signals.status.emit(f"Fichier CSV chargé avec succès: {len(df)} lignes")
        except Exception as e:
            self.signals.status.emit(f"Erreur lors de la lecture du fichier CSV: {str(e)}")
            return []
        
        self.signals.progress.emit(30)
        
        # Vérifier les colonnes nécessaires
        required_columns = ['Name', 'Email', 'Created at', 'Lineitem quantity', 'Lineitem name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.signals.status.emit(f"Colonnes manquantes dans le CSV: {', '.join(missing_columns)}")
            return []
        
        self.signals.status.emit("Vérification des colonnes réussie")
        self.signals.progress.emit(40)
        
        # Grouper par commande (Name/ID)
        orders = {}
        total_rows = len(df)
        
        self.signals.status.emit("Traitement des commandes...")
        
        for idx, row in df.iterrows():
            # Mettre à jour la progression
            if idx % 10 == 0:  # Mettre à jour tous les 10 lignes
                progress = 40 + int((idx / total_rows) * 50)  # De 40% à 90%
                self.signals.progress.emit(progress)
            
            order_id = str(row['Name'])
            
            # Ignorer les lignes sans nom de produit
            if pd.isna(row['Lineitem name']):
                continue
            
            if order_id not in orders:
                # Formater la date (juste la partie date, pas l'heure)
                date_commande = row['Created at'].split(' ')[0] if pd.notna(row['Created at']) else ""
                
                # Extraire le statut de la commande
                status = row.get('Fulfillment Status', 'unfulfilled')
                if pd.isna(status):
                    status = 'unfulfilled'
                
                # Convertir le statut Shopify en statut application
                order_status = "Prêt" if status == 'fulfilled' else "En attente"
                
                # Créer une nouvelle commande
                orders[order_id] = Order(
                    order_id=order_id,
                    date=date_commande,
                    client=row.get('Billing Name', order_id) if pd.notna(row.get('Billing Name', '')) else order_id,
                    email=row['Email'] if pd.notna(row['Email']) else "",
                    status=order_status,
                    priority="Moyenne",
                    notes=row.get('Notes', '') if pd.notna(row.get('Notes', '')) else ""
                )
            
            # Extraire les informations du produit
            lineitem_name = row['Lineitem name']
            lineitem_quantity = int(row['Lineitem quantity']) if pd.notna(row['Lineitem quantity']) else 1
            
            # Extraire le produit et la couleur
            product_info = self.extract_product_color_quantity(lineitem_name, lineitem_quantity)
            
            # Ajouter le produit à la commande
            orders[order_id].add_item(
                product=product_info['product'],
                color=product_info['color'],
                quantity=product_info['quantity'],
                status="Imprimé" if orders[order_id].status == "Prêt" else "À imprimer"
            )
        
        self.signals.status.emit(f"Traitement terminé: {len(orders)} commandes extraites")
        self.signals.progress.emit(90)
        
        return list(orders.values())
    
    def extract_product_color_quantity(self, lineitem_name, default_quantity=1):
        """
        Extrait le produit, la couleur et la quantité à partir du nom de l'article
        Format attendu: "Produit - Couleur" ou "Produit - Couleur (xQuantité)"
        """
        if not lineitem_name or pd.isna(lineitem_name):
            return {'product': 'Inconnu', 'color': 'Aléatoire', 'quantity': default_quantity}
        
        # Extraire la quantité si elle est présente dans le nom de l'article
        quantity = default_quantity
        name = lineitem_name
        
        quantity_match = re.search(r'\(x(\d+)\)', lineitem_name)
        if quantity_match:
            quantity = int(quantity_match.group(1))
            name = re.sub(r'\(x\d+\)', '', lineitem_name).strip()
        
        # Extraire le produit et la couleur
        parts = name.split(' - ')
        if len(parts) >= 2:
            return {
                'product': parts[0].strip(),
                'color': parts[1].strip(),
                'quantity': quantity
            }
        else:
            # Si pas de séparateur, considérer que c'est juste le nom du produit
            return {
                'product': name.strip(),
                'color': 'Aléatoire',
                'quantity': quantity
            }
    
    def validate_csv(self, file_path):
        """
        Vérifie si un fichier CSV est bien un export Shopify valide
        Retourne (True, message) si valide, (False, message d'erreur) sinon
        """
        if not os.path.exists(file_path):
            return False, f"Le fichier {file_path} n'existe pas"
        
        try:
            # Lire les premières lignes du fichier
            df = pd.read_csv(file_path, nrows=5)
            
            # Vérifier les colonnes clés
            required_columns = ['Name', 'Email', 'Created at', 'Lineitem name']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f"Le fichier ne semble pas être un export Shopify valide. Colonnes manquantes: {', '.join(missing_columns)}"
            
            # Vérifier la présence de commandes
            if len(df) == 0:
                return False, "Le fichier CSV est vide"
            
            # Compter le nombre approximatif de commandes
            all_df = pd.read_csv(file_path)
            unique_orders = all_df['Name'].nunique()
            
            return True, f"Le fichier semble être un export Shopify valide. {unique_orders} commande(s) détectée(s)"
            
        except Exception as e:
            return False, f"Erreur lors de la validation du fichier: {str(e)}"