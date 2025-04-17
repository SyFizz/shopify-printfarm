class InventoryItem:
    """Modèle de données pour un élément d'inventaire"""
    
    def __init__(self, product, color, stock=0, alert_threshold=3):
        self.product = product
        self.color = color
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
        return f"{self.product} - {self.color}: {self.stock} en stock"