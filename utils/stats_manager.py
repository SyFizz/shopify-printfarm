from controllers.order_controller import OrderController
from controllers.print_controller import PrintController
from controllers.inventory_controller import InventoryController
import datetime

class StatsManager:
    """Gestionnaire de statistiques pour le tableau de bord"""
    
    def __init__(self):
        self.order_controller = OrderController()
        self.print_controller = PrintController()
        self.inventory_controller = InventoryController()
    
    """ def get_dashboard_stats(self):
        stats = {}
        
        # Statistiques des commandes
        order_stats = self.order_controller.get_orders_count_by_status()
        stats["orders"] = order_stats
        
        # Statistiques du plan d'impression
        print_stats = self.print_controller.get_print_stats()
        stats["print"] = print_stats
        
        # Statistiques de l'inventaire
        inventory_stats = self.inventory_controller.get_inventory_summary()
        stats["inventory"] = inventory_stats
        
        # Produits les plus populaires
        popular_products = self.print_controller.get_most_common_products(5)
        stats["popular_products"] = popular_products
        
        # Couleurs les plus populaires
        popular_colors = self.print_controller.get_most_common_colors(5)
        stats["popular_colors"] = popular_colors
        
        # Produits en rupture de stock
        low_stock = self.inventory_controller.get_low_stock_products()
        stats["low_stock"] = low_stock
        
        # Plan d'impression par couleur
        color_summary = self.print_controller.get_color_summary()
        stats["color_summary"] = color_summary
        
        return stats """
        
    def get_dashboard_stats(self):
        """
        Récupère toutes les statistiques pour le tableau de bord
        """
        stats = {}
        
        # Statistiques des commandes
        # Pour le moment, retournons des données fictives
        stats["orders"] = {
            "En attente": 7,
            "En cours": 3,
            "Prêt": 5,
            "Expédié": 25,
            "Total": 40
        }
        
        # Statistiques du plan d'impression
        stats["print"] = {
            "total_to_print": 42,
            "products_count": 8,
            "colors_count": 6,
            "priority_high": 15,
            "priority_medium": 20,
            "priority_low": 7
        }
        
        # Statistiques de l'inventaire
        stats["inventory"] = {
            "total_products": 108,
            "total_stock": 324,
            "low_stock_count": 5,
            "avg_stock_per_product": 3.0
        }
        
        # Produits les plus populaires
        stats["popular_products"] = [
            {"product": "SpinRing", "total": 18},
            {"product": "Triggo", "total": 15},
            {"product": "StarNest", "total": 12},
            {"product": "OctoTwist", "total": 10},
            {"product": "Infinity Cube", "total": 8}
        ]
        
        # Couleurs les plus populaires
        stats["popular_colors"] = [
            {"color": "Bleu", "total": 22},
            {"color": "Rouge", "total": 15},
            {"color": "Vert", "total": 12},
            {"color": "Noir", "total": 10},
            {"color": "Aléatoire", "total": 8}
        ]
        
        # Produits en rupture de stock
        stats["low_stock"] = [
            {"product": "SpinRing", "color": "Bleu", "stock": 1, "alert_threshold": 3},
            {"product": "Triggo", "color": "Rouge", "stock": 0, "alert_threshold": 3},
            {"product": "StarNest", "color": "Vert", "stock": 2, "alert_threshold": 3},
            {"product": "OctoTwist", "color": "Noir", "stock": 1, "alert_threshold": 3},
            {"product": "Infinity Cube", "color": "Orange", "stock": 0, "alert_threshold": 2}
        ]
        
        # Plan d'impression par couleur
        stats["color_summary"] = [
            {"color": "Bleu", "product_count": 3, "total_quantity": 12},
            {"color": "Rouge", "product_count": 2, "total_quantity": 8},
            {"color": "Vert", "product_count": 2, "total_quantity": 7},
            {"color": "Noir", "product_count": 4, "total_quantity": 15},
            {"color": "Orange", "product_count": 1, "total_quantity": 5}
        ]
        
        return stats
    
    def get_print_efficiency(self, days=30):
        """
        Calcule l'efficacité d'impression: nombre de pièces imprimées par jour
        sur les X derniers jours
        """
        # Cette fonctionnalité serait à implémenter avec un suivi des impressions
        # Pour le moment, retournons une valeur factice
        return 12.5  # pièces par jour en moyenne
    
    def get_order_processing_time(self):
        """
        Calcule le temps moyen de traitement des commandes
        """
        # Cette fonctionnalité serait à implémenter avec un suivi des dates
        # Pour le moment, retournons une valeur factice
        return 2.3  # jours en moyenne
    
    def get_current_day_stats(self):
        """
        Récupère les statistiques pour la journée en cours
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Nombre de commandes reçues aujourd'hui
        # Nombre de commandes complétées aujourd'hui
        # Nombre de pièces imprimées aujourd'hui
        
        # Pour le moment, retournons des valeurs factices
        return {
            "new_orders": 5,
            "completed_orders": 3,
            "printed_items": 25
        }