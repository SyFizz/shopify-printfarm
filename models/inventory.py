"""
Modèles de données pour la gestion de l'inventaire Plasmik3D.
Ce module définit les structures pour:
- Les composants (pièces individuelles)
- Les produits (combinaisons de composants)
- La gestion des stocks par couleur
- Les relations entre composants et produits
"""

class InventoryItem:
    """Classe de base pour tout élément d'inventaire (composant ou produit)"""
    
    def __init__(self, name, color=None, stock=0, alert_threshold=3):
        self.name = name
        self.color = color  # Peut être None pour les composants sans couleur spécifique
        self.stock = stock
        self.alert_threshold = alert_threshold
    
    def is_low_stock(self):
        """Vérifie si le stock est inférieur au seuil d'alerte"""
        return self.stock < self.alert_threshold
    
    def add_stock(self, quantity):
        """Ajoute du stock"""
        self.stock += quantity
        return self.stock
    
    def remove_stock(self, quantity):
        """Retire du stock, sans aller en dessous de 0"""
        if quantity > self.stock:
            # Lever une exception ou retourner False pour indiquer l'échec
            raise ValueError(f"Stock insuffisant: {self.stock} disponible, {quantity} demandé")
        
        self.stock -= quantity
        return self.stock
    
    def __str__(self):
        color_str = f" - {self.color}" if self.color else ""
        return f"{self.name}{color_str}: {self.stock} en stock"


class Component(InventoryItem):
    """Modèle pour un composant (pièce individuelle)"""
    
    def __init__(self, name, color=None, stock=0, alert_threshold=3):
        super().__init__(name, color, stock, alert_threshold)
        self.used_in_products = []  # Liste des produits utilisant ce composant
    
    def add_product_usage(self, product_name):
        """Ajoute un produit utilisant ce composant"""
        if product_name not in self.used_in_products:
            self.used_in_products.append(product_name)


class Product:
    """Modèle pour un produit (composé de plusieurs composants)"""
    
    def __init__(self, name, description=""):
        self.name = name
        self.description = description
        self.components = []  # Liste des composants nécessaires
        self.assembled_items = {}  # Inventaire des produits assemblés par couleur
        self.color_constraints = {}  # Contraintes de couleur pour les composants
    
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
        for comp in self.components:
            if comp["name"] == component_name:
                # Mettre à jour la quantité si le composant existe déjà
                comp["quantity"] = quantity
                if color_constraint:
                    self.color_constraints[component_name] = color_constraint
                return
        
        # Ajouter un nouveau composant
        self.components.append({
            "name": component_name,
            "quantity": quantity
        })
        
        # Ajouter la contrainte de couleur si spécifiée
        if color_constraint:
            self.color_constraints[component_name] = color_constraint
    
    def get_component_color(self, component_name, product_color, assembly_colors=None):
        """
        Détermine la couleur à utiliser pour un composant en fonction des contraintes
        
        Args:
            component_name (str): Nom du composant
            product_color (str): Couleur principale du produit
            assembly_colors (dict, optional): Couleurs spécifiées pour l'assemblage
        
        Returns:
            str: Couleur à utiliser pour ce composant
        """
        # Si aucune contrainte définie, utiliser la couleur du produit
        if component_name not in self.color_constraints:
            # Si des couleurs spécifiques sont fournies pour l'assemblage, les utiliser
            if assembly_colors and component_name in assembly_colors:
                return assembly_colors[component_name]
            return product_color
        
        constraint = self.color_constraints[component_name]
        
        # Traiter les différents types de contraintes
        if constraint == "same_as_main":
            return product_color
        elif constraint.startswith("fixed:"):
            return constraint.split(":", 1)[1]
        elif constraint.startswith("same_as:"):
            ref_component = constraint.split(":", 1)[1]
            # Récursion pour obtenir la couleur du composant référencé
            return self.get_component_color(ref_component, product_color, assembly_colors)
        
        # Par défaut, utiliser la couleur du produit
        return product_color
    
    def add_assembled_product(self, color, quantity=1):
        """Ajoute un produit assemblé à l'inventaire"""
        if color in self.assembled_items:
            self.assembled_items[color] += quantity
        else:
            self.assembled_items[color] = quantity
        
        return self.assembled_items[color]
    
    def remove_assembled_product(self, color, quantity=1):
        """Retire un produit assemblé de l'inventaire"""
        if color not in self.assembled_items:
            raise ValueError(f"Aucun produit {self.name} de couleur {color} en stock")
        
        if self.assembled_items[color] < quantity:
            raise ValueError(f"Stock insuffisant: {self.assembled_items[color]} disponible, {quantity} demandé")
        
        self.assembled_items[color] -= quantity
        
        # Supprimer l'entrée si le stock atteint zéro
        if self.assembled_items[color] == 0:
            del self.assembled_items[color]
        
        return quantity
    
    def get_total_assembled(self):
        """Retourne le nombre total de produits assemblés toutes couleurs confondues"""
        return sum(self.assembled_items.values())
    
    def get_assemblable_count(self, component_inventory, color=None):
        """
        Calcule le nombre de produits assemblables avec le stock de composants disponible
        
        Args:
            component_inventory (dict): Stock des composants {nom: {couleur: quantité}}
            color (str, optional): Couleur spécifique à vérifier, ou None pour calculer
                                  le nombre maximal assemblable quelle que soit la couleur
        
        Returns:
            int: Nombre de produits assemblables
        """
        if not self.components:
            return 0  # Pas de composants définis, impossible d'assembler
        
        min_assemblable = float('inf')
        
        for comp in self.components:
            component_name = comp["name"]
            quantity_needed = comp["quantity"]
            
            # Déterminer la couleur du composant
            component_color = self.get_component_color(component_name, color) if color else None
            
            # Si une couleur spécifique est demandée
            if component_color:
                if (component_name not in component_inventory or 
                    component_color not in component_inventory[component_name]):
                    return 0  # Composant ou couleur non disponible
                
                stock = component_inventory[component_name][component_color]
                possible = stock // quantity_needed
                min_assemblable = min(min_assemblable, possible)
            else:
                # Si aucune couleur spécifique n'est demandée, chercher la couleur la plus disponible
                max_possible = 0
                if component_name in component_inventory:
                    for color_stock in component_inventory[component_name].values():
                        possible = color_stock // quantity_needed
                        max_possible = max(max_possible, possible)
                
                if max_possible == 0:
                    return 0  # Aucune couleur disponible pour ce composant
                
                min_assemblable = min(min_assemblable, max_possible)
        
        # Si aucun composant n'a été trouvé, ou si la quantité est infinie
        if min_assemblable == float('inf'):
            return 0
        
        return min_assemblable
    
    def __str__(self):
        components_str = ", ".join([f"{c['quantity']} x {c['name']}" for c in self.components])
        return f"{self.name} ({components_str})"


