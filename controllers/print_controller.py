from models.database import Database
from config import DATABASE_PATH, PRIORITIES

class PrintController:
    """Contrôleur pour la gestion du plan d'impression"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
    
    def get_print_plan(self, include_printing=True):
        """
        Récupère le plan d'impression organisé par couleur
        et regroupé par produit
        
        Args:
            include_printing (bool): Si True, inclut aussi les produits en cours d'impression
        """
        plan = {}
        
        # Préparer la condition pour le statut
        status_condition = "'À imprimer'" if not include_printing else "'À imprimer', 'En impression'"
        
        # Récupérer tous les produits à imprimer et en cours d'impression
        query = f"""
            SELECT oi.product, oi.color, SUM(oi.quantity) as total_quantity,
                   GROUP_CONCAT(oi.order_id) as order_ids, oi.status
            FROM order_items oi
            WHERE oi.status IN ({status_condition})
            GROUP BY oi.product, oi.color, oi.status
            ORDER BY oi.color, oi.product
        """
        
        self.db.cursor.execute(query)
        
        for row in self.db.cursor.fetchall():
            color = row['color']
            product = row['product']
            quantity = row['total_quantity']
            order_ids = row['order_ids'].split(',') if row['order_ids'] else []
            status = row['status']
            
            # Déterminer la priorité en fonction de la quantité
            priority = "Haute" if quantity > 3 else ("Moyenne" if quantity > 1 else "Basse")
            
            # Organiser par couleur
            if color not in plan:
                plan[color] = []
            
            plan[color].append({
                'product': product,
                'quantity': quantity,
                'order_ids': order_ids,
                'priority': priority,
                'status': status
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
        ou pour les commandes spécifiées.
        Ne marque QUE les produits qui sont actuellement en cours d'impression,
        pas ceux qui sont encore à imprimer.
        """
        if orders:
            # Mettre à jour uniquement les commandes spécifiées
            placeholders = ', '.join(['?'] * len(orders))
            query = f"""
                UPDATE order_items
                SET status = 'Imprimé'
                WHERE product = ? AND color = ? AND status = 'En impression'
                AND order_id IN ({placeholders})
            """
            params = [product, color] + orders
        else:
            # Mettre à jour toutes les commandes
            query = """
                UPDATE order_items
                SET status = 'Imprimé'
                WHERE product = ? AND color = ? AND status = 'En impression'
            """
            params = [product, color]
        
        self.db.cursor.execute(query, params)
        self.db.conn.commit()
        
        # Mettre à jour le statut des commandes concernées
        self.db.cursor.execute("""
            SELECT DISTINCT order_id
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'Imprimé'
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
        
        return len(updated_orders)
    
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
        try:
            # Utiliser un timeout plus long pour les opérations sur la base de données
            self.db.conn.execute("PRAGMA busy_timeout = 5000")
            
            # Début d'une transaction explicite avec execute à la place de begin
            self.db.conn.execute("BEGIN TRANSACTION")
            
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
            
            # Valider les changements immédiatement avant d'appeler d'autres contrôleurs
            self.db.conn.commit()
            
            # Pour chaque commande mise à jour, vérifier si elle est complète
            # Utiliser une nouvelle connexion pour éviter les blocages
            from controllers.order_controller import OrderController
            order_controller = OrderController()
            
            for order_id in updated_orders:
                order = order_controller.get_order_by_id(order_id)
                if order:
                    order.update_status()
                    try:
                        order_controller.update_order_status(order_id, order.status)
                    except Exception as e:
                        print(f"Erreur lors de la mise à jour du statut de la commande {order_id}: {e}")
            
            # Retourner le nombre de produits concernés
            self.db.cursor.execute("""
                SELECT SUM(quantity) as count
                FROM order_items
                WHERE product = ? AND color = ? AND status = 'En impression'
            """, (product, color))
            
            count = self.db.cursor.fetchone()["count"] or 0
            return count
            
        except Exception as e:
            # En cas d'erreur, annuler la transaction et relancer l'exception
            print(f"Erreur lors du démarrage de l'impression: {e}")
            self.db.conn.rollback()
            raise

    def start_printing_batch_partial(self, product, color, quantity_to_print):
        """
        Marque un lot partiel de produits comme 'En impression'
        
        Args:
            product (str): Nom du produit
            color (str): Couleur du produit
            quantity_to_print (int): Quantité à imprimer dans ce lot
        
        Returns:
            int: Nombre de produits mis en impression
        """
        try:
            # Utiliser un timeout plus long pour les opérations sur la base de données
            self.db.conn.execute("PRAGMA busy_timeout = 5000")
            
            # Vérifier que la quantité demandée est disponible
            self.db.cursor.execute("""
                SELECT SUM(quantity) as total
                FROM order_items
                WHERE product = ? AND color = ? AND status = 'À imprimer'
            """, (product, color))
            
            total_available = self.db.cursor.fetchone()["total"] or 0
            
            if total_available < quantity_to_print:
                raise ValueError(f"Quantité demandée ({quantity_to_print}) supérieure à la quantité disponible ({total_available})")
            
            # Démarrer une transaction explicite
            self.db.conn.execute("BEGIN TRANSACTION")
            
            # Si on ne demande pas d'imprimer la totalité, on doit diviser les entrées
            if quantity_to_print < total_available:
                # Stratégie: on commence par les commandes les plus petites
                self.db.cursor.execute("""
                    SELECT id, order_id, quantity
                    FROM order_items
                    WHERE product = ? AND color = ? AND status = 'À imprimer'
                    ORDER BY quantity ASC
                """, (product, color))
                
                items = self.db.cursor.fetchall()
                remaining = quantity_to_print
                updated_orders = set()
                
                # Parcourir les items à mettre en impression
                for item in items:
                    item_id = item["id"]
                    order_id = item["order_id"]
                    item_quantity = item["quantity"]
                    
                    if remaining <= 0:
                        break
                    
                    if item_quantity <= remaining:
                        # Si tout l'item peut être mis en impression
                        self.db.cursor.execute("""
                            UPDATE order_items
                            SET status = 'En impression'
                            WHERE id = ?
                        """, (item_id,))
                        
                        remaining -= item_quantity
                        updated_orders.add(order_id)
                    else:
                        # Si on ne peut imprimer qu'une partie de l'item
                        # 1. Réduire la quantité de l'item original
                        self.db.cursor.execute("""
                            UPDATE order_items
                            SET quantity = quantity - ?
                            WHERE id = ?
                        """, (remaining, item_id))
                        
                        # 2. Créer un nouvel item pour la quantité en impression
                        self.db.cursor.execute("""
                            INSERT INTO order_items (order_id, product, color, quantity, status)
                            VALUES (?, ?, ?, ?, 'En impression')
                        """, (order_id, product, color, remaining))
                        
                        remaining = 0
                        updated_orders.add(order_id)
            else:
                # Si on imprime tout, c'est plus simple
                self.db.cursor.execute("""
                    UPDATE order_items
                    SET status = 'En impression'
                    WHERE product = ? AND color = ? AND status = 'À imprimer'
                """, (product, color))
                
                # Récupérer les commandes concernées
                self.db.cursor.execute("""
                    SELECT DISTINCT order_id
                    FROM order_items
                    WHERE product = ? AND color = ? AND status = 'En impression'
                """, (product, color))
                
                updated_orders = {row['order_id'] for row in self.db.cursor.fetchall()}
            
            # Valider les changements
            self.db.conn.commit()
            
            # Mettre à jour les statuts des commandes
            from controllers.order_controller import OrderController
            order_controller = OrderController()
            
            for order_id in updated_orders:
                order = order_controller.get_order_by_id(order_id)
                if order:
                    order.update_status()
                    order_controller.update_order_status(order_id, order.status)
            
            return quantity_to_print
            
        except Exception as e:
            # En cas d'erreur, annuler la transaction et relancer l'exception
            print(f"Erreur lors du démarrage de l'impression partielle: {e}")
            self.db.conn.rollback()
            raise

    def get_color_summary(self):
        """
        Récupère un résumé des couleurs à imprimer pour le tableau de bord
        
        Returns:
            list: Liste des couleurs avec le nombre de produits et quantités
        """
        color_summary = []
        
        self.db.cursor.execute("""
            SELECT color, COUNT(DISTINCT product) as product_count, SUM(quantity) as total_quantity
            FROM order_items
            WHERE status = 'À imprimer' OR status = 'En impression'
            GROUP BY color
            ORDER BY total_quantity DESC
        """)
        
        for row in self.db.cursor.fetchall():
            color_summary.append({
                "color": row["color"],
                "product_count": row["product_count"],
                "total_quantity": row["total_quantity"]
            })
        
        return color_summary