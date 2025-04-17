# views/orders_view.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
                           QTableWidgetItem, QPushButton, QComboBox, QLineEdit,
                           QHeaderView, QFrame, QMessageBox, QMenu)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor
from controllers.order_controller import OrderController
from controllers.workflow_controller import WorkflowController
from utils.helpers import format_date
from config import ORDER_STATUSES, PRIORITIES, UI_COLORS

class OrdersWidget(QWidget):
    """Widget pour la gestion des commandes"""
    
    def __init__(self, parent=None, filter_status=None):
        super().__init__(parent)
        self.order_controller = OrderController()
        self.workflow_controller = WorkflowController()
        self.filter_status = filter_status  # Pour filtrer par statut (en attente, en cours, etc.)
        
        self.setup_ui()
        self.load_orders()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre et filtres
        header_layout = QHBoxLayout()
        
        # Titre
        title = "Toutes les commandes"
        if self.filter_status == "pending":
            title = "Commandes en attente"
        elif self.filter_status == "in_progress":
            title = "Commandes en cours"
        elif self.filter_status == "ready":
            title = "Commandes prêtes"
        elif self.filter_status == "shipped":
            title = "Commandes expédiées"
            
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {UI_COLORS['primary']};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Barre de recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher une commande...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self.filter_orders)
        header_layout.addWidget(self.search_input)
        
        # Filtre de statut
        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts", "all")
        for status in ORDER_STATUSES:
            self.status_filter.addItem(status, status)
        
        # Pré-sélectionner le statut si un filtre est appliqué
        if self.filter_status == "pending":
            self.status_filter.setCurrentText("En attente")
        elif self.filter_status == "in_progress":
            self.status_filter.setCurrentText("En cours")
        elif self.filter_status == "ready":
            self.status_filter.setCurrentText("Prêt")
        elif self.filter_status == "shipped":
            self.status_filter.setCurrentText("Expédié")
            
        self.status_filter.currentIndexChanged.connect(self.filter_orders)
        header_layout.addWidget(self.status_filter)
        
        layout.addLayout(header_layout)
        
        # Tableau des commandes
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels([
            "ID", "Date", "Client", "Produits", "Statut", "Priorité", "Actions"
        ])
        
        # Configuration du tableau
        self.orders_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.orders_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Colonne Produits extensible
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.verticalHeader().setVisible(False)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #e0e0e0;
            }
            QTableWidget::item:selected {
                color: black;
            }
        """)
        
        layout.addWidget(self.orders_table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Actualiser")
        refresh_button.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_button.clicked.connect(self.load_orders)
        buttons_layout.addWidget(refresh_button)
        
        new_order_button = QPushButton("Nouvelle commande")
        new_order_button.setIcon(self.style().standardIcon(self.style().SP_FileIcon))
        new_order_button.clicked.connect(self.create_new_order)
        buttons_layout.addWidget(new_order_button)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
    
    def load_orders(self):
        """Charge les commandes depuis le contrôleur"""
        # Récupérer les commandes
        if self.filter_status == "pending":
            orders = self.order_controller.get_orders_by_status("En attente")
        elif self.filter_status == "in_progress":
            orders = self.order_controller.get_orders_by_status("En cours")
        elif self.filter_status == "ready":
            orders = self.order_controller.get_orders_by_status("Prêt")
        elif self.filter_status == "shipped":
            orders = self.order_controller.get_orders_by_status("Expédié")
        else:
            orders = self.order_controller.get_all_orders()
        
        # Remplir le tableau
        self.update_table(orders)
    
    def update_table(self, orders):
        """Met à jour le tableau avec les commandes"""
        # Vider le tableau
        self.orders_table.setRowCount(0)
        
        # Remplir avec les nouvelles données
        for row_idx, order in enumerate(orders):
            self.orders_table.insertRow(row_idx)
            
            # ID
            id_item = QTableWidgetItem(order.id)
            self.orders_table.setItem(row_idx, 0, id_item)
            
            # Date
            date_item = QTableWidgetItem(format_date(order.date))
            self.orders_table.setItem(row_idx, 1, date_item)
            
            # Client
            client_item = QTableWidgetItem(order.client)
            self.orders_table.setItem(row_idx, 2, client_item)
            
            # Produits
            products_text = ""
            for item in order.items:
                products_text += f"{item['product']} - {item['color']} (x{item['quantity']})\n"
            products_item = QTableWidgetItem(products_text.strip())
            self.orders_table.setItem(row_idx, 3, products_item)
            
            # Statut
            status_item = QTableWidgetItem(order.status)
            
            # Colorer selon le statut
            if order.status == "En attente":
                status_item.setBackground(QColor(255, 200, 200))  # Rouge clair
            elif order.status == "En cours":
                status_item.setBackground(QColor(255, 230, 180))  # Orange clair
            elif order.status == "Prêt":
                status_item.setBackground(QColor(200, 255, 200))  # Vert clair
            elif order.status == "Expédié":
                status_item.setBackground(QColor(220, 220, 255))  # Bleu clair
            
            self.orders_table.setItem(row_idx, 4, status_item)
            
            # Priorité
            priority_item = QTableWidgetItem(order.priority)
            self.orders_table.setItem(row_idx, 5, priority_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            # Bouton Voir détails
            view_button = QPushButton("")
            view_button.setIcon(self.style().standardIcon(self.style().SP_FileDialogDetailedView))
            view_button.setToolTip("Voir les détails")
            view_button.setFixedSize(28, 28)
            view_button.clicked.connect(lambda checked, o=order: self.view_order(o))
            actions_layout.addWidget(view_button)
            
            # Bouton Éditer
            edit_button = QPushButton("")
            edit_button.setIcon(self.style().standardIcon(self.style().SP_FileDialogContentsView))
            edit_button.setToolTip("Éditer la commande")
            edit_button.setFixedSize(28, 28)
            edit_button.clicked.connect(lambda checked, o=order: self.edit_order(o))
            actions_layout.addWidget(edit_button)
            
            # Bouton Changer statut
            status_button = QPushButton("")
            status_button.setIcon(self.style().standardIcon(self.style().SP_ArrowRight))
            status_button.setToolTip("Changer le statut")
            status_button.setFixedSize(28, 28)
            status_button.clicked.connect(lambda checked, o=order: self.show_status_menu(status_button, o))
            actions_layout.addWidget(status_button)
            
            self.orders_table.setCellWidget(row_idx, 6, actions_widget)
            
        # Ajuster les hauteurs de ligne pour les produits multiples
        for row in range(self.orders_table.rowCount()):
            self.orders_table.resizeRowToContents(row)
    
    def filter_orders(self):
        """Filtre les commandes selon la recherche et le statut"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter.currentData()
        
        # Récupérer toutes les commandes
        if self.filter_status and status_filter == "all":
            # Si on est dans un onglet filtré mais qu'on a choisi "Tous les statuts",
            # on respecte quand même le filtre de l'onglet
            if self.filter_status == "pending":
                orders = self.order_controller.get_orders_by_status("En attente")
            elif self.filter_status == "in_progress":
                orders = self.order_controller.get_orders_by_status("En cours")
            elif self.filter_status == "ready":
                orders = self.order_controller.get_orders_by_status("Prêt")
            elif self.filter_status == "shipped":
                orders = self.order_controller.get_orders_by_status("Expédié")
            else:
                orders = self.order_controller.get_all_orders()
        elif status_filter != "all":
            orders = self.order_controller.get_orders_by_status(status_filter)
        else:
            orders = self.order_controller.get_all_orders()
        
        # Filtrer par texte de recherche
        if search_text:
            filtered_orders = []
            for order in orders:
                if (search_text in order.id.lower() or 
                    search_text in order.client.lower() or 
                    search_text in order.email.lower()):
                    filtered_orders.append(order)
            orders = filtered_orders
        
        # Mettre à jour le tableau
        self.update_table(orders)
    
    def view_order(self, order):
        """Affiche les détails d'une commande"""
        # Pour le moment, affichons juste une boîte de dialogue
        details = f"Commande: {order.id}\n"
        details += f"Client: {order.client}\n"
        details += f"Email: {order.email}\n"
        details += f"Date: {format_date(order.date)}\n"
        details += f"Statut: {order.status}\n"
        details += f"Priorité: {order.priority}\n\n"
        details += "Produits:\n"
        
        for item in order.items:
            details += f"- {item['product']} - {item['color']} (x{item['quantity']}) [{item['status']}]\n"
        
        QMessageBox.information(self, "Détails de la commande", details)
    
    def edit_order(self, order):
        """Ouvre le formulaire d'édition d'une commande"""
        # Dans une version future, on pourrait ouvrir un formulaire d'édition complet
        QMessageBox.information(self, "Édition", f"Édition de la commande {order.id} (à implémenter)")
    
    def show_status_menu(self, button, order):
        """Affiche un menu pour changer le statut de la commande"""
        menu = QMenu(self)
        
        # Ajouter les statuts possibles
        for status in ORDER_STATUSES:
            if status != order.status:  # Ne pas inclure le statut actuel
                action = menu.addAction(status)
                action.triggered.connect(lambda checked, s=status: self.change_order_status(order, s))
        
        # Si la commande est prête, ajouter une action pour l'expédier
        if order.status == "Prêt":
            menu.addSeparator()
            ship_action = menu.addAction("Expédier")
            ship_action.triggered.connect(lambda: self.ship_order(order))
        
        # Afficher le menu sous le bouton
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))
    
    def change_order_status(self, order, new_status):
        """Change le statut d'une commande"""
        self.order_controller.update_order_status(order.id, new_status)
        self.load_orders()  # Recharger les commandes
    
    def ship_order(self, order):
        """Expédie une commande"""
        success, message = self.workflow_controller.ship_order(order.id)
        
        if success:
            QMessageBox.information(self, "Commande expédiée", message)
        else:
            QMessageBox.warning(self, "Erreur", message)
        
        self.load_orders()  # Recharger les commandes
    
    def create_new_order(self):
        """Crée une nouvelle commande"""
        # Dans une version future, on pourrait ouvrir un formulaire de création
        QMessageBox.information(self, "Nouvelle commande", "Création d'une nouvelle commande (à implémenter)")