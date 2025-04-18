"""
Contrôleur pour la gestion de l'inventaire Plasmik3D.
Implémente les fonctionnalités pour gérer les composants, produits et assemblages.
"""

from models.database import Database
from models.inventory import InventoryManager, Product, Component, ColorVariant
from config import DATABASE_PATH, PRODUCTS, COLORS

class InventoryController:
    """Contrôleur pour la gestion de l'inventaire"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        self.inventory = InventoryManager()
        
        # Charger les données depuis la base de données
        self.initialize_inventory()
    
    def initialize_inventory(self):
        """Initialise l'inventaire avec les données de la base de données"""
        # Vérifier si les tables nécessaires existent
        self._ensure_tables_exist()
        
        # Charger les composants
        self._load_components()
        
        # Charger les produits et leurs définitions
        self._load_products()
        
        # Charger les variantes de couleurs
        self._load_color_variants()
    
    def _ensure_tables_exist(self):
        """S'assure que toutes les tables nécessaires existent dans la base de données"""
        # Vérifier et créer la table des composants
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                stock INTEGER DEFAULT 0,
                alert_threshold INTEGER DEFAULT 3,
                description TEXT DEFAULT '',
                UNIQUE(name, color)
            )
        """)
        
        # Vérifier et créer la table des produits
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        """)
        
        # Vérifier et créer la table des définitions de produits (composants requis)
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                component_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                color_constraint TEXT,
                UNIQUE(product_name, component_name)
            )
        """)
        
        # Vérifier et créer la table des produits assemblés
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assembled_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                color TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                UNIQUE(product_name, color)
            )
        """)
        
        # Vérifier et créer la table des variantes de couleurs
        self.db.cursor.execute("""
            CREATE TABLE IF NOT EXISTS color_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_color TEXT NOT NULL,
                variant_name TEXT NOT NULL,
                hex_code TEXT NOT NULL,
                UNIQUE(variant_name)
            )
        """)
        
        # Mettre à jour le schéma si nécessaire pour ajouter des colonnes manquantes
        try:
            # Vérifier si la colonne description existe dans la table components
            self.db.cursor.execute("PRAGMA table_info(components)")
            columns = [column[1] for column in self.db.cursor.fetchall()]
            
            # Ajouter la colonne description si elle n'existe pas
            if 'description' not in columns:
                self.db.cursor.execute("ALTER TABLE components ADD COLUMN description TEXT DEFAULT ''")
                print("Colonne 'description' ajoutée à la table 'components'")
            
            # Vérifier si la colonne color_constraint existe dans la table product_components
            self.db.cursor.execute("PRAGMA table_info(product_components)")
            pc_columns = [column[1] for column in self.db.cursor.fetchall()]
            
            # Ajouter la colonne color_constraint si elle n'existe pas
            if 'color_constraint' not in pc_columns:
                self.db.cursor.execute("ALTER TABLE product_components ADD COLUMN color_constraint TEXT")
                print("Colonne 'color_constraint' ajoutée à la table 'product_components'")
                
        except Exception as e:
            print(f"Erreur lors de la mise à jour du schéma de la base de données: {e}")
        
        self.db.conn.commit()
    
    def _load_components(self):
        """Charge les composants depuis la base de données"""
        self.db.cursor.execute("""
            SELECT name, color, stock, alert_threshold FROM components
        """)
        
        for row in self.db.cursor.fetchall():
            self.inventory.add_component(
                row['name'],
                row['color'],
                row['stock'],
                row['alert_threshold']
            )
        
        # Si aucun composant n'existe, initialiser avec des composants par défaut
        if not self.inventory.components:
            self._initialize_default_components()
    
    def _initialize_default_components(self):
        """Initialise des composants par défaut pour les produits courants"""
        # Liste des composants communs pour les fidget toys
        default_components = []
        
        # Créer chaque composant dans chaque couleur disponible
        for component in default_components:
            for color in [c for c in COLORS if c != "Aléatoire"]:
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO components (name, color, stock, alert_threshold)
                    VALUES (?, ?, 0, 3)
                """, (component, color))
                
                # Ajouter au gestionnaire d'inventaire
                self.inventory.add_component(component, color, 0, 3)
        
        self.db.conn.commit()
    
    def _load_products(self):
        """Charge les produits et leurs définitions depuis la base de données"""
        # Charger les produits
        self.db.cursor.execute("SELECT name, description FROM products")
        products_data = self.db.cursor.fetchall()
        
        # Si aucun produit n'existe, initialiser avec les produits par défaut
        if not products_data:
            self._initialize_default_products()
            # Recharger les produits après initialisation
            self.db.cursor.execute("SELECT name, description FROM products")
            products_data = self.db.cursor.fetchall()
        
        # Créer les objets de produit
        for row in products_data:
            product = self.inventory.add_product(row['name'], row['description'])
            
            # Charger les composants du produit
            self.db.cursor.execute("""
                SELECT component_name, quantity, color_constraint
                FROM product_components
                WHERE product_name = ?
            """, (row['name'],))
            
            for comp_row in self.db.cursor.fetchall():
                product.add_component(
                    comp_row['component_name'],
                    comp_row['quantity'],
                    comp_row['color_constraint']
                )
            
            # Charger les produits assemblés
            self.db.cursor.execute("""
                SELECT color, quantity
                FROM assembled_products
                WHERE product_name = ?
            """, (row['name'],))
            
            for assembled_row in self.db.cursor.fetchall():
                product.add_assembled_product(
                    assembled_row['color'],
                    assembled_row['quantity']
                )
    
    def _initialize_default_products(self):
        """Initialise des produits par défaut avec leurs composants"""
        # Définitions des produits de base
        default_products = []
        
        # Créer chaque produit
        for product_def in default_products:
            # Insérer le produit
            self.db.cursor.execute("""
                INSERT OR IGNORE INTO products (name, description)
                VALUES (?, ?)
            """, (product_def["name"], product_def["description"]))
            
            # Créer l'objet produit
            product = self.inventory.add_product(
                product_def["name"],
                product_def["description"]
            )
            
            # Ajouter les composants
            for comp in product_def["components"]:
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO product_components 
                    (product_name, component_name, quantity, color_constraint)
                    VALUES (?, ?, ?, ?)
                """, (
                    product_def["name"],
                    comp["name"],
                    comp["quantity"],
                    comp["color_constraint"]
                ))
                
                # Ajouter au produit en mémoire
                product.add_component(
                    comp["name"],
                    comp["quantity"],
                    comp["color_constraint"]
                )
        
        self.db.conn.commit()
    
    def _load_color_variants(self):
        """Charge les variantes de couleurs depuis la base de données"""
        self.db.cursor.execute("""
            SELECT base_color, variant_name, hex_code FROM color_variants
        """)
        
        for row in self.db.cursor.fetchall():
            self.inventory.add_color_variant(
                row['base_color'],
                row['variant_name'],
                row['hex_code']
            )
        
        # Si aucune variante n'existe, initialiser avec des variantes par défaut
        if not self.inventory.color_variants:
            self._initialize_default_color_variants()
    
    def _initialize_default_color_variants(self):
        """Initialise des variantes de couleurs par défaut"""
        default_variants = {
            "Rouge": [
                {"name": "Rouge Foncé", "hex_code": "#8B0000"},
                {"name": "Rouge Vif", "hex_code": "#FF0000"},
                {"name": "Rouge Bordeaux", "hex_code": "#800020"}
            ],
            "Bleu": [
                {"name": "Bleu Ciel", "hex_code": "#87CEEB"},
                {"name": "Bleu Marine", "hex_code": "#000080"},
                {"name": "Bleu Turquoise", "hex_code": "#40E0D0"}
            ],
            "Vert": [
                {"name": "Vert Forêt", "hex_code": "#228B22"},
                {"name": "Vert Menthe", "hex_code": "#98FB98"},
                {"name": "Vert Olive", "hex_code": "#808000"}
            ]
        }
        
        for base_color, variants in default_variants.items():
            for variant in variants:
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO color_variants 
                    (base_color, variant_name, hex_code)
                    VALUES (?, ?, ?)
                """, (base_color, variant["name"], variant["hex_code"]))
                
                # Ajouter à l'inventaire en mémoire
                self.inventory.add_color_variant(
                    base_color,
                    variant["name"],
                    variant["hex_code"]
                )
        
        self.db.conn.commit()
    
    #
    # Méthodes publiques pour la gestion des composants
    #
    
    def get_all_components(self):
        """
        Récupère tous les composants disponibles
        
        Returns:
            list: Liste des composants avec leur stock
        """
        components_list = []
        
        for comp_name, colors in self.inventory.components.items():
            for color, component in colors.items():
                components_list.append({
                    'name': comp_name,
                    'color': color,
                    'stock': component.stock,
                    'alert_threshold': component.alert_threshold
                })
        
        return components_list
    
    def get_component_stock(self, component_name, color):
        """
        Récupère le stock d'un composant spécifique
        
        Args:
            component_name (str): Nom du composant
            color (str): Couleur du composant
            
        Returns:
            int: Quantité en stock (0 si le composant n'existe pas)
        """
        if (component_name in self.inventory.components and 
            color in self.inventory.components[component_name]):
            return self.inventory.components[component_name][color].stock
        return 0
    
    def update_component_stock(self, component_name, color, quantity_change):
        """
        Met à jour le stock d'un composant (ajoute ou retire)
        
        Args:
            component_name (str): Nom du composant
            color (str): Couleur du composant
            quantity_change (int): Quantité à ajouter (positif) ou retirer (négatif)
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Mettre à jour en mémoire
            component = self.inventory.update_component_stock(
                component_name, color, quantity_change
            )
            
            # Mettre à jour dans la base de données
            if quantity_change > 0:
                # Si quantité positive, créer ou mettre à jour
                self.db.cursor.execute("""
                    INSERT INTO components (name, color, stock, alert_threshold)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(name, color) DO UPDATE SET
                    stock = stock + ?
                """, (component_name, color, quantity_change, component.alert_threshold, quantity_change))
            else:
                # Si quantité négative, s'assurer que le composant existe
                self.db.cursor.execute("""
                    UPDATE components
                    SET stock = MAX(0, stock + ?)
                    WHERE name = ? AND color = ?
                """, (quantity_change, component_name, color))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour du stock du composant: {e}")
            return False
    
    def set_component_alert_threshold(self, component_name, color, threshold):
        """
        Définit le seuil d'alerte pour un composant
        
        Args:
            component_name (str): Nom du composant
            color (str): Couleur du composant
            threshold (int): Nouveau seuil d'alerte
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Vérifier si le composant existe
            if (component_name not in self.inventory.components or 
                color not in self.inventory.components[component_name]):
                # Créer le composant s'il n'existe pas
                self.inventory.add_component(component_name, color, 0, threshold)
                
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO components (name, color, stock, alert_threshold)
                    VALUES (?, ?, 0, ?)
                """, (component_name, color, threshold))
            else:
                # Mettre à jour en mémoire
                self.inventory.components[component_name][color].alert_threshold = threshold
                
                # Mettre à jour dans la base de données
                self.db.cursor.execute("""
                    UPDATE components
                    SET alert_threshold = ?
                    WHERE name = ? AND color = ?
                """, (threshold, component_name, color))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour du seuil d'alerte: {e}")
            return False
    
    def add_new_component(self, component_name, initial_stock=None, description=""):
        """
        Ajoute un nouveau type de composant (dans toutes les couleurs)
        
        Args:
            component_name (str): Nom du nouveau composant
            initial_stock (dict, optional): Stock initial par couleur {couleur: quantité}
            description (str, optional): Description du composant
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            if initial_stock is None:
                initial_stock = {}
            
            # Ajouter le composant dans chaque couleur disponible
            for color in [c for c in COLORS if c != "Aléatoire"]:
                stock = initial_stock.get(color, 0)
                
                # Ajouter en mémoire - passer la description comme argument
                self.inventory.add_component(component_name, color, stock, 3, description)
                
                # Ajouter dans la base de données - Modifier pour inclure la description
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO components (name, color, stock, alert_threshold, description)
                    VALUES (?, ?, ?, 3, ?)
                """, (component_name, color, stock, description))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout du nouveau composant: {e}")
            return False
    
    def delete_component(self, component_name, color=None):
        """
        Supprime un composant de l'inventaire
        
        Args:
            component_name (str): Nom du composant à supprimer
            color (str, optional): Couleur spécifique à supprimer, ou None pour supprimer toutes les couleurs
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            if color:
                # Supprimer une couleur spécifique
                if (component_name in self.inventory.components and 
                    color in self.inventory.components[component_name]):
                    del self.inventory.components[component_name][color]
                    
                    # Si c'était la dernière couleur, supprimer le composant entier
                    if not self.inventory.components[component_name]:
                        del self.inventory.components[component_name]
                
                # Supprimer de la base de données
                self.db.cursor.execute("""
                    DELETE FROM components
                    WHERE name = ? AND color = ?
                """, (component_name, color))
            else:
                # Supprimer toutes les couleurs du composant
                if component_name in self.inventory.components:
                    del self.inventory.components[component_name]
                
                # Supprimer de la base de données
                self.db.cursor.execute("""
                    DELETE FROM components
                    WHERE name = ?
                """, (component_name,))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression du composant: {e}")
            return False
    
    def get_low_stock_components(self, threshold_override=None):
        """
        Récupère les composants dont le stock est inférieur au seuil d'alerte
        
        Args:
            threshold_override (int, optional): Seuil personnalisé à utiliser à la place du seuil stocké
            
        Returns:
            list: Liste des composants en stock bas
        """
        low_stock = []
        
        for comp_name, colors in self.inventory.components.items():
            for color, component in colors.items():
                threshold = threshold_override if threshold_override is not None else component.alert_threshold
                
                if component.stock < threshold:
                    low_stock.append({
                        'name': comp_name,
                        'color': color,
                        'stock': component.stock,
                        'alert_threshold': component.alert_threshold
                    })
        
        return low_stock
    
    #
    # Méthodes publiques pour la gestion des produits
    #
    
    def get_all_products(self):
        """
        Récupère tous les produits avec leurs définitions et stocks assemblés
        
        Returns:
            list: Liste des produits avec leurs détails
        """
        products_list = []
        
        for product_name, product in self.inventory.products.items():
            # Préparation des données des composants
            components = []
            for comp in product.components:
                component_data = {
                    'name': comp['name'],
                    'quantity': comp['quantity']
                }
                
                # Ajouter la contrainte de couleur si elle existe
                if comp['name'] in product.color_constraints:
                    component_data['color_constraint'] = product.color_constraints[comp['name']]
                
                components.append(component_data)
            
            # Création de l'objet produit à retourner
            product_data = {
                'name': product_name,
                'description': product.description,
                'components': components,
                'assembled_stock': product.assembled_items.copy()
            }
            
            products_list.append(product_data)
        
        return products_list
    
    def get_product_details(self, product_name):
        """
        Récupère les détails d'un produit spécifique
        
        Args:
            product_name (str): Nom du produit
            
        Returns:
            dict: Détails du produit, ou None si le produit n'existe pas
        """
        if product_name not in self.inventory.products:
            return None
        
        product = self.inventory.products[product_name]
        
        # Préparation des données des composants
        components = []
        for comp in product.components:
            component_data = {
                'name': comp['name'],
                'quantity': comp['quantity']
            }
            
            # Ajouter la contrainte de couleur si elle existe
            if comp['name'] in product.color_constraints:
                component_data['color_constraint'] = product.color_constraints[comp['name']]
            
            components.append(component_data)
        
        # Création de l'objet produit à retourner
        product_data = {
            'name': product_name,
            'description': product.description,
            'components': components,
            'assembled_stock': product.assembled_items.copy(),
            'total_assembled': product.get_total_assembled()
        }
        
        return product_data
    
    def get_assembled_product_stock(self, product_name, color=None):
        """
        Récupère le stock d'un produit assemblé
        
        Args:
            product_name (str): Nom du produit
            color (str, optional): Couleur spécifique, ou None pour tous
            
        Returns:
            int ou dict: Quantité en stock pour la couleur spécifiée, ou dictionnaire {couleur: quantité}
        """
        if product_name not in self.inventory.products:
            return 0 if color else {}
        
        product = self.inventory.products[product_name]
        
        if color:
            return product.assembled_items.get(color, 0)
        else:
            return product.assembled_items.copy()
    
    def update_assembled_product_stock(self, product_name, color, quantity_change):
        """
        Met à jour le stock d'un produit assemblé (ajoute ou retire)
        
        Args:
            product_name (str): Nom du produit
            color (str): Couleur du produit
            quantity_change (int): Quantité à ajouter (positif) ou retirer (négatif)
            
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            if product_name not in self.inventory.products:
                return False
            
            product = self.inventory.products[product_name]
            
            if quantity_change > 0:
                # Ajouter au stock
                product.add_assembled_product(color, quantity_change)
                
                # Mettre à jour la base de données
                self.db.cursor.execute("""
                    INSERT INTO assembled_products (product_name, color, quantity)
                    VALUES (?, ?, ?)
                    ON CONFLICT(product_name, color) DO UPDATE SET
                    quantity = quantity + ?
                """, (product_name, color, quantity_change, quantity_change))
            else:
                # Retirer du stock
                try:
                    product.remove_assembled_product(color, abs(quantity_change))
                    
                    # Mettre à jour la base de données
                    self.db.cursor.execute("""
                        UPDATE assembled_products
                        SET quantity = MAX(0, quantity + ?)
                        WHERE product_name = ? AND color = ?
                    """, (quantity_change, product_name, color))
                    
                    # Si le stock atteint zéro, supprimer l'entrée
                    self.db.cursor.execute("""
                        DELETE FROM assembled_products
                        WHERE product_name = ? AND color = ? AND quantity <= 0
                    """, (product_name, color))
                    
                except ValueError as e:
                    # Gérer le cas où le stock est insuffisant
                    print(f"Erreur: {e}")
                    return False
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour du stock du produit assemblé: {e}")
            return False
    
    def add_product(self, product_name, description=""):
        """
        Ajoute un nouveau produit au catalogue avec diagnostic renforcé
        
        Args:
            product_name (str): Nom du produit
            description (str, optional): Description du produit
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            print(f"--- Début de add_product pour '{product_name}' ---")
            
            # Vérifier la connexion à la base de données
            if self.db is None:
                print("Erreur: db est None")
                return False
            
            if self.db.conn is None:
                print("Erreur: db.conn est None")
                return False
            
            if self.db.cursor is None:
                print("Erreur: db.cursor est None")
                return False
            
            # Vérifier si le produit existe déjà
            print(f"Vérification si le produit '{product_name}' existe dans l'inventaire...")
            if product_name in self.inventory.products:
                print(f"Produit '{product_name}' déjà existant dans l'inventaire")
                return True
            
            # Vérifier si le produit existe déjà dans la base de données
            print(f"Vérification si le produit '{product_name}' existe dans la base de données...")
            self.db.cursor.execute("SELECT COUNT(*) FROM products WHERE name = ?", (product_name,))
            count = self.db.cursor.fetchone()[0]
            if count > 0:
                print(f"Produit '{product_name}' déjà existant dans la base de données")
                # Charger en mémoire si pas déjà fait
                self.inventory.add_product(product_name, description)
                return True
            
            # Ajouter en mémoire
            print(f"Ajout du produit '{product_name}' en mémoire...")
            try:
                self.inventory.add_product(product_name, description)
                print("Produit ajouté en mémoire avec succès")
            except Exception as mem_err:
                print(f"Erreur lors de l'ajout en mémoire: {mem_err}")
                raise
            
            # Ajouter dans la base de données
            print(f"Ajout du produit '{product_name}' dans la base de données...")
            try:
                self.db.cursor.execute("""
                    INSERT INTO products (name, description)
                    VALUES (?, ?)
                """, (product_name, description))
                print("Requête SQL exécutée avec succès")
            except Exception as sql_err:
                print(f"Erreur SQL: {sql_err}")
                raise
            
            # Commit des changements
            print("Commit des changements...")
            self.db.conn.commit()
            print(f"--- Fin de add_product pour '{product_name}': SUCCÈS ---")
            return True
            
        except Exception as e:
            print(f"Erreur détaillée lors de l'ajout du produit '{product_name}': {repr(e)}")
            print(f"Type d'erreur: {type(e).__name__}")
            
            # En cas d'erreur, faire un rollback
            try:
                if hasattr(self.db, 'conn') and self.db.conn:
                    self.db.conn.rollback()
                    print("Rollback effectué avec succès")
            except Exception as rollback_err:
                print(f"Erreur lors du rollback: {rollback_err}")
            
            print(f"--- Fin de add_product pour '{product_name}': ÉCHEC ---")
            return False
        
        
    def add_component_to_product(self, product_name, component_name, quantity=1, color_constraint=None):
        """
        Ajoute un composant à un produit
        
        Args:
            product_name (str): Nom du produit
            component_name (str): Nom du composant
            quantity (int): Nombre d'unités nécessaires
            color_constraint (str, optional): Contrainte de couleur
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            if product_name not in self.inventory.products:
                return False
            
            product = self.inventory.products[product_name]
            
            # Ajouter en mémoire
            product.add_component(component_name, quantity, color_constraint)
            
            # Ajouter dans la base de données
            self.db.cursor.execute("""
                INSERT INTO product_components 
                (product_name, component_name, quantity, color_constraint)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(product_name, component_name) DO UPDATE SET
                quantity = ?, color_constraint = ?
            """, (
                product_name, component_name, quantity, color_constraint,
                quantity, color_constraint
            ))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout du composant au produit: {e}")
            return False
    
    def remove_component_from_product(self, product_name, component_name):
        """
        Retire un composant d'un produit
        
        Args:
            product_name (str): Nom du produit
            component_name (str): Nom du composant
            
        Returns:
            bool: True si le retrait a réussi, False sinon
        """
        try:
            if product_name not in self.inventory.products:
                return False
            
            product = self.inventory.products[product_name]
            
            # Retirer en mémoire
            product.components = [c for c in product.components if c["name"] != component_name]
            
            # Retirer toute contrainte de couleur associée
            if component_name in product.color_constraints:
                del product.color_constraints[component_name]
            
            # Retirer de la base de données
            self.db.cursor.execute("""
                DELETE FROM product_components
                WHERE product_name = ? AND component_name = ?
            """, (product_name, component_name))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors du retrait du composant du produit: {e}")
            return False
    
    def delete_product(self, product_name):
        """
        Supprime un produit du catalogue
        
        Args:
            product_name (str): Nom du produit
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            if product_name not in self.inventory.products:
                return False
            
            # Supprimer en mémoire
            del self.inventory.products[product_name]
            
            # Supprimer de la base de données
            self.db.cursor.execute("""
                DELETE FROM products WHERE name = ?
            """, (product_name,))
            
            self.db.cursor.execute("""
                DELETE FROM product_components WHERE product_name = ?
            """, (product_name,))
            
            self.db.cursor.execute("""
                DELETE FROM assembled_products WHERE product_name = ?
            """, (product_name,))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression du produit: {e}")
            return False
    
    #
    # Méthodes publiques pour l'assemblage
    #
    
    def get_assemblable_products(self):
        """
        Récupère la liste des produits assemblables avec les stocks actuels
        
        Returns:
            dict: {nom_produit: {couleur: quantité_assemblable}}
        """
        return self.inventory.get_assemblable_products()
    
    def assemble_product(self, product_name, color, quantity=1, component_colors=None, auto_assign=False, order_id=None):
        """
        Assemble un produit à partir de ses composants
        
        Args:
            product_name (str): Nom du produit à assembler
            color (str): Couleur principale du produit
            quantity (int): Nombre de produits à assembler
            component_colors (dict, optional): Couleurs spécifiques pour certains composants
                                            {nom_composant: couleur}
            auto_assign (bool): Si True, attribue automatiquement à une commande
            order_id (str): ID de la commande pour attribution automatique
            
        Returns:
            tuple: (bool, str) - (succès, message)
        """
        try:
            # Vérifier si le produit peut être assemblé
            assemblable = self.get_assemblable_products()
            if (product_name not in assemblable or 
                (color != "Aléatoire" and color not in assemblable[product_name]) or
                (color != "Aléatoire" and assemblable[product_name][color] < quantity) or
                (color == "Aléatoire" and assemblable[product_name].get("Aléatoire", 0) < quantity)):
                
                return False, "Stock de composants insuffisant pour l'assemblage"
            
            # Si couleur aléatoire, choisir une couleur disponible
            actual_color = color
            if color == "Aléatoire":
                # Trouver les couleurs disponibles (sauf "Aléatoire")
                available_colors = [c for c in assemblable[product_name].keys() if c != "Aléatoire"]
                if available_colors:
                    # Choisir la première couleur disponible
                    actual_color = available_colors[0]
                else:
                    return False, "Aucune couleur disponible pour l'assemblage aléatoire"
            
            # Effectuer l'assemblage
            self.inventory.assemble_product(product_name, actual_color, quantity, component_colors)
            
            # Attribution automatique à une commande si demandé
            if auto_assign and order_id:
                from controllers.order_controller import OrderController
                order_controller = OrderController()
                
                # Mettre à jour le statut du produit dans la commande
                order_controller.update_item_status(order_id, product_name, actual_color, "Imprimé")
                
                # Si l'attribution automatique est réussie, ne pas ajouter au stock de produits assemblés
                return True, f"{quantity} {product_name} de couleur {actual_color} assemblé(s) et attribué(s) à la commande {order_id}"
            
            # Sinon, mettre à jour le stock de produits assemblés
            self.update_assembled_product_stock(product_name, actual_color, quantity)
            
            return True, f"{quantity} {product_name} de couleur {actual_color} assemblé(s) avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de l'assemblage: {str(e)}"
    #
    # Méthodes pour les variantes de couleurs
    #
    
    def get_color_variants(self, base_color=None):
        """
        Récupère les variantes de couleurs
        
        Args:
            base_color (str, optional): Filtrer par couleur de base
            
        Returns:
            list: Liste des variantes de couleurs
        """
        variants = []
        
        for variant_name, variant in self.inventory.color_variants.items():
            if base_color is None or variant.base_color == base_color:
                variants.append({
                    'base_color': variant.base_color,
                    'variant_name': variant.variant_name,
                    'hex_code': variant.hex_code
                })
        
        return variants
    
    def add_color_variant(self, base_color, variant_name, hex_code):
        """
        Ajoute une variante de couleur
        
        Args:
            base_color (str): Couleur de base
            variant_name (str): Nom de la variante
            hex_code (str): Code hexadécimal
            
        Returns:
            bool: True si l'ajout a réussi, False sinon
        """
        try:
            # Ajouter en mémoire
            self.inventory.add_color_variant(base_color, variant_name, hex_code)
            
            # Ajouter dans la base de données
            self.db.cursor.execute("""
                INSERT OR REPLACE INTO color_variants 
                (base_color, variant_name, hex_code)
                VALUES (?, ?, ?)
            """, (base_color, variant_name, hex_code))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de l'ajout de la variante de couleur: {e}")
            return False
    
    def delete_color_variant(self, variant_name):
        """
        Supprime une variante de couleur
        
        Args:
            variant_name (str): Nom de la variante
            
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            if variant_name not in self.inventory.color_variants:
                return False
            
            # Supprimer en mémoire
            del self.inventory.color_variants[variant_name]
            
            # Supprimer de la base de données
            self.db.cursor.execute("""
                DELETE FROM color_variants
                WHERE variant_name = ?
            """, (variant_name,))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erreur lors de la suppression de la variante de couleur: {e}")
            return False
    
    def get_available_colors(self):
        """
        Récupère la liste de toutes les couleurs disponibles dans l'inventaire
        
        Returns:
            list: Liste des couleurs uniques
        """
        return self.inventory.get_available_colors()
    
    def get_inventory_summary(self):
        """
        Récupère un résumé des statistiques d'inventaire
        
        Returns:
            dict: Dictionnaire avec les statistiques d'inventaire
        """
        # Récupérer tous les produits et composants
        products = self.get_all_products()
        components = self.get_all_components()
        
        # Calculer les statistiques
        total_products = 0
        total_assembled = 0
        for product in products:
            # Compter le nombre total de produits assemblés
            product_count = sum(product["assembled_stock"].values())
            total_assembled += product_count
            total_products += 1
        
        # Calculer les statistiques des composants
        total_components = 0
        total_component_types = len({comp["name"] for comp in components})
        total_component_stock = sum(comp["stock"] for comp in components)
        
        # Calculer le stock moyen par produit
        avg_stock = 0
        if total_products > 0:
            avg_stock = total_assembled / total_products
        
        return {
            "total_products": total_products,               # Nombre de types de produits
            "total_assembled": total_assembled,             # Nombre total de produits assemblés
            "total_component_types": total_component_types, # Nombre de types de composants
            "total_component_stock": total_component_stock, # Stock total de composants
            "avg_stock_per_product": round(avg_stock, 1)    # Stock moyen par produit
        }
    
    def get_low_stock_products(self):
        """
        Récupère la liste des composants en rupture de stock ou sous le seuil d'alerte
        
        Returns:
            list: Liste des composants avec stock faible
        """
        low_stock_components = self.get_low_stock_components()
        
        # Formater les données pour le tableau de bord
        formatted_stock = []
        for component in low_stock_components:
            formatted_stock.append({
                "product": component["name"],
                "color": component["color"],
                "stock": component["stock"],
                "alert_threshold": component["alert_threshold"]
            })
        
        return formatted_stock