class InventoryItem:
    """Modèle de données pour un élément d'inventaire"""
    
    def __init__(self, product, color, component=None, stock=0, alert_threshold=3):
        self.product = product
        self.color = color
        self.component = component  # Nom du composant ou None si produit simple
        self.stock = stock
        self.alert_threshold = alert_threshold
    
    def is_low_stock(self):
        """Vérifie si le stock est inférieur au seuil d'alerte"""
        return self.stock < self.alert_threshold
    
    def add_stock(self, quantity):
        """Ajoute du stock"""
        self.stock += quantity
    
    def remove_stock(self, quantity):
        """Retire du stock, sans aller en dessous de 0"""
        self.stock = max(0, self.stock - quantity)
    
    def __str__(self):
        if self.component:
            return f"{self.product} - {self.component} - {self.color}: {self.stock} en stock"
        return f"{self.product} - {self.color}: {self.stock} en stock"


class ColorVariant:
    """Modèle pour gérer les variantes de couleurs"""
    
    def __init__(self, base_color, variant_name, hex_code):
        self.base_color = base_color  # Couleur de base (ex: "Bleu")
        self.variant_name = variant_name  # Nom de la variante (ex: "Bleu Ciel")
        self.hex_code = hex_code  # Code couleur hexadécimal
    
    def __str__(self):
        return f"{self.variant_name} ({self.base_color})"


class ProductComponent:
    """Modèle pour représenter les composants d'un produit"""
    
    def __init__(self, product_name, component_name, quantity=1):
        self.product_name = product_name
        self.component_name = component_name
        self.quantity = quantity  # Nombre de pièces de ce composant nécessaires
    
    def __str__(self):
        return f"{self.component_name} ({self.quantity} pour {self.product_name})"


class InventoryForecast:
    """Modèle pour les prévisions d'inventaire"""
    
    def __init__(self, product, color, component=None, avg_monthly_sales=0, 
                 recommended_stock=0, trend_factor=1.0):
        self.product = product
        self.color = color
        self.component = component
        self.avg_monthly_sales = avg_monthly_sales
        self.recommended_stock = recommended_stock  # Stock recommandé pour un mois
        self.trend_factor = trend_factor  # Facteur multiplicateur basé sur les tendances actuelles
    
    def get_forecast_stock(self):
        """Calcule le stock recommandé en tenant compte des tendances"""
        return int(self.recommended_stock * self.trend_factor)
    
    def __str__(self):
        item_name = self.product
        if self.component:
            item_name = f"{self.product} - {self.component}"
        return f"{item_name} - {self.color}: {self.get_forecast_stock()} unités recommandées"