from models.database import Database
from config import DATABASE_PATH, PRIORITIES

class PrintController:
    """Contrôleur pour la gestion du plan d'impression"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
    
    def get_print_plan(self):
        """
        Récupère le plan d'impression organisé par couleur
        et regroupé par produit
        """
        plan = {}
        
        # Récupérer tous les produits à imprimer
        self.db.cursor.execute("""
            SELECT oi.product, oi.color, SUM(oi.quantity) as total_quantity,
                   GROUP_CONCAT(oi.order_id) as order_ids
            FROM order_items oi
            WHERE oi.status = 'À imprimer'
            GROUP BY oi.product, oi.color
            ORDER BY oi.color, oi.product
        """)
        
        for row in self.db.cursor.fetchall():
            color = row['color']
            product = row['product']
            quantity = row['total_quantity']
            order_ids = row['order_ids'].split(',') if row['order_ids'] else []
            
            # Déterminer la priorité en fonction de la quantité
            priority = "Haute" if quantity > 3 else ("Moyenne" if quantity > 1 else "Basse")
            
            # Organiser par couleur
            if color not in plan:
                plan[color] = []
            
            plan[color].append({
                'product': product,
                'quantity': quantity,
                'order_ids': order_ids,
                'priority': priority
            })
        
        return plan
    
    def get_print_plan_by_color(self, color):
        """Récupère le plan d'impression pour une couleur spécifique"""
        items = []
        
        self.db.cursor.execute("""
            SELECT oi.product, SUM(oi.quantity) as total_quantity,
                   GROUP_CONCAT(oi.order_id) as order_ids
            FROM order_items oi
            WHERE oi.status = 'À imprimer' AND oi.color = ?
            GROUP BY oi.product
            ORDER BY oi.product
        """, (color,))
        
        for row in self.db.cursor.fetchall():
            product = row['product']
            quantity = row['total_quantity']
            order_ids = row['order_ids'].split(',') if row['order_ids'] else []
            
            # Déterminer la priorité en fonction de la quantité
            priority = "Haute" if quantity > 3 else ("Moyenne" if quantity > 1 else "Basse")
            
            items.append({
                'product': product,
                'quantity': quantity,
                'order_ids': order_ids,
                'priority': priority
            })
        
        return items
    
    def mark_as_printed(self, product, color, orders=None):
        """
        Marque un produit comme imprimé pour toutes les commandes
        ou pour les commandes spécifiées
        """
        if orders:
            # Mettre à jour uniquement les commandes spécifiées
            placeholders = ', '.join(['?'] * len(orders))
            query = f"""
                UPDATE order_items
                SET status = 'Imprimé'
                WHERE product = ? AND color = ? AND status = 'À imprimer'
                AND order_id IN ({placeholders})
            """
            params = [product, color] + orders
        else:
            # Mettre à jour toutes les commandes
            query = """
                UPDATE order_items
                SET status = 'Imprimé'
                WHERE product = ? AND color = ? AND status = 'À imprimer'
            """
            params = [product, color]
        
        self.db.cursor.execute(query, params)
        
        # Mettre à jour le statut des commandes concernées
        self.db.cursor.execute("""
            SELECT DISTINCT order_id
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'Imprimé'
        """, (product, color))
        
        updated_orders = [row['order_id'] for row in self.db.cursor.fetchall()]
        
        # Pour chaque commande mise à jour,
            
    def get_print_stats(self):
        """
        Récupère des statistiques sur le plan d'impression
        """
        stats = {
            "total_to_print": 0,
            "products_count": 0,
            "colors_count": 0,
            "priority_high": 0,
            "priority_medium": 0,
            "priority_low": 0
        }
        
        # Nombre total de pièces à imprimer
        self.db.cursor.execute("""
            SELECT SUM(quantity) as total
            FROM order_items
            WHERE status = 'À imprimer'
        """)
        row = self.db.cursor.fetchone()
        stats["total_to_print"] = row["total"] if row["total"] else 0
        
        # Nombre de produits différents à imprimer
        self.db.cursor.execute("""
            SELECT COUNT(DISTINCT product) as count
            FROM order_items
            WHERE status = 'À imprimer'
        """)
        stats["products_count"] = self.db.cursor.fetchone()["count"]
        
        # Nombre de couleurs différentes à imprimer
        self.db.cursor.execute("""
            SELECT COUNT(DISTINCT color) as count
            FROM order_items
            WHERE status = 'À imprimer'
        """)
        stats["colors_count"] = self.db.cursor.fetchone()["count"]
        
        # Nombre de pièces par priorité
        # La priorité est déterminée par la quantité
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE status = 'À imprimer' AND quantity > 3
        """)
        stats["priority_high"] = self.db.cursor.fetchone()["count"] or 0
        
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE status = 'À imprimer' AND quantity > 1 AND quantity <= 3
        """)
        stats["priority_medium"] = self.db.cursor.fetchone()["count"] or 0
        
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE status = 'À imprimer' AND quantity = 1
        """)
        stats["priority_low"] = self.db.cursor.fetchone()["count"] or 0
        
        return stats

    def get_most_common_products(self, limit=5):
        """
        Récupère les produits les plus commandés
        """
        products = []
        
        self.db.cursor.execute("""
            SELECT product, SUM(quantity) as total
            FROM order_items
            GROUP BY product
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))
        
        for row in self.db.cursor.fetchall():
            products.append({
                "product": row["product"],
                "total": row["total"]
            })
        
        return products

    def get_most_common_colors(self, limit=5):
        """
        Récupère les couleurs les plus demandées
        """
        colors = []
        
        self.db.cursor.execute("""
            SELECT color, SUM(quantity) as total
            FROM order_items
            GROUP BY color
            ORDER BY total DESC
            LIMIT ?
        """, (limit,))
        
        for row in self.db.cursor.fetchall():
            colors.append({
                "color": row["color"],
                "total": row["total"]
            })
        
        return colors

    def start_printing_batch(self, product, color):
        """
        Marque un lot de produits comme 'En impression'
        """
        self.db.cursor.execute("""
            UPDATE order_items
            SET status = 'En impression'
            WHERE product = ? AND color = ? AND status = 'À imprimer'
        """, (product, color))
        
        # Mettre à jour le statut des commandes concernées
        self.db.cursor.execute("""
            SELECT DISTINCT order_id
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'En impression'
        """, (product, color))
        
        updated_orders = [row['order_id'] for row in self.db.cursor.fetchall()]
        
        # Pour chaque commande mise à jour, vérifier si elle est complète
        from controllers.order_controller import OrderController
        order_controller = OrderController()
        
        for order_id in updated_orders:
            order = order_controller.get_order_by_id(order_id)
            if order:
                order.update_status()
                order_controller.update_order_status(order_id, order.status)
        
        self.db.conn.commit()
        
        # Retourner le nombre de produits concernés
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'En impression'
        """, (product, color))
        
        count = self.db.cursor.fetchone()["count"] or 0
        return count