class Product:
    """Modèle de données pour un produit"""
    
    def __init__(self, name, color, price=0.0):
        self.name = name
        self.color = color
        self.price = price
    
    @property
    def full_name(self):
        """Retourne le nom complet du produit avec sa couleur"""
        return f"{self.name} - {self.color}"
    
    def __str__(self):
        return self.full_name