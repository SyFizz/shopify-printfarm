# views/print_plan_view.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QPushButton, QSizePolicy, QTableWidget,
                           QTableWidgetItem, QHeaderView, QComboBox, QCheckBox,
                           QMessageBox, QSpinBox, QStyle, QDialog, QFormLayout,
                           QDialogButtonBox, QAbstractItemView, QMenu, QTabWidget)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QColor, QIcon, QCursor
from controllers.print_controller import PrintController
from controllers.inventory_controller import InventoryController
from controllers.workflow_controller import WorkflowController
from controllers.order_controller import OrderController
from config import COLOR_HEX_MAP, UI_COLORS, COLORS

class StartPrintDialog(QDialog):
    """Dialogue pour démarrer une impression partielle"""
    
    def __init__(self, product, color, total_quantity, parent=None):
        super().__init__(parent)
        self.product = product
        self.color = color
        self.total_quantity = total_quantity
        self.quantity_to_print = total_quantity  # Par défaut, tout imprimer
        
        self.setWindowTitle(f"Démarrer l'impression de {product}")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations sur le produit
        info_layout = QHBoxLayout()
        
        # Indicateur de couleur
        color_indicator = QFrame()
        color_indicator.setFixedSize(24, 24)
        color_indicator.setStyleSheet(f"background-color: {COLOR_HEX_MAP.get(self.color, '#CCCCCC')}; border: 1px solid #999; border-radius: 4px;")
        info_layout.addWidget(color_indicator)
        
        # Nom du produit et couleur
        product_label = QLabel(f"<b>{self.product}</b> ({self.color})")
        product_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(product_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Formulaire
        form_layout = QFormLayout()
        
        # Quantité totale
        total_label = QLabel(f"{self.total_quantity}")
        total_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Quantité totale à imprimer:", total_label)
        
        # Quantité à imprimer dans ce lot
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(self.total_quantity)
        self.quantity_spin.setValue(self.total_quantity)
        self.quantity_spin.valueChanged.connect(self.update_remaining)
        form_layout.addRow("Quantité à imprimer maintenant:", self.quantity_spin)
        
        # Quantité restante
        self.remaining_label = QLabel("0")
        form_layout.addRow("Quantité restante pour plus tard:", self.remaining_label)
        
        layout.addLayout(form_layout)
        
        # Message d'information
        info_msg = QLabel("Vous pouvez choisir d'imprimer seulement une partie des produits maintenant et le reste plus tard.")
        info_msg.setWordWrap(True)
        info_msg.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_msg)
        
        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        # Mettre à jour l'affichage initial
        self.update_remaining()
    
    def update_remaining(self):
        """Met à jour l'affichage de la quantité restante"""
        remaining = self.total_quantity - self.quantity_spin.value()
        self.remaining_label.setText(str(remaining))
        
        # Colorer en rouge si beaucoup reste
        if remaining > self.total_quantity / 2:
            self.remaining_label.setStyleSheet("font-weight: bold; color: #C00;")
        else:
            self.remaining_label.setStyleSheet("font-weight: bold;")
    
    def get_quantity(self):
        """Retourne la quantité choisie pour l'impression"""
        return self.quantity_spin.value()


