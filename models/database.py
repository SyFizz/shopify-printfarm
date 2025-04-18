import sqlite3
import os

class Database:
    """Gestionnaire de la base de données SQLite"""
    
    def __init__(self, db_path):
        """Initialise la connexion à la base de données"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialiser la base de données
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Établit la connexion à la base de données"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        self.cursor = self.conn.cursor()
    
    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_tables(self):
        """Crée les tables de la base de données si elles n'existent pas"""
        # Table des commandes
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            client TEXT NOT NULL,
            email TEXT,
            status TEXT DEFAULT 'En attente',
            priority TEXT DEFAULT 'Moyenne',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table des produits commandés
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            product TEXT NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            status TEXT DEFAULT 'À imprimer',
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        ''')
        
        # Table d'inventaire mise à jour pour inclure les composants
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            color TEXT NOT NULL,
            component TEXT,
            stock INTEGER DEFAULT 0,
            alert_threshold INTEGER DEFAULT 3,
            UNIQUE(product, color, component)
        )
        ''')
        
        # Table des composants de produits
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            component_name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            UNIQUE(product_name, component_name)
        )
        ''')
        
        # Table des variantes de couleurs
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS color_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_color TEXT NOT NULL,
            variant_name TEXT NOT NULL,
            hex_code TEXT NOT NULL,
            UNIQUE(variant_name)
        )
        ''')
        
        # Table des prévisions d'inventaire
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_forecast (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            color TEXT NOT NULL,
            component TEXT,
            avg_monthly_sales REAL DEFAULT 0,
            recommended_stock INTEGER DEFAULT 0,
            trend_factor REAL DEFAULT 1.0,
            UNIQUE(product, color, component)
        )
        ''')
        
        self.conn.commit()
        
    def migrate_inventory_data(self):
        """Migration des données d'inventaire vers le nouveau schéma avec composants"""
        # Vérifier si la colonne component existe déjà dans la table inventory
        self.cursor.execute("PRAGMA table_info(inventory)")
        columns = self.cursor.fetchall()
        column_names = [column['name'] for column in columns]
        
        # Si la migration est déjà faite, ne rien faire
        if 'component' in column_names:
            return
            
        # Sauvegarde des données actuelles
        self.cursor.execute("SELECT * FROM inventory")
        old_inventory = self.cursor.fetchall()
        
        # Renommer l'ancienne table
        self.cursor.execute("ALTER TABLE inventory RENAME TO inventory_old")
        
        # Créer la nouvelle table
        self.cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            color TEXT NOT NULL,
            component TEXT,
            stock INTEGER DEFAULT 0,
            alert_threshold INTEGER DEFAULT 3,
            UNIQUE(product, color, component)
        )
        ''')
        
        # Migrer les données
        for item in old_inventory:
            self.cursor.execute('''
            INSERT INTO inventory (product, color, stock, alert_threshold)
            VALUES (?, ?, ?, ?)
            ''', (item['product'], item['color'], item['stock'], item['alert_threshold']))
        
        # Supprimer l'ancienne table
        self.cursor.execute("DROP TABLE inventory_old")
        
        self.conn.commit()