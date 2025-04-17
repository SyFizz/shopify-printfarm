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
        
        # Table d'inventaire
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            color TEXT NOT NULL,
            stock INTEGER DEFAULT 0,
            alert_threshold INTEGER DEFAULT 3,
            UNIQUE(product, color)
        )
        ''')
        
        self.conn.commit()