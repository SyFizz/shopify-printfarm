class Order:
    """Modèle de données pour une commande"""
    
    def __init__(self, order_id, date, client, email, status="En attente", priority="Moyenne", notes=""):
        self.id = order_id
        self.date = date
        self.client = client
        self.email = email
        self.status = status
        self.priority = priority
        self.notes = notes
        self.items = []  # Liste des produits commandés
    
    def add_item(self, product, color, quantity=1, status="À imprimer"):
        """Ajoute un produit à la commande"""
        item = {
            "product": product,
            "color": color,
            "quantity": quantity,
            "status": status
        }
        self.items.append(item)
    
    def get_total_items(self):
        """Retourne le nombre total d'articles dans la commande"""
        return sum(item["quantity"] for item in self.items)
    
    def get_total_unique_items(self):
        """Retourne le nombre de produits différents dans la commande"""
        return len(self.items)
    
    def is_complete(self):
        """Vérifie si tous les produits de la commande sont prêts"""
        return all(item["status"] == "Imprimé" for item in self.items)
    
    def is_in_progress(self):
        """Vérifie si la commande est en cours de traitement"""
        return any(item["status"] == "En impression" for item in self.items) and not self.is_complete()
    
    def update_status(self):
        """Met à jour le statut de la commande en fonction des produits"""
        if self.is_complete():
            self.status = "Prêt"
        elif self.is_in_progress():
            self.status = "En cours"
        else:
            self.status = "En attente"
        return self.status
    
    def get_progress_percentage(self):
        """Calcule le pourcentage d'avancement de la commande"""
        if not self.items:
            return 0
        
        total_items = sum(item["quantity"] for item in self.items)
        completed_items = sum(item["quantity"] for item in self.items if item["status"] == "Imprimé")
        
        return int((completed_items / total_items) * 100)
    
    def get_items_by_status(self, status):
        """Récupère les produits de la commande selon leur statut"""
        return [item for item in self.items if item["status"] == status]
    
    def __str__(self):
        return f"Commande {self.id} - {self.client} - {self.status}"