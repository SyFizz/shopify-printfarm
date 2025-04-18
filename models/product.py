class Product:
    """Modèle de données pour un produit"""
    
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.components = []  # Liste des composants nécessaires
        self.assembled_items = {}  # Inventaire des produits assemblés par couleur
        self.color_constraints = {}  # Contraintes de couleur pour les composants
    
    @property
    def full_name(self):
        """Retourne le nom complet du produit avec sa couleur"""
        return f"{self.name} - {self.color}"
    
    def __str__(self):
        return self.full_name
    
    def add_component(self, component_name, quantity=1, color_constraint=None):
        """
        Ajoute un composant nécessaire pour ce produit
        
        Args:
            component_name (str): Nom du composant
            quantity (int): Nombre d'unités nécessaires
            color_constraint (str, optional): Contrainte de couleur pour ce composant
                - None: Utiliser la couleur spécifiée lors de l'assemblage
                - "same_as_main": Même couleur que le produit principal
                - "fixed:COLOR": Couleur fixe spécifique (ex: "fixed:Noir")
                - "same_as:COMPONENT": Même couleur qu'un autre composant (ex: "same_as:montant")
        """
        # Vérifier si le composant existe déjà dans la liste
        existing_component = None
        for comp in self.components:
            if comp["name"] == component_name:
                existing_component = comp
                break
                
        if existing_component:
            # Mettre à jour la quantité si le composant existe déjà
            existing_component["quantity"] = quantity
        else:
            # Ajouter un nouveau composant
            self.components.append({
                "name": component_name,
                "quantity": quantity
            })
        
        # Ajouter la contrainte de couleur si spécifiée
        if color_constraint:
            self.color_constraints[component_name] = color_constraint