class CompletePrintDialog(QDialog):
    """Dialogue pour terminer une impression et choisir la commande à laquelle affecter les produits"""
    
    def __init__(self, product, color, quantity, parent=None):
        super().__init__(parent)
        self.product = product
        self.color = color
        self.quantity = quantity
        self.order_controller = OrderController()
        
        self.setWindowTitle(f"Terminer l'impression de {product}")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Informations sur le produit
        info_layout = QHBoxLayout()
        
        # Indicateur de couleur
        color_indicator = QFrame()
        color_indicator.setFixedSize(24, 24)
        color_indicator.setStyleSheet(f"background-color: {COLOR_HEX_MAP.get(self.color, '#CCCCCC')}; border: 1px solid #999; border-radius: 4px;")
        info_layout.addWidget(color_indicator)
        
        # Nom du produit et couleur
        product_label = QLabel(f"<b>{self.product}</b> en {self.color}")
        product_label.setStyleSheet("font-size: 14px;")
        info_layout.addWidget(product_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Message principal
        msg = QLabel(f"L'impression de {self.quantity} {self.product}(s) en {self.color} est terminée.")
        msg.setWordWrap(True)
        layout.addWidget(msg)
        
        # Trouver les commandes les plus anciennes qui attendent ce produit
        orders = self.get_oldest_orders()
        
        if orders:
            info = QLabel("Les commandes suivantes attendent ce produit (du plus ancien au plus récent) :")
            info.setWordWrap(True)
            layout.addWidget(info)
            
            # Liste des commandes
            orders_layout = QVBoxLayout()
            orders_layout.setSpacing(5)
            
            for order in orders:
                order_layout = QHBoxLayout()
                order_layout.setSpacing(10)
                
                # Indicateur de date
                date_label = QLabel(order["date"])
                date_label.setStyleSheet("color: #666;")
                order_layout.addWidget(date_label)
                
                # ID de commande
                order_id_label = QLabel(f"<b>Commande {order['id']}</b>")
                order_layout.addWidget(order_id_label)
                
                # Client
                client_label = QLabel(f"Client: {order['client']}")
                order_layout.addWidget(client_label)
                
                # Quantité requise
                qty_label = QLabel(f"Quantité: {order['quantity']}")
                qty_label.setStyleSheet("font-weight: bold;")
                order_layout.addWidget(qty_label)
                
                order_layout.addStretch()
                
                orders_layout.addLayout(order_layout)
            
            layout.addLayout(orders_layout)
            
            recommendation = QLabel("<b>Recommandation:</b> Attribuez ces produits à la commande la plus ancienne en premier.")
            recommendation.setStyleSheet("color: #4472C4; margin-top: 10px;")
            layout.addWidget(recommendation)
        else:
            no_orders = QLabel("Aucune commande n'est en attente de ce produit.")
            no_orders.setStyleSheet("font-style: italic;")
            layout.addWidget(no_orders)
        
        # Boutons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)
    
    def get_oldest_orders(self):
        """Récupère les commandes les plus anciennes qui attendent ce produit"""
        return self.order_controller.get_orders_waiting_for_product(self.product, self.color)


class PrintPlanWidget(QWidget):
    """Widget principal pour le plan d'impression"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.print_controller = PrintController()
        self.inventory_controller = InventoryController()
        self.workflow_controller = WorkflowController()
        self.order_controller = OrderController()
        
        # Données du plan d'impression
        self.print_plan = {}
        self.products_to_print = []
        self.products_printing = []
        
        # Configuration des colonnes du tableau
        self.COLUMN_COLOR = 0
        self.COLUMN_PRODUCT = 1
        self.COLUMN_QUANTITY = 2
        self.COLUMN_PRIORITY = 3
        self.COLUMN_ACTIONS = 4
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configure l'interface utilisateur du plan d'impression avec deux tableaux"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # En-tête avec filtres communs
        header_layout = QHBoxLayout()
        
        # Titre compact
        title = QLabel("Plan d'impression")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Filtre par couleur (commun aux deux tableaux)
        color_label = QLabel("Couleur:")
        header_layout.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItem("Toutes")
        for color in COLORS:
            self.color_combo.addItem(color)
        self.color_combo.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(self.color_combo)
        
        # Filtre par priorité (uniquement pour le tableau "À imprimer")
        priority_label = QLabel("Priorité:")
        header_layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItem("Toutes")
        self.priority_combo.addItem("Haute")
        self.priority_combo.addItem("Moyenne")
        self.priority_combo.addItem("Basse")
        self.priority_combo.currentTextChanged.connect(self.apply_filters)
        header_layout.addWidget(self.priority_combo)
        
        header_layout.addStretch()
        
        # Bouton rafraîchir
        refresh_button = QPushButton()
        refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_button.setFixedSize(28, 28)
        refresh_button.clicked.connect(self.load_data)
        refresh_button.setToolTip("Actualiser")
        header_layout.addWidget(refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # Zone des tableaux
        self.tab_widget = QTabWidget()
        
        # 1. Onglet "À imprimer"
        to_print_widget = QWidget()
        to_print_layout = QVBoxLayout(to_print_widget)
        to_print_layout.setContentsMargins(0, 10, 0, 0)
        
        # Tableau des produits à imprimer
        self.to_print_table = QTableWidget()
        self.to_print_table.setColumnCount(5)
        self.to_print_table.setHorizontalHeaderLabels(["Couleur", "Produit", "Quantité", "Priorité", "Actions"])
        self.to_print_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.to_print_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Configuration des colonnes
        self.to_print_table.horizontalHeader().setSectionResizeMode(self.COLUMN_COLOR, QHeaderView.ResizeToContents)
        self.to_print_table.horizontalHeader().setSectionResizeMode(self.COLUMN_PRODUCT, QHeaderView.Stretch)
        self.to_print_table.horizontalHeader().setSectionResizeMode(self.COLUMN_QUANTITY, QHeaderView.ResizeToContents)
        self.to_print_table.horizontalHeader().setSectionResizeMode(self.COLUMN_PRIORITY, QHeaderView.ResizeToContents)
        self.to_print_table.horizontalHeader().setSectionResizeMode(self.COLUMN_ACTIONS, QHeaderView.ResizeToContents)
        
        # Activer le tri
        self.to_print_table.setSortingEnabled(True)
        
        # Style du tableau
        self.to_print_table.setAlternatingRowColors(True)
        self.to_print_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                selection-background-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ddd;
            }
        """)
        
        # Menu contextuel
        self.to_print_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.to_print_table.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.to_print_table, is_printing=False)
        )
        
        to_print_layout.addWidget(self.to_print_table)
        
        # 2. Onglet "En impression"
        printing_widget = QWidget()
        printing_layout = QVBoxLayout(printing_widget)
        printing_layout.setContentsMargins(0, 10, 0, 0)
        
        # Tableau des produits en impression
        self.printing_table = QTableWidget()
        self.printing_table.setColumnCount(5)
        self.printing_table.setHorizontalHeaderLabels(["Couleur", "Produit", "Quantité", "Priorité", "Actions"])
        self.printing_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.printing_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Configuration des colonnes comme le premier tableau
        self.printing_table.horizontalHeader().setSectionResizeMode(self.COLUMN_COLOR, QHeaderView.ResizeToContents)
        self.printing_table.horizontalHeader().setSectionResizeMode(self.COLUMN_PRODUCT, QHeaderView.Stretch)
        self.printing_table.horizontalHeader().setSectionResizeMode(self.COLUMN_QUANTITY, QHeaderView.ResizeToContents)
        self.printing_table.horizontalHeader().setSectionResizeMode(self.COLUMN_PRIORITY, QHeaderView.ResizeToContents)
        self.printing_table.horizontalHeader().setSectionResizeMode(self.COLUMN_ACTIONS, QHeaderView.ResizeToContents)
        
        # Activer le tri
        self.printing_table.setSortingEnabled(True)
        
        # Style du tableau
        self.printing_table.setAlternatingRowColors(True)
        self.printing_table.setStyleSheet(self.to_print_table.styleSheet())
        
        # Menu contextuel
        self.printing_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.printing_table.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(pos, self.printing_table, is_printing=True)
        )
        
        printing_layout.addWidget(self.printing_table)
        
        # Ajouter les onglets
        self.tab_widget.addTab(to_print_widget, "À imprimer")
        self.tab_widget.addTab(printing_widget, "En impression")
        
        main_layout.addWidget(self.tab_widget)
        
        # Barre d'état
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)
        
        main_layout.addLayout(status_layout)
        
        # Timer pour auto-refresh périodique
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_data)
        self.refresh_timer.start(120000)  # 2 minutes
    
    def load_data(self):
        """Charge les données du plan d'impression"""
        self.print_plan = self.print_controller.get_print_plan(include_printing=True)
        self.prepare_product_lists()
        self.update_tables()
        self.update_status_bar()
    
    def prepare_product_lists(self):
        """Prépare deux listes distinctes : produits à imprimer et produits en impression"""
        self.products_to_print = []
        self.products_printing = []
        
        # Aplatir la structure pour faciliter l'affichage dans les tableaux
        for color, products in self.print_plan.items():
            for product in products:
                # Ajouter la couleur dans les données du produit
                product_data = product.copy()
                product_data["color"] = color
                
                # Répartir dans la liste appropriée selon le statut
                if product_data.get("status") == "En impression":
                    self.products_printing.append(product_data)
                else:
                    self.products_to_print.append(product_data)
    
    def update_tables(self):
        """Met à jour les deux tableaux avec les données filtrées"""
        # Mettre à jour le tableau des produits à imprimer
        self.update_to_print_table()
        
        # Mettre à jour le tableau des produits en impression
        self.update_printing_table()
    
    def update_to_print_table(self):
        """Met à jour le tableau des produits à imprimer"""
        # Désactiver temporairement le tri
        sorting_enabled = self.to_print_table.isSortingEnabled()
        self.to_print_table.setSortingEnabled(False)
        
        # Sauvegarder le tri actuel
        sort_column = self.to_print_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.to_print_table.horizontalHeader().sortIndicatorOrder()
        
        # Vider le tableau
        self.to_print_table.setRowCount(0)
        
        # Appliquer les filtres
        filtered_products = self.get_filtered_products(self.products_to_print)
        
        # Remplir le tableau
        for product_data in filtered_products:
            row = self.to_print_table.rowCount()
            self.to_print_table.insertRow(row)
            
            # Ajouter les données dans chaque colonne
            self.add_color_cell(self.to_print_table, row, product_data["color"])
            self.add_product_cell(self.to_print_table, row, product_data["product"])
            self.add_quantity_cell(self.to_print_table, row, product_data["quantity"])
            self.add_priority_cell(self.to_print_table, row, product_data["priority"])
            self.add_actions_cell(self.to_print_table, row, product_data, is_printing=False)
            
        # Réactiver le tri avec les paramètres précédents
        self.to_print_table.setSortingEnabled(sorting_enabled)
        if sorting_enabled:
            self.to_print_table.sortItems(sort_column, sort_order)
    
    def update_printing_table(self):
        """Met à jour le tableau des produits en impression"""
        # Désactiver temporairement le tri
        sorting_enabled = self.printing_table.isSortingEnabled()
        self.printing_table.setSortingEnabled(False)
        
        # Sauvegarder le tri actuel
        sort_column = self.printing_table.horizontalHeader().sortIndicatorSection()
        sort_order = self.printing_table.horizontalHeader().sortIndicatorOrder()
        
        # Vider le tableau
        self.printing_table.setRowCount(0)
        
        # Appliquer les filtres (uniquement par couleur pour ce tableau)
        filtered_products = self.get_filtered_products(self.products_printing, ignore_priority=True)
        
        # Remplir le tableau
        for product_data in filtered_products:
            row = self.printing_table.rowCount()
            self.printing_table.insertRow(row)
            
            # Ajouter les données dans chaque colonne
            self.add_color_cell(self.printing_table, row, product_data["color"])
            self.add_product_cell(self.printing_table, row, product_data["product"])
            self.add_quantity_cell(self.printing_table, row, product_data["quantity"])
            self.add_priority_cell(self.printing_table, row, product_data["priority"])
            self.add_actions_cell(self.printing_table, row, product_data, is_printing=True)
            
        # Réactiver le tri avec les paramètres précédents
        self.printing_table.setSortingEnabled(sorting_enabled)
        if sorting_enabled:
            self.printing_table.sortItems(sort_column, sort_order)
            
        # Basculer sur l'onglet "En impression" s'il y a des produits en cours d'impression
        if self.printing_table.rowCount() > 0 and self.tab_widget.currentIndex() != 1:
            # Clignoter le titre de l'onglet ou changer sa couleur pour attirer l'attention
            self.tab_widget.setTabText(1, "✓ En impression")
        else:
            self.tab_widget.setTabText(1, "En impression")
    
    def add_color_cell(self, table, row, color):
        """Ajoute une cellule pour la couleur avec l'indicateur visuel et le texte"""
        # Créer directement un QTableWidgetItem avec le nom de la couleur
        item = QTableWidgetItem("  " + color)  # Espace au début pour laisser place à l'indicateur de couleur
        item.setData(Qt.UserRole, color)  # Pour le tri
        
        # Définir une couleur de fond pour toute la cellule
        bgColor = QColor(COLOR_HEX_MAP.get(color, "#CCCCCC"))
        # Ajuster la luminosité pour assurer la lisibilité du texte
        # Si la couleur est trop claire, on utilise un texte foncé, sinon un texte clair
        brightness = (bgColor.red() * 299 + bgColor.green() * 587 + bgColor.blue() * 114) / 1000
        if brightness > 125:  # Couleur claire
            item.setForeground(QColor(0, 0, 0))  # Texte noir
        else:  # Couleur foncée
            item.setForeground(QColor(255, 255, 255))  # Texte blanc
        
        # Appliquer la couleur de fond
        item.setBackground(bgColor)
        
        table.setItem(row, self.COLUMN_COLOR, item)
    
    def add_product_cell(self, table, row, product):
        """Ajoute une cellule pour le nom du produit"""
        item = QTableWidgetItem(product)
        table.setItem(row, self.COLUMN_PRODUCT, item)
    
    def add_quantity_cell(self, table, row, quantity):
        """Ajoute une cellule pour la quantité avec alignement centré"""
        item = QTableWidgetItem(str(quantity))
        item.setData(Qt.UserRole, quantity)  # Pour le tri numérique
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, self.COLUMN_QUANTITY, item)
    
    def add_priority_cell(self, table, row, priority):
        """Ajoute une cellule pour la priorité avec couleur appropriée"""
        item = QTableWidgetItem(priority)
        
        # Valeur numérique pour le tri
        priority_value = {"Haute": 3, "Moyenne": 2, "Basse": 1}.get(priority, 0)
        item.setData(Qt.UserRole, priority_value)
        
        # Couleur selon priorité
        if priority == "Haute":
            item.setForeground(QColor(UI_COLORS["danger"]))
        elif priority == "Moyenne":
            item.setForeground(QColor(UI_COLORS["warning"]))
        else:
            item.setForeground(QColor(UI_COLORS["info"]))
            
        table.setItem(row, self.COLUMN_PRIORITY, item)
    
    def add_actions_cell(self, table, row, product_data, is_printing):
        """Ajoute une cellule pour les actions selon l'état d'impression"""
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(4, 2, 4, 2)
        actions_layout.setAlignment(Qt.AlignCenter)
        
        if not is_printing:
            # Bouton pour lancer l'impression
            start_btn = QPushButton("Lancer")
            start_btn.setFixedHeight(24)
            start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QPushButton:hover { background-color: #45a049; }
            """)
            
            product = product_data["product"]
            color = product_data["color"]
            quantity = product_data["quantity"]
            start_btn.clicked.connect(lambda checked=False, p=product, c=color, q=quantity: 
                                     self.show_print_dialog(p, c, q))
            actions_layout.addWidget(start_btn)
        else:
            # Bouton pour terminer l'impression
            complete_btn = QPushButton("Terminer")
            complete_btn.setFixedHeight(24)
            complete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QPushButton:hover { background-color: #0b7dda; }
            """)
            
            product = product_data["product"]
            color = product_data["color"]
            quantity = product_data["quantity"]
            complete_btn.clicked.connect(lambda checked=False, p=product, c=color, q=quantity: 
                                       self.complete_printing_job(p, c, q))
            actions_layout.addWidget(complete_btn)
        
        table.setCellWidget(row, self.COLUMN_ACTIONS, actions_widget)
    
    def get_filtered_products(self, products_list, ignore_priority=False):
        """Applique les filtres actuels à une liste de produits"""
        filtered_products = []
        
        # Récupérer les valeurs des filtres
        color_filter = self.color_combo.currentText()
        priority_filter = self.priority_combo.currentText()
        
        # Appliquer les filtres
        for product in products_list:
            # Filtre de couleur
            if color_filter != "Toutes" and product["color"] != color_filter:
                continue
            
            # Filtre de priorité (seulement si applicable)
            if not ignore_priority and priority_filter != "Toutes" and product["priority"] != priority_filter:
                continue
            
            filtered_products.append(product)
        
        return filtered_products
    
    def update_status_bar(self):
        """Met à jour la barre d'état avec des statistiques"""
        to_print_count = len(self.products_to_print)
        printing_count = len(self.products_printing)
        high_priority = sum(1 for p in self.products_to_print if p["priority"] == "Haute")
        
        status_text = f"{to_print_count} produits à imprimer • {printing_count} en cours d'impression"
        
        if high_priority > 0:
            status_text += f" • {high_priority} priorité haute"
        
        self.status_label.setText(status_text)
    
    def apply_filters(self):
        """Applique les filtres et met à jour les tableaux"""
        self.update_tables()
    
    def show_context_menu(self, position, table, is_printing):
        """Affiche un menu contextuel sur clic droit dans un tableau"""
        menu = QMenu()
        
        # Obtenir la ligne sélectionnée
        row = table.rowAt(position.y())
        if row >= 0:
            # Récupérer les données de la ligne
            product = table.item(row, self.COLUMN_PRODUCT).text()
            color_item = table.item(row, self.COLUMN_COLOR)
            color = color_item.data(Qt.UserRole) if color_item else ""
            quantity = int(table.item(row, self.COLUMN_QUANTITY).text())
            
            # Actions du menu contextuel selon le statut
            if not is_printing:
                start_action = menu.addAction("Lancer l'impression")
                start_action.triggered.connect(lambda: self.show_print_dialog(product, color, quantity))
            else:
                complete_action = menu.addAction("Terminer l'impression")
                complete_action.triggered.connect(lambda: self.complete_printing_job(product, color, quantity))
            
            # Exécuter le menu
            menu.exec_(QCursor.pos())
    
    def show_print_dialog(self, product, color, quantity):
        """Affiche le dialogue pour démarrer une impression"""
        # Ouvrir la boîte de dialogue
        dialog = StartPrintDialog(product, color, quantity, self)
        if dialog.exec_() == QDialog.Accepted:
            quantity_to_print = dialog.get_quantity()
            self.start_printing_job(product, color, quantity_to_print)
    
    def start_printing_job(self, product, color, quantity_to_print):
        """Démarre l'impression d'un produit"""
        try:
            # Appeler le contrôleur pour démarrer l'impression
            self.print_controller.start_printing_batch_partial(product, color, quantity_to_print)
            
            QMessageBox.information(self, "Impression démarrée",
                                  f"L'impression de {quantity_to_print} {product}(s) en {color} a été démarrée.")
            
            # Rafraîchir les données
            self.load_data()
            
            # Basculer vers l'onglet "En impression"
            self.tab_widget.setCurrentIndex(1)
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", 
                              f"Une erreur s'est produite lors du démarrage de l'impression:\n{str(e)}")
    
    def complete_printing_job(self, product, color, quantity):
        """Marque un job d'impression comme terminé et suggère la commande à alimenter"""
        try:
            # Afficher le dialogue avec les commandes en attente
            dialog = CompletePrintDialog(product, color, quantity, self)
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Marquer comme imprimé
                self.print_controller.mark_as_printed(product, color)
                
                # Mettre à jour l'inventaire
                if quantity > 0:
                    self.inventory_controller.adjust_inventory_after_printing(product, color, quantity)
                
                # Rafraîchir les données
                self.load_data()
                
                # Revenir vers l'onglet "À imprimer" s'il n'y a plus d'impressions en cours
                if self.printing_table.rowCount() == 0:
                    self.tab_widget.setCurrentIndex(0)
        
        except Exception as e:
            QMessageBox.warning(self, "Erreur", 
                              f"Une erreur s'est produite lors de la finalisation de l'impression:\n{str(e)}")