from models.database import Database
from config import DATABASE_PATH
from controllers.order_controller import OrderController
from controllers.print_controller import PrintController
from controllers.inventory_controller import InventoryController

class WorkflowController:
    """
    Contrôleur pour gérer les workflows complets (commande, impression, expédition)
    """
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.order_controller = OrderController()
        self.print_controller = PrintController()
        self.inventory_controller = InventoryController()
    
    def process_printing_batch(self, product, color, quantity):
        """
        Traite un lot d'impression complet:
        1. Marque les produits comme imprimés
        2. Met à jour le statut des commandes
        3. Ajuste l'inventaire
        """
        # Marquer les produits comme imprimés
        self.print_controller.mark_as_printed(product, color)
        
        # Ajuster l'inventaire
        self.inventory_controller.adjust_inventory_after_printing(product, color, quantity)
        
        # Récupérer les commandes impactées
        self.db.cursor.execute("""
            SELECT DISTINCT order_id
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'Imprimé'
        """, (product, color))
        
        impacted_orders = [row["order_id"] for row in self.db.cursor.fetchall()]
        
        # Mettre à jour le statut de chaque commande
        updated_orders = []
        for order_id in impacted_orders:
            order = self.order_controller.get_order_by_id(order_id)
            if order:
                previous_status = order.status
                order.update_status()
                if previous_status != order.status:
                    self.order_controller.update_order_status(order_id, order.status)
                    updated_orders.append(order_id)
        
        return {
            "product": product,
            "color": color,
            "quantity": quantity,
            "impacted_orders": len(impacted_orders),
            "updated_orders": len(updated_orders)
        }
    
    def ship_order(self, order_id):
        """
        Marque une commande comme expédiée:
        1. Met à jour le statut de la commande
        2. Ajuste l'inventaire si nécessaire
        """
        # Récupérer la commande
        order = self.order_controller.get_order_by_id(order_id)
        if not order:
            return False, "Commande non trouvée"
        
        # Vérifier que tous les produits sont prêts
        if not order.is_complete():
            return False, "Tous les produits de la commande ne sont pas prêts"
        
        # Marquer la commande comme expédiée
        self.order_controller.update_order_status(order_id, "Expédié")
        
        # Ajuster l'inventaire
        self.inventory_controller.adjust_inventory_after_order(order_id)
        
        return True, "Commande expédiée avec succès"
    
    def cancel_order(self, order_id):
        """
        Annule une commande:
        1. Met à jour le statut de la commande
        2. Remet les produits en stock si nécessaire
        """
        # Récupérer la commande
        order = self.order_controller.get_order_by_id(order_id)
        if not order:
            return False, "Commande non trouvée"
        
        # Récupérer les produits qui ont été imprimés
        printed_items = order.get_items_by_status("Imprimé")
        
        # Remettre ces produits en stock
        for item in printed_items:
            current_stock = self.inventory_controller.get_product_stock(item["product"], item["color"])
            new_stock = current_stock + item["quantity"]
            self.inventory_controller.update_stock(item["product"], item["color"], new_stock)
        
        # Marquer la commande comme annulée
        self.order_controller.update_order_status(order_id, "Annulé")
        
        return True, f"Commande annulée avec succès. {len(printed_items)} produits remis en stock."
    
    def optimize_print_plan(self):
        """
        Optimise le plan d'impression en fonction de différents critères:
        - Priorité des commandes
        - Regroupement par couleur
        - Stock disponible
        - Etc.
        """
        # Récupérer le plan d'impression actuel
        print_plan = self.print_controller.get_print_plan()
        
        # Pour chaque couleur, calculer un score de priorité
        color_priorities = {}
        for color, products in print_plan.items():
            # Somme des quantités
            total_quantity = sum(prod["quantity"] for prod in products)
            
            # Nombre de produits différents
            product_count = len(products)
            
            # Nombre de commandes impactées
            order_count = len(set(order_id for prod in products for order_id in prod["order_ids"]))
            
            # Calculer un score (plus il est élevé, plus la couleur est prioritaire)
            score = (total_quantity * 0.5) + (product_count * 0.3) + (order_count * 0.2)
            
            color_priorities[color] = {
                "score": score,
                "total_quantity": total_quantity,
                "product_count": product_count,
                "order_count": order_count
            }
        
        # Trier les couleurs par score décroissant
        sorted_colors = sorted(color_priorities.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # Retourner le plan d'impression optimisé
        optimized_plan = []
        for color, stats in sorted_colors:
            optimized_plan.append({
                "color": color,
                "stats": stats,
                "products": print_plan[color]
            })
        
        return optimized_plan