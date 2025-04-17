from utils.csv_parser import ShopifyCSVParser
from models.database import Database
import os
from config import DATABASE_PATH
from PyQt5.QtCore import QObject, pyqtSignal

class ImportSignals(QObject):
    """Signaux pour le processus d'importation"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

class ImportController:
    """Contrôleur pour gérer l'importation des données depuis Shopify"""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.parser = ShopifyCSVParser()
        self.signals = ImportSignals()
        
        # Ne pas créer de connexion à la base de données ici
        # elle sera créée dans chaque méthode qui en a besoin
        
        # Connecter les signaux du parser aux signaux du contrôleur
        self.parser.signals.progress.connect(self.signals.progress)
        self.parser.signals.status.connect(self.signals.status)
    
    def import_shopify_csv(self, file_path, skip_existing=True, default_status="En attente", default_priority="Moyenne"):
        """
        Importe les commandes depuis un fichier CSV de Shopify
        et les enregistre dans la base de données
        """
        # Créer une nouvelle connexion à la base de données dans ce thread
        db = Database(self.db_path)
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            self.signals.status.emit(f"Le fichier {file_path} n'existe pas")
            self.signals.finished.emit(False, f"Le fichier {file_path} n'existe pas")
            return False, f"Le fichier {file_path} n'existe pas"
        
        # Parser le fichier CSV
        self.signals.status.emit("Analyse du fichier CSV...")
        orders = self.parser.parse_file(file_path)
        
        if not orders:
            self.signals.status.emit("Aucune commande n'a pu être extraite du fichier")
            self.signals.finished.emit(False, "Aucune commande n'a pu être extraite du fichier")
            return False, "Aucune commande n'a pu être extraite du fichier"
        
        # Insérer les commandes dans la base de données
        self.signals.status.emit(f"Importation de {len(orders)} commandes...")
        imported_count = 0
        skipped_count = 0
        
        for i, order in enumerate(orders):
            # Mettre à jour la progression
            progress = 90 + int((i / len(orders)) * 10)  # De 90% à 100%
            self.signals.progress.emit(progress)
            
            # Vérifier si la commande existe déjà
            db.cursor.execute("SELECT id FROM orders WHERE id = ?", (order.id,))
            existing = db.cursor.fetchone()
            
            if existing and skip_existing:
                skipped_count += 1
                self.signals.status.emit(f"Commande {order.id} déjà existante, ignorée.")
                continue
            
            # Supprimer la commande existante si on ne skip pas
            if existing and not skip_existing:
                db.cursor.execute("DELETE FROM orders WHERE id = ?", (order.id,))
                db.cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order.id,))
            
            # Insérer la commande
            db.cursor.execute("""
                INSERT INTO orders (id, date, client, email, status, priority, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order.id, 
                order.date, 
                order.client, 
                order.email, 
                default_status if default_status else order.status, 
                default_priority if default_priority else order.priority, 
                order.notes
            ))
            
            # Insérer les produits de la commande
            for item in order.items:
                item_status = "À imprimer"
                if default_status == "Prêt":
                    item_status = "Imprimé"
                elif default_status == "En cours":
                    item_status = "En impression"
                
                db.cursor.execute("""
                    INSERT INTO order_items (order_id, product, color, quantity, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    order.id,
                    item["product"],
                    item["color"],
                    item["quantity"],
                    item_status
                ))
            
            imported_count += 1
            
            # Log pour chaque 10 commandes importées
            if imported_count % 10 == 0:
                self.signals.status.emit(f"{imported_count} commandes importées...")
        
        # Valider les changements
        db.conn.commit()
        
        # Fermer la connexion
        db.close()
        
        result_message = f"{imported_count} commandes importées avec succès"
        if skipped_count > 0:
            result_message += f", {skipped_count} commandes ignorées (déjà existantes)"
        
        self.signals.status.emit(result_message)
        self.signals.finished.emit(True, result_message)
        
        return True, result_message
    
    def validate_shopify_csv(self, file_path):
        """
        Vérifie si un fichier CSV est bien un export Shopify valide
        """
        return self.parser.validate_csv(file_path)