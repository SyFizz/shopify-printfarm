from models.database import Database
from config import DATABASE_PATH, PRODUCTS, COLORS

class InventoryController:
    """Contrôleur pour la gestion de l'inventaire"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.initialize_inventory()
    
    def initialize_inventory(self):
        """
        Initialise l'inventaire avec tous les produits et couleurs disponibles
        si ce n'est pas déjà fait
        """
        # Vérifier si l'inventaire est déjà initialisé
        self.db.cursor.execute("SELECT COUNT(*) as count FROM inventory")
        count = self.db.cursor.fetchone()['count']
        
        if count == 0:
            # Initialiser l'inventaire avec tous les produits et couleurs
            for product in PRODUCTS:
                for color in COLORS:
                    if color != "Aléatoire":  # Ne pas inclure "Aléatoire" dans l'inventaire
                        self.db.cursor.execute("""
                            INSERT INTO inventory (product, color, stock, alert_threshold)
                            VALUES (?, ?, 0, 3)
                        """, (product, color))
            
            self.db.conn.commit()
    
    def get_inventory(self):
        """Récupère tout l'inventaire"""
        inventory = []
        
        self.db.cursor.execute("""
            SELECT id, product, color, stock, alert_threshold
            FROM inventory
            ORDER BY product, color
        """)
        
        for row in self.db.cursor.fetchall():
            inventory.append({
                'id': row['id'],
                'product': row['product'],
                'color': row['color'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold']
            })
        
        return inventory
    
    def get_product_stock(self, product, color):
        """Récupère le stock d'un produit spécifique"""
        self.db.cursor.execute("""
            SELECT stock
            FROM inventory
            WHERE product = ? AND color = ?
        """, (product, color))
        
        row = self.db.cursor.fetchone()
        return row['stock'] if row else 0
    
    def update_stock(self, product, color, new_stock):
        """Met à jour le stock d'un produit"""
        self.db.cursor.execute("""
            UPDATE inventory
            SET stock = ?
            WHERE product = ? AND color = ?
        """, (new_stock, product, color))
        
        self.db.conn.commit()
        return True
    
    def adjust_stock(self, product, color, adjustment):
        """
        Ajuste le stock d'un produit par une quantité donnée
        (positive pour ajouter, négative pour retirer)
        """
        current_stock = self.get_product_stock(product, color)
        new_stock = max(0, current_stock + adjustment)  # Éviter un stock négatif
        
        return self.update_stock(product, color, new_stock)
    
    def update_alert_threshold(self, product, color, threshold):
        """Met à jour le seuil d'alerte d'un produit"""
        self.db.cursor.execute("""
            UPDATE inventory
            SET alert_threshold = ?
            WHERE product = ? AND color = ?
        """, (threshold, product, color))
        
        self.db.conn.commit()
        return True
    
    def get_low_stock_products(self):
        """Récupère les produits dont le stock est inférieur au seuil d'alerte"""
        low_stock = []
        
        self.db.cursor.execute("""
            SELECT product, color, stock, alert_threshold
            FROM inventory
            WHERE stock < alert_threshold
            ORDER BY product, color
        """)
        
        for row in self.db.cursor.fetchall():
            low_stock.append({
                'product': row['product'],
                'color': row['color'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold']
            })
        
        return low_stock
    
    def calculate_needed_prints(self):
        """
        Calcule le nombre de pièces à imprimer pour chaque produit
        en fonction des commandes en attente et du stock
        """
        needed_prints = []
        
        # Récupérer tous les produits à imprimer
        self.db.cursor.execute("""
            SELECT oi.product, oi.color, SUM(oi.quantity) as needed
            FROM order_items oi
            WHERE oi.status = 'À imprimer'
            GROUP BY oi.product, oi.color
        """)
        
        for row in self.db.cursor.fetchall():
            product = row['product']
            color = row['color']
            needed = row['needed']
            
            # Récupérer le stock actuel
            stock = self.get_product_stock(product, color)
            
            # Calculer combien d'unités il faut imprimer
            to_print = max(0, needed - stock)
            
            if to_print > 0:
                needed_prints.append({
                    'product': product,
                    'color': color,
                    'stock': stock,
                    'needed': needed,
                    'to_print': to_print
                })
        
        return needed_prints
    def get_product_to_print_count(self, product, color):
        """
        Récupère le nombre de produits à imprimer pour un produit et une couleur
        """
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'À imprimer'
        """, (product, color))
        
        row = self.db.cursor.fetchone()
        return row["count"] if row and row["count"] else 0

    def get_inventory_with_print_needs(self):
        """
        Récupère l'inventaire avec le nombre de produits à imprimer pour chaque item
        """
        inventory = []
        
        # Récupérer l'inventaire complet
        self.db.cursor.execute("""
            SELECT id, product, color, stock, alert_threshold
            FROM inventory
            ORDER BY product, color
        """)
        
        for row in self.db.cursor.fetchall():
            # Récupérer le nombre de produits à imprimer
            to_print = self.get_product_to_print_count(row["product"], row["color"])
            
            inventory.append({
                'id': row['id'],
                'product': row['product'],
                'color': row['color'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold'],
                'to_print': to_print,
                'status': 'OK' if row['stock'] >= row['alert_threshold'] else 'Low'
            })
        
        return inventory

    def adjust_inventory_after_printing(self, product, color, quantity):
        """
        Ajuste l'inventaire après une impression
        """
        # Récupérer le stock actuel
        current_stock = self.get_product_stock(product, color)
        
        # Ajouter la quantité imprimée
        new_stock = current_stock + quantity
        
        # Mettre à jour le stock
        self.update_stock(product, color, new_stock)
        
        return new_stock

    def adjust_inventory_after_order(self, order_id):
        """
        Ajuste l'inventaire après l'envoi d'une commande
        """
        # Récupérer les produits de la commande
        self.db.cursor.execute("""
            SELECT product, color, quantity
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        for row in self.db.cursor.fetchall():
            product = row["product"]
            color = row["color"]
            quantity = row["quantity"]
            
            # Récupérer le stock actuel
            current_stock = self.get_product_stock(product, color)
            
            # Soustraire la quantité expédiée
            new_stock = max(0, current_stock - quantity)
            
            # Mettre à jour le stock
            self.update_stock(product, color, new_stock)
        
        return True

    def get_inventory_summary(self):
        """
        Récupère un résumé de l'inventaire
        """
        summary = {
            "total_products": 0,
            "total_stock": 0,
            "low_stock_count": 0,
            "avg_stock_per_product": 0
        }
        
        # Nombre total de produits différents en stock
        self.db.cursor.execute("""
            SELECT COUNT(*) as count
            FROM inventory
            WHERE stock > 0
        """)
        summary["total_products"] = self.db.cursor.fetchone()["count"]
        
        # Stock total
        self.db.cursor.execute("""
            SELECT SUM(stock) as total
            FROM inventory
        """)
        summary["total_stock"] = self.db.cursor.fetchone()["total"] or 0
        
        # Nombre de produits en stock bas
        self.db.cursor.execute("""
            SELECT COUNT(*) as count
            FROM inventory
            WHERE stock < alert_threshold
        """)
        summary["low_stock_count"] = self.db.cursor.fetchone()["count"]
        
        # Stock moyen par produit
        if summary["total_products"] > 0:
            summary["avg_stock_per_product"] = summary["total_stock"] / summary["total_products"]
        
        return summary