class ColorVariant:
    """Modèle pour gérer les variantes de couleurs"""
    
    def __init__(self, base_color, variant_name, hex_code):
        self.base_color = base_color  # Couleur de base (ex: "Bleu")
        self.variant_name = variant_name  # Nom de la variante (ex: "Bleu Ciel")
        self.hex_code = hex_code  # Code couleur hexadécimal
    
    def __str__(self):
        return f"{self.variant_name} ({self.base_color})"


class InventoryManager:
    """Gestionnaire global de l'inventaire"""
    
    def __init__(self):
        self.components = {}  # {nom: {couleur: Component}}
        self.products = {}  # {nom: Product}
        self.color_variants = {}  # {variante: ColorVariant}
    
    def add_product(self, name, description=""):
        """Ajoute un produit au catalogue"""
        try:
            # Vérifier si le produit existe déjà
            if name in self.products:
                return self.products[name]
            
            # Créer un nouveau produit
            product = Product(name, description)
            self.products[name] = product
            return product
        except Exception as e:
            # Pour le diagnostic
            print(f"Exception dans InventoryManager.add_product: {repr(e)}")
            raise  # Re-lever l'exception pour qu'elle puisse être gérée plus haut
    
    def add_component(self, name, color, stock=0, alert_threshold=3, description=""):
        """Ajoute un composant à l'inventaire"""
        if name not in self.components:
            self.components[name] = {}
        
        if color not in self.components[name]:
            self.components[name][color] = Component(name, color, stock, alert_threshold)
            # Pour le moment, nous n'utilisons pas la description pour les composants
            # Vous pourriez étendre la classe Component pour inclure cette propriété
        else:
            # Mettre à jour le stock si le composant existe déjà
            self.components[name][color].stock += stock
            self.components[name][color].alert_threshold = alert_threshold
        
        return self.components[name][color]
    
    def update_component_stock(self, component_name, color, quantity):
        """Met à jour le stock d'un composant (ajout ou retrait)"""
        if component_name not in self.components or color not in self.components[component_name]:
            if quantity > 0:
                # Créer le composant s'il n'existe pas et que la quantité est positive
                return self.add_component(component_name, color, quantity)
            else:
                raise ValueError(f"Composant {component_name} de couleur {color} non trouvé")
        
        component = self.components[component_name][color]
        
        if quantity > 0:
            component.add_stock(quantity)
        else:
            component.remove_stock(abs(quantity))
        
        return component
    
    def update_assembled_product_stock(self, product_name, color, quantity):
        """Met à jour le stock d'un produit assemblé (ajout ou retrait)"""
        if product_name not in self.products:
            raise ValueError(f"Produit {product_name} non trouvé")
        
        product = self.products[product_name]
        
        if quantity > 0:
            product.add_assembled_product(color, quantity)
        else:
            product.remove_assembled_product(color, abs(quantity))
        
        return product
    
    def assemble_product(self, product_name, color, quantity=1, component_colors=None):
        """
        Assemble un produit à partir de ses composants
        
        Args:
            product_name (str): Nom du produit à assembler
            color (str): Couleur principale du produit
            quantity (int): Nombre de produits à assembler
            component_colors (dict, optional): Couleurs spécifiques pour certains composants
                                             {nom_composant: couleur}
        
        Returns:
            bool: True si l'assemblage a réussi, False sinon
        """
        if product_name not in self.products:
            raise ValueError(f"Produit {product_name} non trouvé")
        
        product = self.products[product_name]
        
        # Vérifier si suffisamment de composants sont disponibles
        for comp in product.components:
            component_name = comp["name"]
            comp_quantity = comp["quantity"] * quantity
            
            # Déterminer la couleur du composant selon les contraintes
            comp_color = product.get_component_color(component_name, color, component_colors)
            
            # Vérifier le stock
            if (component_name not in self.components or 
                comp_color not in self.components[component_name] or 
                self.components[component_name][comp_color].stock < comp_quantity):
                raise ValueError(f"Stock insuffisant pour le composant {component_name} en {comp_color}")
        
        # Tous les composants sont disponibles, procéder à l'assemblage
        try:
            # Retirer les composants de l'inventaire
            for comp in product.components:
                component_name = comp["name"]
                comp_quantity = comp["quantity"] * quantity
                
                # Déterminer la couleur du composant
                comp_color = product.get_component_color(component_name, color, component_colors)
                
                # Retirer du stock
                self.update_component_stock(component_name, comp_color, -comp_quantity)
            
            # Ajouter le produit assemblé à l'inventaire
            self.update_assembled_product_stock(product_name, color, quantity)
            
            return True
            
        except Exception as e:
            # En cas d'erreur, annuler l'opération
            # Note: Dans une vraie application, il faudrait implémenter un système de transactions
            raise ValueError(f"Erreur lors de l'assemblage: {str(e)}")
    
    def get_available_stock(self, include_components=True, include_products=True):
        """
        Récupère tout le stock disponible
        
        Returns:
            dict: Dictionnaire contenant le stock des composants et produits
        """
        result = {"components": {}, "products": {}}
        
        if include_components:
            for comp_name, colors in self.components.items():
                result["components"][comp_name] = {}
                for color, component in colors.items():
                    result["components"][comp_name][color] = component.stock
        
        if include_products:
            for product_name, product in self.products.items():
                result["products"][product_name] = product.assembled_items.copy()
        
        return result
    
    def get_assemblable_products(self):
        """
        Calcule le nombre de produits assemblables avec le stock actuel
        
        Returns:
            dict: {nom_produit: {couleur: quantité_assemblable}}
        """
        assemblable = {}
        
        # Convertir l'inventaire des composants au format attendu par get_assemblable_count
        component_inventory = {}
        for comp_name, colors in self.components.items():
            component_inventory[comp_name] = {}
            for color, component in colors.items():
                component_inventory[comp_name][color] = component.stock
        
        for product_name, product in self.products.items():
            assemblable[product_name] = {}
            
            # Pour chaque produit, calculer le nombre assemblable par couleur
            for color in self.get_available_colors():
                count = product.get_assemblable_count(component_inventory, color)
                if count > 0:
                    assemblable[product_name][color] = count
            
            # Ajouter l'option "Aléatoire" si disponible
            random_count = product.get_assemblable_count(component_inventory)
            if random_count > 0:
                assemblable[product_name]["Aléatoire"] = random_count
        
        return assemblable
    
    def get_low_stock_items(self):
        """
        Récupère la liste des composants en rupture de stock ou sous le seuil d'alerte
        
        Returns:
            list: Liste des composants avec stock faible
        """
        low_stock = []
        
        for comp_name, colors in self.components.items():
            for color, component in colors.items():
                if component.is_low_stock():
                    low_stock.append({
                        "type": "component",
                        "name": comp_name,
                        "color": color,
                        "stock": component.stock,
                        "threshold": component.alert_threshold
                    })
        
        return low_stock
    
    def get_available_colors(self):
        """
        Récupère la liste de toutes les couleurs disponibles dans l'inventaire
        
        Returns:
            list: Liste des couleurs uniques
        """
        colors = set()
        
        for comp_colors in self.components.values():
            for color in comp_colors.keys():
                colors.add(color)
        
        return sorted(list(colors))
    
    def add_color_variant(self, base_color, variant_name, hex_code):
        """Ajoute une variante de couleur"""
        self.color_variants[variant_name] = ColorVariant(base_color, variant_name, hex_code)
        return self.color_variants[variant_name]
    
    def get_color_hex(self, color_name):
        """Récupère le code hexadécimal d'une couleur"""
        if color_name in self.color_variants:
            return self.color_variants[color_name].hex_code
        
        # Couleurs par défaut pour les couleurs de base
        default_colors = {
            "Bleu": "#00448f",
            "Sky Blue": "#00eaf7",
            "Sakura Pink": "#ff86dc",
            "Blanc": "#ffffff",
            "Noir": "#000000",
            "Orange": "#ff7f00",
            "Gris": "#808080",
            "Lavande": "#ba6eff",
            "Satin couleur Or": "#d49a06",
            "Satin couleur Or/Noir": "#d3b300",
            "Satin couleur Noir/Violet": "#6b5087",
            "Aléatoire": "#d9f1fa"
        }
        
        return default_colors.get(color_name, "#d9f1fa")  # Gris par défaut