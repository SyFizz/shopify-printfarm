from models.database import Database
from models.inventory import InventoryItem, ColorVariant, ProductComponent, InventoryForecast
from config import DATABASE_PATH, PRODUCTS, COLORS
import datetime

class InventoryController:
    """Contrôleur pour la gestion de l'inventaire"""
    
    def __init__(self):
        self.db = Database(DATABASE_PATH)
        # Migrer les données si nécessaire
        self.db.migrate_inventory_data()
        self.initialize_inventory()
    
    def initialize_inventory(self):
        """
        Initialise l'inventaire avec tous les produits et couleurs disponibles
        si ce n'est pas déjà fait
        """
        # Vérifier si l'inventaire est déjà initialisé
        self.db.cursor.execute("SELECT COUNT(*) as count FROM inventory")
        count = self.db.cursor.fetchone()['count']
        
        if count == 0:
            # Initialiser l'inventaire avec tous les produits et couleurs
            for product in PRODUCTS:
                for color in COLORS:
                    if color != "Aléatoire":  # Ne pas inclure "Aléatoire" dans l'inventaire
                        self.db.cursor.execute("""
                            INSERT INTO inventory (product, color, component, stock, alert_threshold)
                            VALUES (?, ?, NULL, 0, 3)
                        """, (product, color))
            
            # Ajouter les composants pour SpinRing
            components = ["Corps", "Rotor", "Disque"]
            for component in components:
                for color in COLORS:
                    if color != "Aléatoire":
                        self.db.cursor.execute("""
                            INSERT INTO inventory (product, color, component, stock, alert_threshold)
                            VALUES (?, ?, ?, 0, 5)
                        """, ('SpinRing', color, component))
                
                # Enregistrer la relation produit-composant
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO product_components (product_name, component_name, quantity)
                    VALUES (?, ?, 1)
                """, ('SpinRing', component))
            
            self.db.conn.commit()
            
            # Initialiser quelques variantes de couleurs pour l'exemple
            base_colors = {
                "Rouge": ["Rouge Foncé", "Rouge Vif", "Rouge Bordeaux"],
                "Bleu": ["Bleu Ciel", "Bleu Marine", "Bleu Turquoise"],
                "Vert": ["Vert Forêt", "Vert Menthe", "Vert Olive"]
            }
            
            hex_codes = {
                "Rouge Foncé": "#8B0000",
                "Rouge Vif": "#FF0000",
                "Rouge Bordeaux": "#800020",
                "Bleu Ciel": "#87CEEB",
                "Bleu Marine": "#000080",
                "Bleu Turquoise": "#40E0D0",
                "Vert Forêt": "#228B22",
                "Vert Menthe": "#98FB98",
                "Vert Olive": "#808000"
            }
            
            for base, variants in base_colors.items():
                for variant in variants:
                    self.db.cursor.execute("""
                        INSERT OR IGNORE INTO color_variants (base_color, variant_name, hex_code)
                        VALUES (?, ?, ?)
                    """, (base, variant, hex_codes[variant]))
            
            self.db.conn.commit()
    
    def get_inventory(self, include_components=True):
        """Récupère tout l'inventaire"""
        inventory = []
        
        query = """
            SELECT id, product, color, component, stock, alert_threshold
            FROM inventory
        """
        
        if not include_components:
            query += " WHERE component IS NULL"
        
        query += " ORDER BY product, component, color"
        
        self.db.cursor.execute(query)
        
        for row in self.db.cursor.fetchall():
            inventory.append({
                'id': row['id'],
                'product': row['product'],
                'color': row['color'],
                'component': row['component'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold']
            })
        
        return inventory
    
    def get_product_stock(self, product, color, component=None):
        """Récupère le stock d'un produit ou composant spécifique"""
        query = """
            SELECT stock
            FROM inventory
            WHERE product = ? AND color = ?
        """
        
        params = [product, color]
        
        if component is not None:
            query += " AND component = ?"
            params.append(component)
        else:
            query += " AND component IS NULL"
        
        self.db.cursor.execute(query, params)
        
        row = self.db.cursor.fetchone()
        return row['stock'] if row else 0
    
    def update_stock(self, product, color, new_stock, component=None):
        """Met à jour le stock d'un produit ou composant"""
        query = """
            UPDATE inventory
            SET stock = ?
            WHERE product = ? AND color = ?
        """
        
        params = [new_stock, product, color]
        
        if component is not None:
            query += " AND component = ?"
            params.append(component)
        else:
            query += " AND component IS NULL"
        
        self.db.cursor.execute(query, params)
        
        if self.db.cursor.rowcount == 0:
            # L'item n'existe pas encore, le créer
            self.db.cursor.execute("""
                INSERT INTO inventory (product, color, component, stock, alert_threshold)
                VALUES (?, ?, ?, ?, 3)
            """, (product, color, component, new_stock))
        
        self.db.conn.commit()
        return True
    
    def adjust_stock(self, product, color, adjustment, component=None):
        """
        Ajuste le stock d'un produit ou composant par une quantité donnée
        (positive pour ajouter, négative pour retirer)
        """
        current_stock = self.get_product_stock(product, color, component)
        new_stock = max(0, current_stock + adjustment)  # Éviter un stock négatif
        
        return self.update_stock(product, color, new_stock, component)
    
    def update_alert_threshold(self, product, color, threshold, component=None):
        """Met à jour le seuil d'alerte d'un produit ou composant"""
        query = """
            UPDATE inventory
            SET alert_threshold = ?
            WHERE product = ? AND color = ?
        """
        
        params = [threshold, product, color]
        
        if component is not None:
            query += " AND component = ?"
            params.append(component)
        else:
            query += " AND component IS NULL"
        
        self.db.cursor.execute(query, params)
        
        self.db.conn.commit()
        return True
    
    def get_low_stock_products(self, include_components=True):
        """Récupère les produits dont le stock est inférieur au seuil d'alerte"""
        low_stock = []
        
        query = """
            SELECT product, color, component, stock, alert_threshold
            FROM inventory
            WHERE stock < alert_threshold
        """
        
        if not include_components:
            query += " AND component IS NULL"
        
        query += " ORDER BY product, component, color"
        
        self.db.cursor.execute(query)
        
        for row in self.db.cursor.fetchall():
            low_stock.append({
                'product': row['product'],
                'color': row['color'],
                'component': row['component'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold']
            })
        
        return low_stock
    
    def calculate_needed_prints(self, include_components=True):
        """
        Calcule le nombre de pièces à imprimer pour chaque produit
        en fonction des commandes en attente et du stock
        """
        needed_prints = []
        
        # Récupérer tous les produits à imprimer (non décomposés en composants)
        self.db.cursor.execute("""
            SELECT oi.product, oi.color, SUM(oi.quantity) as needed
            FROM order_items oi
            WHERE oi.status = 'À imprimer'
            GROUP BY oi.product, oi.color
        """)
        
        products_to_print = []
        for row in self.db.cursor.fetchall():
            products_to_print.append({
                'product': row['product'],
                'color': row['color'],
                'quantity': row['needed']
            })
        
        # Pour chaque produit, vérifier s'il a des composants
        for product_item in products_to_print:
            product = product_item['product']
            color = product_item['color']
            quantity = product_item['quantity']
            
            # Vérifier si le produit a des composants
            self.db.cursor.execute("""
                SELECT COUNT(*) as count
                FROM product_components
                WHERE product_name = ?
            """, (product,))
            
            has_components = self.db.cursor.fetchone()['count'] > 0
            
            if has_components and include_components:
                # Récupérer les composants du produit
                self.db.cursor.execute("""
                    SELECT component_name, quantity
                    FROM product_components
                    WHERE product_name = ?
                """, (product,))
                
                components = []
                for comp_row in self.db.cursor.fetchall():
                    components.append({
                        'name': comp_row['component_name'],
                        'quantity': comp_row['quantity']
                    })
                
                # Pour chaque composant, vérifier le stock et ajouter à la liste si nécessaire
                for component in components:
                    component_name = component['name']
                    component_quantity = component['quantity']
                    
                    # Stock actuel du composant
                    stock = self.get_product_stock(product, color, component_name)
                    
                    # Nombre total de composants nécessaires
                    total_needed = quantity * component_quantity
                    
                    # Nombre à imprimer
                    to_print = max(0, total_needed - stock)
                    
                    if to_print > 0:
                        needed_prints.append({
                            'product': product,
                            'color': color,
                            'component': component_name,
                            'stock': stock,
                            'needed': total_needed,
                            'to_print': to_print
                        })
            else:
                # Pour les produits sans composants ou si on ne prend pas en compte les composants
                stock = self.get_product_stock(product, color)
                to_print = max(0, quantity - stock)
                
                if to_print > 0:
                    needed_prints.append({
                        'product': product,
                        'color': color,
                        'component': None,
                        'stock': stock,
                        'needed': quantity,
                        'to_print': to_print
                    })
        
        return needed_prints
    
    def get_product_to_print_count(self, product, color, component=None):
        """
        Récupère le nombre de produits à imprimer pour un produit et une couleur
        """
        self.db.cursor.execute("""
            SELECT SUM(quantity) as count
            FROM order_items
            WHERE product = ? AND color = ? AND status = 'À imprimer'
        """, (product, color))
        
        row = self.db.cursor.fetchone()
        total_needed = row["count"] if row and row["count"] else 0
        
        # Si c'est un composant, multiplier par la quantité nécessaire pour chaque produit
        if component:
            self.db.cursor.execute("""
                SELECT quantity
                FROM product_components
                WHERE product_name = ? AND component_name = ?
            """, (product, component))
            
            comp_row = self.db.cursor.fetchone()
            if comp_row:
                total_needed *= comp_row["quantity"]
        
        return total_needed

    def get_inventory_with_print_needs(self, include_components=True):
        """
        Récupère l'inventaire avec le nombre de produits à imprimer pour chaque item
        """
        inventory = []
        
        query = """
            SELECT id, product, color, component, stock, alert_threshold
            FROM inventory
        """
        
        if not include_components:
            query += " WHERE component IS NULL"
        
        query += " ORDER BY product, component, color"
        
        self.db.cursor.execute(query)
        
        for row in self.db.cursor.fetchall():
            product = row["product"]
            color = row["color"]
            component = row["component"]
            
            # Récupérer le nombre de produits à imprimer
            to_print = self.get_product_to_print_count(product, color, component)
            
            inventory.append({
                'id': row['id'],
                'product': row['product'],
                'color': row['color'],
                'component': row['component'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold'],
                'to_print': to_print,
                'status': 'OK' if row['stock'] >= row['alert_threshold'] else 'Low'
            })
        
        return inventory

    def adjust_inventory_after_printing(self, product, color, quantity, component=None):
        """
        Ajuste l'inventaire après une impression
        """
        return self.adjust_stock(product, color, quantity, component)

    def adjust_inventory_after_order(self, order_id):
        """
        Ajuste l'inventaire après l'envoi d'une commande
        """
        # Récupérer les produits de la commande
        self.db.cursor.execute("""
            SELECT product, color, quantity
            FROM order_items
            WHERE order_id = ?
        """, (order_id,))
        
        for row in self.db.cursor.fetchall():
            product = row["product"]
            color = row["color"]
            quantity = row["quantity"]
            
            # Vérifier si le produit a des composants
            self.db.cursor.execute("""
                SELECT COUNT(*) as count
                FROM product_components
                WHERE product_name = ?
            """, (product,))
            
            has_components = self.db.cursor.fetchone()['count'] > 0
            
            if has_components:
                # Récupérer les composants du produit
                self.db.cursor.execute("""
                    SELECT component_name, quantity as comp_quantity
                    FROM product_components
                    WHERE product_name = ?
                """, (product,))
                
                for comp_row in self.db.cursor.fetchall():
                    component = comp_row["component_name"]
                    comp_quantity = comp_row["comp_quantity"]
                    
                    # Ajuster le stock du composant
                    current_stock = self.get_product_stock(product, color, component)
                    new_stock = max(0, current_stock - quantity * comp_quantity)
                    self.update_stock(product, color, new_stock, component)
            else:
                # Pour les produits sans composants
                current_stock = self.get_product_stock(product, color)
                new_stock = max(0, current_stock - quantity)
                self.update_stock(product, color, new_stock)
        
        self.db.conn.commit()
        return True

    def get_inventory_summary(self, include_components=True):
        """
        Récupère un résumé de l'inventaire
        """
        summary = {
            "total_products": 0,
            "total_stock": 0,
            "low_stock_count": 0,
            "avg_stock_per_product": 0,
            "component_count": 0
        }
        
        # Nombre total de produits différents en stock
        query = """
            SELECT COUNT(*) as count
            FROM inventory
            WHERE stock > 0
        """
        
        if not include_components:
            query += " AND component IS NULL"
            
        self.db.cursor.execute(query)
        summary["total_products"] = self.db.cursor.fetchone()["count"]
        
        # Stock total
        query = """
            SELECT SUM(stock) as total
            FROM inventory
        """
        
        if not include_components:
            query += " WHERE component IS NULL"
            
        self.db.cursor.execute(query)
        summary["total_stock"] = self.db.cursor.fetchone()["total"] or 0
        
        # Nombre de produits en stock bas
        query = """
            SELECT COUNT(*) as count
            FROM inventory
            WHERE stock < alert_threshold
        """
        
        if not include_components:
            query += " AND component IS NULL"
            
        self.db.cursor.execute(query)
        summary["low_stock_count"] = self.db.cursor.fetchone()["count"]
        
        # Nombre de composants en stock
        self.db.cursor.execute("""
            SELECT COUNT(*) as count
            FROM inventory
            WHERE component IS NOT NULL AND stock > 0
        """)
        summary["component_count"] = self.db.cursor.fetchone()["count"]
        
        # Stock moyen par produit
        if summary["total_products"] > 0:
            summary["avg_stock_per_product"] = summary["total_stock"] / summary["total_products"]
        
        return summary
    
    #
    # Nouvelles méthodes pour la gestion des composants
    #
    
    def add_product_component(self, product_name, component_name, quantity=1):
        """
        Ajoute un composant à un produit
        """
        self.db.cursor.execute("""
            INSERT OR REPLACE INTO product_components (product_name, component_name, quantity)
            VALUES (?, ?, ?)
        """, (product_name, component_name, quantity))
        
        # S'assurer que l'inventaire existe pour ce composant dans toutes les couleurs
        for color in COLORS:
            if color != "Aléatoire":
                self.db.cursor.execute("""
                    INSERT OR IGNORE INTO inventory (product, color, component, stock, alert_threshold)
                    VALUES (?, ?, ?, 0, 3)
                """, (product_name, color, component_name))
        
        self.db.conn.commit()
        return True
    
    def remove_product_component(self, product_name, component_name):
        """
        Supprime un composant d'un produit
        """
        self.db.cursor.execute("""
            DELETE FROM product_components
            WHERE product_name = ? AND component_name = ?
        """, (product_name, component_name))
        
        self.db.conn.commit()
        return True
    
    def get_product_components(self, product_name):
        """
        Récupère tous les composants d'un produit
        """
        components = []
        
        self.db.cursor.execute("""
            SELECT component_name, quantity
            FROM product_components
            WHERE product_name = ?
        """, (product_name,))
        
        for row in self.db.cursor.fetchall():
            components.append({
                'name': row['component_name'],
                'quantity': row['quantity']
            })
        
        return components
    
    def is_product_with_components(self, product_name):
        """
        Vérifie si un produit a des composants
        """
        self.db.cursor.execute("""
            SELECT COUNT(*) as count
            FROM product_components
            WHERE product_name = ?
        """, (product_name,))
        
        return self.db.cursor.fetchone()['count'] > 0
    
    #
    # Nouvelles méthodes pour la gestion des variantes de couleurs
    #
    
    def add_color_variant(self, base_color, variant_name, hex_code):
        """
        Ajoute une variante de couleur
        """
        self.db.cursor.execute("""
            INSERT OR REPLACE INTO color_variants (base_color, variant_name, hex_code)
            VALUES (?, ?, ?)
        """, (base_color, variant_name, hex_code))
        
        self.db.conn.commit()
        return True
    
    def remove_color_variant(self, variant_name):
        """
        Supprime une variante de couleur
        """
        self.db.cursor.execute("""
            DELETE FROM color_variants
            WHERE variant_name = ?
        """, (variant_name,))
        
        self.db.conn.commit()
        return True
    
    def get_color_variants(self, base_color=None):
        """
        Récupère toutes les variantes de couleurs ou seulement celles d'une couleur de base
        """
        variants = []
        
        query = "SELECT base_color, variant_name, hex_code FROM color_variants"
        params = []
        
        if base_color:
            query += " WHERE base_color = ?"
            params.append(base_color)
        
        query += " ORDER BY base_color, variant_name"
        
        self.db.cursor.execute(query, params)
        
        for row in self.db.cursor.fetchall():
            variants.append({
                'base_color': row['base_color'],
                'variant_name': row['variant_name'],
                'hex_code': row['hex_code']
            })
        
        return variants
    
    def color_variant_exists(self, variant_name):
        """
        Vérifie si une variante de couleur existe
        """
        self.db.cursor.execute("""
            SELECT COUNT(*) as count
            FROM color_variants
            WHERE variant_name = ?
        """, (variant_name,))
        
        return self.db.cursor.fetchone()['count'] > 0
    
    #
    # Nouvelles méthodes pour les prévisions d'inventaire
    #
    
    def update_inventory_forecast(self):
        """
        Met à jour les prévisions d'inventaire en fonction des ventes
        """
        # Récupérer les données des 3 derniers mois pour l'analyse
        three_months_ago = datetime.datetime.now() - datetime.timedelta(days=90)
        date_limit = three_months_ago.strftime("%Y-%m-%d")
        
        # Calculer les ventes moyennes mensuelles par produit et couleur
        self.db.cursor.execute("""
            SELECT oi.product, oi.color, SUM(oi.quantity) / 3.0 as monthly_avg
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.date >= ?
            GROUP BY oi.product, oi.color
        """, (date_limit,))
        
        # Stocker les résultats temporaires
        monthly_sales = {}
        for row in self.db.cursor.fetchall():
            key = (row['product'], row['color'], None)  # Tuple (produit, couleur, composant)
            monthly_sales[key] = row['monthly_avg']
        
        # Pour les produits avec composants, répartir les ventes sur les composants
        for product, color, _ in list(monthly_sales.keys()):
            # Vérifier si le produit a des composants
            self.db.cursor.execute("""
                SELECT component_name, quantity
                FROM product_components
                WHERE product_name = ?
            """, (product,))
            
            components = self.db.cursor.fetchall()
            if components:
                monthly_avg = monthly_sales.get((product, color, None), 0)
                for comp in components:
                    comp_name = comp['component_name']
                    comp_quantity = comp['quantity']
                    key = (product, color, comp_name)
                    monthly_sales[key] = monthly_avg * comp_quantity
        
        # Calculer le stock recommandé et les facteurs de tendance
        # Pour chaque produit ou composant, mettre à jour les prévisions
        for (product, color, component), monthly_avg in monthly_sales.items():
            # Stock recommandé = ventes mensuelles moyennes * 1.5
            recommended_stock = int(monthly_avg * 1.5)
            
            # Vérifier si une entrée de prévision existe déjà
            self.db.cursor.execute("""
                SELECT id, avg_monthly_sales, recommended_stock, trend_factor
                FROM inventory_forecast
                WHERE product = ? AND color = ? AND (component = ? OR (component IS NULL AND ? IS NULL))
            """, (product, color, component, component))
            
            row = self.db.cursor.fetchone()
            
            if row:
                # Calculer le facteur de tendance
                old_avg = row['avg_monthly_sales']
                trend_factor = 1.0
                if old_avg > 0:
                    trend_factor = monthly_avg / old_avg
                    # Limiter les variations extrêmes
                    trend_factor = max(0.5, min(trend_factor, 2.0))
                
                # Mettre à jour l'entrée existante
                self.db.cursor.execute("""
                    UPDATE inventory_forecast
                    SET avg_monthly_sales = ?,
                        recommended_stock = ?,
                        trend_factor = ?
                    WHERE id = ?
                """, (monthly_avg, recommended_stock, trend_factor, row['id']))
            else:
                # Créer une nouvelle entrée
                self.db.cursor.execute("""
                    INSERT INTO inventory_forecast (
                        product, color, component, 
                        avg_monthly_sales, recommended_stock, trend_factor
                    ) VALUES (?, ?, ?, ?, ?, 1.0)
                """, (product, color, component, monthly_avg, recommended_stock))
        
        self.db.conn.commit()
        return True
    
    def get_inventory_forecast(self, product=None, color=None, component=None):
        """
        Récupère les prévisions d'inventaire filtrées par produit, couleur ou composant
        """
        forecasts = []
        
        query = """
            SELECT 
                product, color, component, 
                avg_monthly_sales, recommended_stock, trend_factor
            FROM inventory_forecast
        """
        
        conditions = []
        params = []
        
        if product:
            conditions.append("product = ?")
            params.append(product)
        
        if color:
            conditions.append("color = ?")
            params.append(color)
        
        if component is not None:  # Pour permettre component=None explicitement
            conditions.append("component = ?")
            params.append(component)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY product, component, color"
        
        self.db.cursor.execute(query, params)
        
        for row in self.db.cursor.fetchall():
            forecasts.append({
                'product': row['product'],
                'color': row['color'],
                'component': row['component'],
                'avg_monthly_sales': row['avg_monthly_sales'],
                'recommended_stock': row['recommended_stock'],
                'trend_factor': row['trend_factor'],
                'forecast_stock': int(row['recommended_stock'] * row['trend_factor'])
            })
        
        return forecasts
    
    def get_inventory_with_forecast(self):
        """
        Récupère l'inventaire avec les prévisions
        """
        inventory = []
        
        self.db.cursor.execute("""
            SELECT 
                i.id, i.product, i.color, i.component, i.stock, i.alert_threshold,
                ifnull(f.avg_monthly_sales, 0) as avg_monthly_sales,
                ifnull(f.recommended_stock, 0) as recommended_stock,
                ifnull(f.trend_factor, 1.0) as trend_factor
            FROM inventory i
            LEFT JOIN inventory_forecast f ON 
                i.product = f.product AND 
                i.color = f.color AND 
                (i.component = f.component OR (i.component IS NULL AND f.component IS NULL))
            ORDER BY i.product, i.component, i.color
        """)
        
        for row in self.db.cursor.fetchall():
            forecast_stock = int(row['recommended_stock'] * row['trend_factor'])
            stock_status = 'OK'
            
            if row['stock'] < row['alert_threshold']:
                stock_status = 'Low'
            
            if row['stock'] < forecast_stock:
                stock_status = 'Below Forecast'
            
            inventory.append({
                'id': row['id'],
                'product': row['product'],
                'color': row['color'],
                'component': row['component'],
                'stock': row['stock'],
                'alert_threshold': row['alert_threshold'],
                'avg_monthly_sales': row['avg_monthly_sales'],
                'recommended_stock': row['recommended_stock'],
                'forecast_stock': forecast_stock,
                'status': stock_status
            })
        
        return inventory