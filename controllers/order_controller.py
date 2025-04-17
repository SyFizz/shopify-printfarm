from models.database import Database
from models.order import Order
from config import DATABASE_PATH

class OrderController:
    """Contrôleur pour la gestion des commandes"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
    
    def get_all_orders(self):
        """Récupère toutes les commandes depuis la base de données"""
        orders = []
        
        # Récupérer les commandes
        self.db.cursor.execute("""
            SELECT id, date, client, email, status, priority, notes
            FROM orders
            ORDER BY date DESC
        """)
        
        for row in self.db.cursor.fetchall():
            order = Order(
                order_id=row['id'],
                date=row['date'],
                client=row['client'],
                email=row['email'],
                status=row['status'],
                priority=row['priority'],
                notes=row['notes']
            )
            
            # Récupérer les produits de la commande
            self.db.cursor.execute("""
                SELECT product, color, quantity, status
                FROM order_items
                WHERE order_id = ?
            """, (order.id,))
            
            for item_row in self.db.cursor.fetchall():
                order.add_item(
                    product=item_row['product'],
                    color=item_row['color'],
                    quantity=item_row['quantity'],
                    status=item_row['status']
                )
            
            orders.append(order)
        
        return orders
    
    def get_order_by_id(self, order_id):
        """Récupère une commande par son ID"""
        self.db.cursor.execute("""
            SELECT id, date, client, email, status, priority, notes
            FROM orders
            WHERE id = ?
        """, (order_id,))
        
        row = self.db.cursor.fetchone()
        if not row:
            return None
        
        order = Order(
            order_id=row['id'],
            date=row['date'],
            client=row['client'],
            email=row['email'],
            status=row['status'],
            priority=row['priority'],
            notes=row['notes']
        )
        
        # Récupérer les produits de la commande
        self.db.cursor.execute("""
            SELECT product, color, quantity, status
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        for item_row in self.db.cursor.fetchall():
            order.add_item(
                product=item_row['product'],
                color=item_row['color'],
                quantity=item_row['quantity'],
                status=item_row['status']
            )
        
        return order
    
    def update_order_status(self, order_id, new_status):
        """Met à jour le statut d'une commande"""
        self.db.cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (new_status, order_id))
        
        self.db.conn.commit()
        return True
    
    def update_item_status(self, order_id, product, color, new_status):
        """Met à jour le statut d'un produit dans une commande"""
        self.db.cursor.execute("""
            UPDATE order_items
            SET status = ?
            WHERE order_id = ? AND product = ? AND color = ?
        """, (new_status, order_id, product, color))
        
        self.db.conn.commit()
        
        # Mettre à jour le statut de la commande
        order = self.get_order_by_id(order_id)
        if order:
            order.update_status()
            self.update_order_status(order_id, order.status)
        
        return True
    
    def get_orders_by_status(self, status):
        """Récupère les commandes par statut"""
        orders = []
        
        self.db.cursor.execute("""
            SELECT id, date, client, email, status, priority, notes
            FROM orders
            WHERE status = ?
            ORDER BY date DESC
        """, (status,))
        
        for row in self.db.cursor.fetchall():
            order = Order(
                order_id=row['id'],
                date=row['date'],
                client=row['client'],
                email=row['email'],
                status=row['status'],
                priority=row['priority'],
                notes=row['notes']
            )
            
            # Récupérer les produits de la commande
            self.db.cursor.execute("""
                SELECT product, color, quantity, status
                FROM order_items
                WHERE order_id = ?
            """, (order.id,))
            
            for item_row in self.db.cursor.fetchall():
                order.add_item(
                    product=item_row['product'],
                    color=item_row['color'],
                    quantity=item_row['quantity'],
                    status=item_row['status']
                )
            
            orders.append(order)
        
        return orders
    def search_orders(self, query):
        """Recherche des commandes par ID, client ou email"""
        orders = []
        
        # Utiliser une recherche avec LIKE pour trouver les correspondances partielles
        self.db.cursor.execute("""
            SELECT id, date, client, email, status, priority, notes
            FROM orders
            WHERE id LIKE ? OR client LIKE ? OR email LIKE ?
            ORDER BY date DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        for row in self.db.cursor.fetchall():
            order = Order(
                order_id=row['id'],
                date=row['date'],
                client=row['client'],
                email=row['email'],
                status=row['status'],
                priority=row['priority'],
                notes=row['notes']
            )
            
            # Récupérer les produits de la commande
            self.db.cursor.execute("""
                SELECT product, color, quantity, status
                FROM order_items
                WHERE order_id = ?
            """, (order.id,))
            
            for item_row in self.db.cursor.fetchall():
                order.add_item(
                    product=item_row['product'],
                    color=item_row['color'],
                    quantity=item_row['quantity'],
                    status=item_row['status']
                )
            
            orders.append(order)
        
        return orders

    def update_order(self, order):
        """Met à jour une commande complète"""
        # Mettre à jour la commande elle-même
        self.db.cursor.execute("""
            UPDATE orders
            SET date = ?, client = ?, email = ?, status = ?, priority = ?, notes = ?
            WHERE id = ?
        """, (
            order.date,
            order.client,
            order.email,
            order.status,
            order.priority,
            order.notes,
            order.id
        ))
        
        # Supprimer tous les produits existants
        self.db.cursor.execute("""
            DELETE FROM order_items
            WHERE order_id = ?
        """, (order.id,))
        
        # Insérer les nouveaux produits
        for item in order.items:
            self.db.cursor.execute("""
                INSERT INTO order_items (order_id, product, color, quantity, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                order.id,
                item["product"],
                item["color"],
                item["quantity"],
                item["status"]
            ))
        
        self.db.conn.commit()
        return True

    def delete_order(self, order_id):
        """Supprime une commande et tous ses produits"""
        # Supprimer les produits
        self.db.cursor.execute("""
            DELETE FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        # Supprimer la commande
        self.db.cursor.execute("""
            DELETE FROM orders
            WHERE id = ?
        """, (order_id,))
        
        self.db.conn.commit()
        return True

    def get_orders_count_by_status(self):
        """Récupère le nombre de commandes par statut"""
        counts = {
            "En attente": 0,
            "En cours": 0,
            "Prêt": 0,
            "Expédié": 0,
            "Total": 0
        }
        
        self.db.cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM orders
            GROUP BY status
        """)
        
        for row in self.db.cursor.fetchall():
            status = row["status"]
            count = row["count"]
            
            if status in counts:
                counts[status] = count
                counts["Total"] += count
        
        return counts