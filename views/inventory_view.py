from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QScrollArea, QPushButton, QSizePolicy,
                           QGridLayout, QSpacerItem, QTabWidget, QTableWidget,
                           QTableWidgetItem, QComboBox, QSpinBox, QHeaderView,
                           QDialog, QFormLayout, QLineEdit, QColorDialog, QMessageBox,
                           QListWidget, QListWidgetItem, QSplitter, QTreeWidget, 
                           QTreeWidgetItem, QGroupBox, QCheckBox, QTextEdit, QRadioButton)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QBrush
from controllers.inventory_controller import InventoryController
from models.inventory import InventoryItem, ColorVariant, ProductComponent
from config import COLORS, PRODUCTS, UI_COLORS

class InventoryWidget(QWidget):
    """Widget principal pour la gestion de l'inventaire"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_controller = InventoryController()
        self.selected_product = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configure l'interface utilisateur de l'inventaire"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Titre de la page
        title_label = QLabel("Gestion de l'inventaire")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {UI_COLORS['primary']};")
        main_layout.addWidget(title_label)
        
        # Onglets pour organiser l'interface
        self.tab_widget = QTabWidget()
        
        # Onglet de l'inventaire des produits finis
        self.products_tab = QWidget()
        self.setup_products_tab()
        self.tab_widget.addTab(self.products_tab, "Produits finis")
        
        # Onglet de l'inventaire des composants
        self.components_tab = QWidget()
        self.setup_components_tab()
        self.tab_widget.addTab(self.components_tab, "Composants")
        
        # Onglet pour les définitions de produits
        self.product_defs_tab = QWidget()
        self.setup_product_defs_tab()
        self.tab_widget.addTab(self.product_defs_tab, "Définitions de produits")
        
        # Onglet pour les prévisions
        self.forecast_tab = QWidget()
        self.setup_forecast_tab()
        self.tab_widget.addTab(self.forecast_tab, "Prévisions")
        
        main_layout.addWidget(self.tab_widget)
        
        # Boutons d'action en bas
        action_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_btn.clicked.connect(self.load_data)
        
        export_btn = QPushButton("Exporter")
        export_btn.setIcon(self.style().standardIcon(self.style().SP_DialogSaveButton))
        export_btn.clicked.connect(self.export_inventory)
        
        action_layout.addWidget(refresh_btn)
        action_layout.addWidget(export_btn)
        action_layout.addStretch()
        
        main_layout.addLayout(action_layout)
    
    def setup_products_tab(self):
        """Configure l'onglet des produits finis"""
        layout = QVBoxLayout(self.products_tab)
        
        # Filtres en haut
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filtrer par produit:"))
        self.product_filter = QComboBox()
        self.product_filter.addItem("Tous")
        self.product_filter.addItems(PRODUCTS)
        self.product_filter.currentTextChanged.connect(self.apply_product_filters)
        filter_layout.addWidget(self.product_filter)
        
        filter_layout.addWidget(QLabel("Filtrer par couleur:"))
        self.color_filter = QComboBox()
        self.color_filter.addItem("Toutes")
        self.color_filter.addItems([c for c in COLORS if c != "Aléatoire"])
        self.color_filter.currentTextChanged.connect(self.apply_product_filters)
        filter_layout.addWidget(self.color_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tableau des produits finis
        self.products_table = QTableWidget(0, 6)
        self.products_table.setHorizontalHeaderLabels([
            "Produit", "Couleur/Variante", "Stock", "Assemblables", "Seuil d'alerte", "Actions"
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.products_table)
        
        # Options d'action
        actions_layout = QHBoxLayout()
        
        add_product_btn = QPushButton("Ajouter stock produit")
        add_product_btn.clicked.connect(self.add_product_stock_dialog)
        
        assemble_product_btn = QPushButton("Assembler produit")
        assemble_product_btn.clicked.connect(self.assemble_product_dialog)
        
        actions_layout.addStretch()
        actions_layout.addWidget(add_product_btn)
        actions_layout.addWidget(assemble_product_btn)
        
        layout.addLayout(actions_layout)
    
    def setup_components_tab(self):
        """Configure l'onglet des composants"""
        layout = QVBoxLayout(self.components_tab)
        
        # Filtres en haut
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filtrer par produit:"))
        self.component_product_filter = QComboBox()
        self.component_product_filter.addItem("Tous")
        self.component_product_filter.addItems(PRODUCTS)
        self.component_product_filter.currentTextChanged.connect(self.update_component_filters)
        filter_layout.addWidget(self.component_product_filter)
        
        filter_layout.addWidget(QLabel("Filtrer par composant:"))
        self.component_name_filter = QComboBox()
        self.component_name_filter.addItem("Tous")
        self.component_name_filter.currentTextChanged.connect(self.apply_component_filters)
        filter_layout.addWidget(self.component_name_filter)
        
        filter_layout.addWidget(QLabel("Filtrer par couleur:"))
        self.component_color_filter = QComboBox()
        self.component_color_filter.addItem("Toutes")
        self.component_color_filter.addItems([c for c in COLORS if c != "Aléatoire"])
        self.component_color_filter.currentTextChanged.connect(self.apply_component_filters)
        filter_layout.addWidget(self.component_color_filter)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tableau des composants
        self.components_table = QTableWidget(0, 6)
        self.components_table.setHorizontalHeaderLabels([
            "Produit", "Composant", "Couleur", "Stock", "Seuil d'alerte", "Actions"
        ])
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.components_table)
        
        # Options d'action
        actions_layout = QHBoxLayout()
        
        add_component_btn = QPushButton("Ajouter composant")
        add_component_btn.clicked.connect(self.add_component_dialog)
        
        add_component_stock_btn = QPushButton("Ajouter stock composant")
        add_component_stock_btn.clicked.connect(self.add_component_stock_dialog)
        
        actions_layout.addStretch()
        actions_layout.addWidget(add_component_btn)
        actions_layout.addWidget(add_component_stock_btn)
        
        layout.addLayout(actions_layout)
    
    def setup_product_defs_tab(self):
        """Configure l'onglet des définitions de produits"""
        layout = QVBoxLayout(self.product_defs_tab)
        
        # Splitter pour diviser la vue en deux parties
        splitter = QSplitter(Qt.Horizontal)
        
        # Partie gauche: Liste des produits
        products_list_widget = QWidget()
        products_list_layout = QVBoxLayout(products_list_widget)
        
        products_list_title = QLabel("Produits")
        products_list_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        products_list_layout.addWidget(products_list_title)
        
        self.products_list = QListWidget()
        self.products_list.currentItemChanged.connect(self.on_product_def_selected)
        products_list_layout.addWidget(self.products_list)
        
        # Partie droite: Détails et structure du produit
        product_def_widget = QWidget()
        product_def_layout = QVBoxLayout(product_def_widget)
        
        self.product_def_title = QLabel("Définition du produit")
        self.product_def_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        product_def_layout.addWidget(self.product_def_title)
        
        # Table des composants du produit
        self.product_components_table = QTableWidget(0, 4)
        self.product_components_table.setHorizontalHeaderLabels([
            "Composant", "Quantité", "Options de couleur", "Actions"
        ])
        self.product_components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.product_components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        product_def_layout.addWidget(self.product_components_table)
        
        # Bouton pour ajouter un composant au produit
        add_to_product_btn = QPushButton("Ajouter composant au produit")
        add_to_product_btn.clicked.connect(self.add_component_to_product_dialog)
        product_def_layout.addWidget(add_to_product_btn)
        
        # Règles d'assemblage spécifiques
        rules_group = QGroupBox("Règles d'assemblage spécifiques")
        rules_layout = QVBoxLayout(rules_group)
        
        self.has_custom_rules_check = QCheckBox("Utiliser des règles personnalisées")
        self.has_custom_rules_check.stateChanged.connect(self.toggle_custom_rules)
        rules_layout.addWidget(self.has_custom_rules_check)
        
        # Notes sur les règles d'assemblage
        rules_label = QLabel("Exemple: 'Corps toujours noir', 'Les deux roues doivent être de la même couleur'")
        rules_label.setWordWrap(True)
        rules_layout.addWidget(rules_label)
        
        self.rules_text = QTextEdit()
        self.rules_text.setPlaceholderText("Entrez les règles d'assemblage spécifiques à ce produit...")
        self.rules_text.setEnabled(False)  # Désactivé par défaut
        rules_layout.addWidget(self.rules_text)
        
        save_rules_btn = QPushButton("Enregistrer les règles")
        save_rules_btn.clicked.connect(self.save_product_rules)
        rules_layout.addWidget(save_rules_btn)
        
        product_def_layout.addWidget(rules_group)
        
        # Ajouter les widgets au splitter
        splitter.addWidget(products_list_widget)
        splitter.addWidget(product_def_widget)
        
        # Définir les tailles initiales
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)
    
    def setup_forecast_tab(self):
        """Configure l'onglet des prévisions d'inventaire"""
        layout = QVBoxLayout(self.forecast_tab)
        
        # Explication des prévisions
        info_label = QLabel(
            "Les prévisions sont calculées en fonction des ventes des 3 derniers mois. "
            "Le stock recommandé est 1,5 fois les ventes mensuelles moyennes, "
            "ajusté par un facteur de tendance qui reflète l'évolution récente des ventes."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Filtres
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Afficher:"))
        self.forecast_view_combo = QComboBox()
        self.forecast_view_combo.addItems(["Produits finis", "Composants", "Tous"])
        self.forecast_view_combo.currentTextChanged.connect(self.apply_forecast_filters)
        filter_layout.addWidget(self.forecast_view_combo)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Tableau des prévisions
        self.forecast_table = QTableWidget(0, 7)
        self.forecast_table.setHorizontalHeaderLabels([
            "Produit", "Composant", "Variante", "Stock actuel", 
            "Ventes mensuelles", "Stock recommandé", "Tendance"
        ])
        self.forecast_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.forecast_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.forecast_table)
        
        # Bouton pour mettre à jour les prévisions
        update_forecast_btn = QPushButton("Mettre à jour les prévisions")
        update_forecast_btn.clicked.connect(self.update_forecasts)
        
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        action_layout.addWidget(update_forecast_btn)
        
        layout.addLayout(action_layout)
    
    def load_data(self):
        """Charge les données dans tous les onglets avec gestion d'erreurs"""
        try:
            self.load_product_data()
        except Exception as e:
            print(f"Erreur lors du chargement des données de produits: {e}")
            QMessageBox.warning(self, "Erreur", f"Impossible de charger les produits: {str(e)}")
        
        try:
            self.load_component_data()
        except Exception as e:
            print(f"Erreur lors du chargement des données de composants: {e}")
        
        try:
            self.load_product_definitions()
        except Exception as e:
            print(f"Erreur lors du chargement des définitions de produits: {e}")
        
        try:
            self.load_forecast_data()
        except Exception as e:
            print(f"Erreur lors du chargement des prévisions: {e}")
        
        self.update_component_filters()
    
    def load_product_data(self):
        """Charge les données des produits finis dans le tableau"""
        # Récupérer l'inventaire sans les composants
        inventory = self.inventory_controller.get_inventory_with_print_needs(include_components=False)
        
        # Filtrer selon les critères sélectionnés
        filtered_inventory = self.filter_product_inventory(inventory)
        
        # Calculer le nombre assemblable pour chaque produit/couleur
        for item in filtered_inventory:
            # Déterminer si c'est un produit avec composants
            has_components = self.inventory_controller.is_product_with_components(item['product'])
            
            if has_components:
                # Calculer combien de produits peuvent être assemblés
                item['assemblable'] = self.calculate_assemblable(item['product'], item['color'])
            else:
                item['assemblable'] = 0  # Pas de composants, donc pas assemblable
        
        # Mise à jour du tableau
        self.products_table.setRowCount(0)
        self.products_table.setRowCount(len(filtered_inventory))
        
        for row, item in enumerate(filtered_inventory):
            # Produit
            self.products_table.setItem(row, 0, QTableWidgetItem(item['product']))
            
            # Couleur/Variante
            self.products_table.setItem(row, 1, QTableWidgetItem(item['color']))
            
            # Stock
            stock_item = QTableWidgetItem(str(item['stock']))
            if item['stock'] < item['alert_threshold']:
                stock_item.setBackground(QColor('#FFDDDD'))
            self.products_table.setItem(row, 2, stock_item)
            
            # Assemblables
            assemblable_item = QTableWidgetItem(str(item.get('assemblable', 0)))
            self.products_table.setItem(row, 3, assemblable_item)
            
            # Seuil d'alerte
            self.products_table.setItem(row, 4, QTableWidgetItem(str(item['alert_threshold'])))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton +
            add_btn = QPushButton("+")
            add_btn.setMaximumWidth(30)
            add_btn.clicked.connect(lambda _, p=item['product'], c=item['color']: 
                                  self.quick_add_product_stock(p, c))
            
            # Bouton -
            sub_btn = QPushButton("-")
            sub_btn.setMaximumWidth(30)
            sub_btn.clicked.connect(lambda _, p=item['product'], c=item['color']: 
                                  self.quick_remove_product_stock(p, c))
            
            # Bouton Assembler (si assemblable)
            if item.get('assemblable', 0) > 0:
                assemble_btn = QPushButton("Assembler")
                assemble_btn.clicked.connect(lambda _, p=item['product'], c=item['color']: 
                                          self.assemble_specific_product(p, c))
                actions_layout.addWidget(assemble_btn)
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(sub_btn)
            
            self.products_table.setCellWidget(row, 5, actions_widget)
    
    def filter_product_inventory(self, inventory):
        """Filtre l'inventaire selon les critères sélectionnés"""
        filtered = []
        
        product_filter = self.product_filter.currentText()
        color_filter = self.color_filter.currentText()
        
        for item in inventory:
            # Appliquer le filtre de produit
            if product_filter != "Tous" and item['product'] != product_filter:
                continue
                
            # Appliquer le filtre de couleur
            if color_filter != "Toutes" and item['color'] != color_filter:
                continue
                
            filtered.append(item)
        
        return filtered
    
    def calculate_assemblable(self, product, color):
        """
        Calcule le nombre de produits assemblables en fonction du stock des composants
        """
        # Obtenir la définition des composants pour ce produit
        components = self.inventory_controller.get_product_components(product)
        if not components:
            return 0  # Aucun composant défini
        
        # Vérifier le stock de chaque composant
        min_assemblable = float('inf')
        
        for component in components:
            component_name = component['name']
            quantity_needed = component['quantity']
            
            # Vérifier si le composant a une couleur spécifique définie
            # Cette logique doit être adaptée selon comment vous stockez les contraintes de couleur
            color_constraint = component.get('color_constraint')
            
            # Si le composant a une couleur spécifique, utiliser cette couleur
            # sinon utiliser la couleur du produit final
            component_color = color_constraint if color_constraint else color
            
            # Récupérer le stock disponible pour ce composant
            component_stock = self.inventory_controller.get_product_stock(
                product, component_color, component_name)
            
            # Si le composant est épuisé, le produit n'est pas assemblable
            if component_stock == 0:
                return 0
            
            # Calculer combien de produits peuvent être assemblés avec ce composant
            possible_from_component = component_stock // quantity_needed
            
            # Mettre à jour le minimum
            min_assemblable = min(min_assemblable, possible_from_component)
        
        # Si aucun composant n'a été trouvé, ou si la quantité est infinie
        if min_assemblable == float('inf'):
            return 0
            
        return min_assemblable
    
    def load_component_data(self):
        """Charge les données des composants dans le tableau"""
        # Récupérer l'inventaire complet
        inventory = self.inventory_controller.get_inventory_with_print_needs(include_components=True)
        
        # Filtrer pour ne garder que les composants selon les critères sélectionnés
        filtered_inventory = []
        
        product_filter = self.component_product_filter.currentText()
        component_filter = self.component_name_filter.currentText()
        color_filter = self.component_color_filter.currentText()
        
        for item in inventory:
            # Ignorer les non-composants
            if not item['component']:
                continue
                
            # Appliquer le filtre de produit
            if product_filter != "Tous" and item['product'] != product_filter:
                continue
                
            # Appliquer le filtre de composant
            if component_filter != "Tous" and item['component'] != component_filter:
                continue
                
            # Appliquer le filtre de couleur
            if color_filter != "Toutes" and item['color'] != color_filter:
                continue
                
            filtered_inventory.append(item)
        
        # Mise à jour du tableau
        self.components_table.setRowCount(0)
        self.components_table.setRowCount(len(filtered_inventory))
        
        for row, item in enumerate(filtered_inventory):
            # Produit
            self.components_table.setItem(row, 0, QTableWidgetItem(item['product']))
            
            # Composant
            self.components_table.setItem(row, 1, QTableWidgetItem(item['component']))
            
            # Couleur
            self.components_table.setItem(row, 2, QTableWidgetItem(item['color']))
            
            # Stock
            stock_item = QTableWidgetItem(str(item['stock']))
            if item['status'] == 'Low':
                stock_item.setBackground(QColor('#FFDDDD'))
            self.components_table.setItem(row, 3, stock_item)
            
            # Seuil d'alerte
            self.components_table.setItem(row, 4, QTableWidgetItem(str(item['alert_threshold'])))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton +
            add_btn = QPushButton("+")
            add_btn.setMaximumWidth(30)
            add_btn.clicked.connect(lambda _, p=item['product'], c=item['color'], comp=item['component']: 
                                  self.quick_add_component_stock(p, comp, c))
            
            # Bouton -
            sub_btn = QPushButton("-")
            sub_btn.setMaximumWidth(30)
            sub_btn.clicked.connect(lambda _, p=item['product'], c=item['color'], comp=item['component']: 
                                  self.quick_remove_component_stock(p, comp, c))
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(sub_btn)
            
            self.components_table.setCellWidget(row, 5, actions_widget)
    
    def update_component_filters(self):
        """Met à jour les options du filtre de composants en fonction du produit sélectionné"""
        product = self.component_product_filter.currentText()
        
        # Réinitialiser le filtre de composants
        self.component_name_filter.clear()
        self.component_name_filter.addItem("Tous")
        
        if product != "Tous":
            # Récupérer tous les composants pour ce produit
            components = self.inventory_controller.get_product_components(product)
            
            for component in components:
                self.component_name_filter.addItem(component['name'])
        else:
            # En mode "Tous les produits", récupérer tous les composants uniques
            all_components = set()
            for product_name in PRODUCTS:
                components = self.inventory_controller.get_product_components(product_name)
                for component in components:
                    all_components.add(component['name'])
            
            for component_name in sorted(all_components):
                self.component_name_filter.addItem(component_name)
        
        # Appliquer les nouveaux filtres
        self.apply_component_filters()
    
    def apply_component_filters(self):
        """Applique les filtres et met à jour le tableau des composants"""
        self.load_component_data()
    
    def apply_product_filters(self):
        """Applique les filtres et met à jour le tableau des produits"""
        self.load_product_data()
    
    def load_product_definitions(self):
        """Charge les définitions de produits dans la liste"""
        # Vider la liste actuelle
        self.products_list.clear()
        
        # Ajouter tous les produits à la liste
        for product in PRODUCTS:
            item = QListWidgetItem(product)
            # Stocker si le produit a des composants
            has_components = self.inventory_controller.is_product_with_components(product)
            item.setData(Qt.UserRole, has_components)
            self.products_list.addItem(item)
    
    def on_product_def_selected(self, current, previous):
        """Gère la sélection d'un produit dans la liste des définitions"""
        if not current:
            return
            
        product = current.text()
        self.product_def_title.setText(f"Définition du produit: {product}")
        
        # Vérifier si le produit a des composants
        has_components = current.data(Qt.UserRole)
        
        if has_components:
            # Charger les composants du produit
            self.load_product_components(product)
        else:
            # Effacer le tableau des composants
            self.product_components_table.setRowCount(0)
    
    def load_product_components(self, product):
        """Charge les composants d'un produit dans le tableau"""
        components = self.inventory_controller.get_product_components(product)
        
        # Mise à jour du tableau
        self.product_components_table.setRowCount(0)
        self.product_components_table.setRowCount(len(components))
        
        for row, component in enumerate(components):
            # Nom du composant
            self.product_components_table.setItem(row, 0, QTableWidgetItem(component['name']))
            
            # Quantité
            self.product_components_table.setItem(row, 1, QTableWidgetItem(str(component['quantity'])))
            
            # Options de couleur (à implémenter plus tard)
            self.product_components_table.setItem(row, 2, QTableWidgetItem("Toutes les couleurs"))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton pour modifier le composant
            edit_btn = QPushButton("Modifier")
            edit_btn.clicked.connect(lambda _, p=product, c=component['name']: 
                                   self.edit_product_component(p, c))
            
            # Bouton pour supprimer le composant
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, p=product, c=component['name']: 
                                     self.remove_product_component(p, c))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.product_components_table.setCellWidget(row, 3, actions_widget)
    
    def toggle_custom_rules(self, state):
        """Active ou désactive le champ de règles personnalisées"""
        self.rules_text.setEnabled(state == Qt.Checked)
    
    def save_product_rules(self):
        """Enregistre les règles d'assemblage personnalisées pour le produit sélectionné"""
        # Cette fonction nécessite l'implémentation d'un système de stockage des règles
        current_item = self.products_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun produit sélectionné")
            return
            
        QMessageBox.information(
            self,
            "Fonctionnalité à venir",
            "L'enregistrement des règles d'assemblage personnalisées sera disponible dans une prochaine version."
        )
    
    def load_forecast_data(self):
        """Charge les données de prévisions d'inventaire"""
        try:
            forecasts = self.inventory_controller.get_inventory_with_forecast()
            
            # Filtrer selon le type sélectionné
            filtered_forecasts = []
            forecast_type = self.forecast_view_combo.currentText()
            
            for item in forecasts:
                if forecast_type == "Produits finis" and item.get('component'):
                    continue
                elif forecast_type == "Composants" and not item.get('component'):
                    continue
                
                filtered_forecasts.append(item)
            
            # Mise à jour du tableau
            self.forecast_table.setRowCount(0)
            self.forecast_table.setRowCount(len(filtered_forecasts))
            
            for row, item in enumerate(filtered_forecasts):
                # Produit
                self.forecast_table.setItem(row, 0, QTableWidgetItem(item.get('product', 'N/A')))
                
                # Composant
                component = item.get('component', '') if item.get('component') else "-"
                self.forecast_table.setItem(row, 1, QTableWidgetItem(component))
                
                # Variante (couleur)
                self.forecast_table.setItem(row, 2, QTableWidgetItem(item.get('color', 'N/A')))
                
                # Stock actuel
                stock = item.get('stock', 0)
                stock_item = QTableWidgetItem(str(stock))
                if item.get('status') in ['Low', 'Below Forecast']:
                    stock_item.setBackground(QColor('#FFDDDD'))
                self.forecast_table.setItem(row, 3, stock_item)
                
                # Ventes mensuelles moyennes
                sales = round(item.get('avg_monthly_sales', 0), 2)
                self.forecast_table.setItem(row, 4, QTableWidgetItem(str(sales)))
                
                # Stock recommandé
                recommended = item.get('forecast_stock', 0)
                self.forecast_table.setItem(row, 5, QTableWidgetItem(str(recommended)))
                
                # Tendance (facteur)
                trend_factor = item.get('trend_factor', 1.0)
                trend_item = QTableWidgetItem(f"{trend_factor:.2f}x")
                if trend_factor > 1:
                    trend_item.setBackground(QColor('#DDFFDD'))
                elif trend_factor < 1:
                    trend_item.setBackground(QColor('#FFDDDD'))
                self.forecast_table.setItem(row, 6, trend_item)
        except Exception as e:
            print(f"Erreur lors du chargement des prévisions: {e}")
            # En cas d'erreur, vider le tableau pour éviter des affichages partiels
            self.forecast_table.setRowCount(0)
    
    def apply_forecast_filters(self):
        """Applique les filtres et met à jour le tableau des prévisions"""
        self.load_forecast_data()
    
    def quick_add_product_stock(self, product, color):
        """Ajoute rapidement 1 au stock du produit"""
        self.inventory_controller.adjust_stock(product, color, 1)
        self.load_product_data()
    
    def quick_remove_product_stock(self, product, color):
        """Retire rapidement 1 du stock du produit"""
        self.inventory_controller.adjust_stock(product, color, -1)
        self.load_product_data()
    
    def quick_add_component_stock(self, product, component, color):
        """Ajoute rapidement 1 au stock du composant"""
        self.inventory_controller.adjust_stock(product, color, 1, component)
        self.load_component_data()
    
    def quick_remove_component_stock(self, product, component, color):
        """Retire rapidement 1 du stock du composant"""
        self.inventory_controller.adjust_stock(product, color, -1, component)
        self.load_component_data()
    
    def add_product_stock_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter du stock à un produit fini"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter du stock de produit fini")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Sélection du produit
        product_combo = QComboBox()
        product_combo.addItems(PRODUCTS)
        layout.addRow("Produit:", product_combo)
        
        # Sélection de la couleur
        color_combo = QComboBox()
        color_combo.addItems([c for c in COLORS if c != "Aléatoire"])
        layout.addRow("Couleur:", color_combo)
        
        # Quantité à ajouter
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 1000)
        quantity_spin.setValue(1)
        layout.addRow("Quantité:", quantity_spin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            product = product_combo.currentText()
            color = color_combo.currentText()
            quantity = quantity_spin.value()
            
            self.inventory_controller.adjust_stock(product, color, quantity)
            self.load_product_data()
    
    def add_component_stock_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter du stock à un composant"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter du stock de composant")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Sélection du produit
        product_combo = QComboBox()
        product_combo.addItems([p for p in PRODUCTS 
                               if self.inventory_controller.is_product_with_components(p)])
        layout.addRow("Produit:", product_combo)
        
        # Sélection du composant
        component_combo = QComboBox()
        
        def update_components():
            # Mettre à jour la liste des composants en fonction du produit sélectionné
            product = product_combo.currentText()
            component_combo.clear()
            
            components = self.inventory_controller.get_product_components(product)
            for comp in components:
                component_combo.addItem(comp['name'])
        
        product_combo.currentTextChanged.connect(update_components)
        update_components()  # Initialiser les composants
        
        layout.addRow("Composant:", component_combo)
        
        # Sélection de la couleur
        color_combo = QComboBox()
        color_combo.addItems([c for c in COLORS if c != "Aléatoire"])
        layout.addRow("Couleur:", color_combo)
        
        # Quantité à ajouter
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 1000)
        quantity_spin.setValue(1)
        layout.addRow("Quantité:", quantity_spin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            product = product_combo.currentText()
            component = component_combo.currentText()
            color = color_combo.currentText()
            quantity = quantity_spin.value()
            
            self.inventory_controller.adjust_stock(product, color, quantity, component)
            self.load_component_data()
    
    def assemble_product_dialog(self):
        """Ouvre une boîte de dialogue pour assembler un produit à partir de composants"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Assembler un produit")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Formulaire pour sélectionner le produit et la couleur
        form_layout = QFormLayout()
        
        # Sélection du produit
        product_combo = QComboBox()
        product_combo.addItems([p for p in PRODUCTS 
                               if self.inventory_controller.is_product_with_components(p)])
        form_layout.addRow("Produit:", product_combo)
        
        # Sélection de la couleur
        color_combo = QComboBox()
        color_combo.addItems([c for c in COLORS if c != "Aléatoire"])
        form_layout.addRow("Couleur:", color_combo)
        
        # Quantité à assembler
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 100)
        quantity_spin.setValue(1)
        form_layout.addRow("Quantité:", quantity_spin)
        
        layout.addLayout(form_layout)
        
        # Tableau des composants nécessaires
        components_label = QLabel("Composants nécessaires:")
        components_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(components_label)
        
        self.assembly_components_table = QTableWidget(0, 4)
        self.assembly_components_table.setHorizontalHeaderLabels([
            "Composant", "Nécessaire", "Disponible", "Manquant"
        ])
        self.assembly_components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assembly_components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.assembly_components_table)
        
        # Mise à jour du tableau des composants en fonction de la sélection
        def update_assembly_components():
            product = product_combo.currentText()
            color = color_combo.currentText()
            quantity = quantity_spin.value()
            
            # Récupérer les composants nécessaires
            components = self.inventory_controller.get_product_components(product)
            
            # Mise à jour du tableau
            self.assembly_components_table.setRowCount(0)
            self.assembly_components_table.setRowCount(len(components))
            
            for row, component in enumerate(components):
                # Nom du composant
                self.assembly_components_table.setItem(row, 0, QTableWidgetItem(component['name']))
                
                # Quantité nécessaire
                total_needed = component['quantity'] * quantity
                self.assembly_components_table.setItem(row, 1, QTableWidgetItem(str(total_needed)))
                
                # Stock disponible
                available = self.inventory_controller.get_product_stock(product, color, component['name'])
                available_item = QTableWidgetItem(str(available))
                
                # Mettre en évidence si pas assez de stock
                if available < total_needed:
                    available_item.setBackground(QColor('#FFDDDD'))
                
                self.assembly_components_table.setItem(row, 2, available_item)
                
                # Manquant
                missing = max(0, total_needed - available)
                self.assembly_components_table.setItem(row, 3, QTableWidgetItem(str(missing)))
            
            # Vérifier s'il y a assez de composants pour assembler
            can_assemble = True
            for row in range(self.assembly_components_table.rowCount()):
                if int(self.assembly_components_table.item(row, 3).text()) > 0:
                    can_assemble = False
                    break
            
            assemble_btn.setEnabled(can_assemble)
        
        # Connecter les changements de sélection à la mise à jour du tableau
        product_combo.currentTextChanged.connect(update_assembly_components)
        color_combo.currentTextChanged.connect(update_assembly_components)
        quantity_spin.valueChanged.connect(update_assembly_components)
        
        # Initialiser le tableau
        update_assembly_components()
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        assemble_btn = QPushButton("Assembler")
        assemble_btn.clicked.connect(dialog.accept)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(assemble_btn)
        
        layout.addLayout(buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            product = product_combo.currentText()
            color = color_combo.currentText()
            quantity = quantity_spin.value()
            
            # Assembler le produit
            self.assemble_product(product, color, quantity)
    
    def assemble_product(self, product, color, quantity=1):
        """
        Assemble un produit à partir de ses composants
        - Réduit le stock des composants nécessaires
        - Augmente le stock du produit fini
        """
        try:
            # Récupérer les composants nécessaires
            components = self.inventory_controller.get_product_components(product)
            
            # Vérifier s'il y a assez de composants
            for component in components:
                component_name = component['name']
                needed = component['quantity'] * quantity
                
                # Vérifier si le composant a une couleur spécifique définie
                color_constraint = component.get('color_constraint')
                component_color = color_constraint if color_constraint else color
                
                available = self.inventory_controller.get_product_stock(
                    product, component_color, component_name)
                
                if available < needed:
                    raise ValueError(f"Pas assez de composants {component_name} disponibles")
            
            # Soustraire les composants utilisés
            for component in components:
                component_name = component['name']
                used = component['quantity'] * quantity
                
                # Utiliser la couleur contrainte si définie
                color_constraint = component.get('color_constraint')
                component_color = color_constraint if color_constraint else color
                
                self.inventory_controller.adjust_stock(
                    product, component_color, -used, component_name)
            
            # Ajouter le produit assemblé à l'inventaire
            self.inventory_controller.adjust_stock(product, color, quantity)
            
            QMessageBox.information(
                self,
                "Assemblage réussi",
                f"{quantity} {product} de couleur {color} ont été assemblés avec succès."
            )
            
            # Mettre à jour les tableaux
            self.load_product_data()
            self.load_component_data()
            
        except ValueError as e:
            QMessageBox.warning(self, "Erreur d'assemblage", str(e))
        
    def assemble_specific_product(self, product, color):
        """Assemble un produit spécifique à partir de la liste des produits"""
        self.assemble_product(product, color, 1)
    
    def add_component_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter un nouveau composant de produit"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un nouveau composant")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Sélection du produit
        product_combo = QComboBox()
        product_combo.addItems(PRODUCTS)
        layout.addRow("Produit:", product_combo)
        
        # Nom du composant
        component_edit = QLineEdit()
        layout.addRow("Nom du composant:", component_edit)
        
        # Options pour les couleurs disponibles
        colors_group = QGroupBox("Options de couleurs")
        colors_layout = QVBoxLayout(colors_group)
        
        all_colors_check = QCheckBox("Toutes les couleurs")
        all_colors_check.setChecked(True)
        colors_layout.addWidget(all_colors_check)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addRow(colors_group)
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            product = product_combo.currentText()
            component = component_edit.text()
            
            if component:
                # À ce stade, nous ajoutons simplement le composant sans gestion spécifique de couleurs
                self.inventory_controller.add_product_component(product, component, 1)
                self.load_product_definitions()
                
                # Si le produit est actuellement sélectionné, rafraîchir ses composants
                current_item = self.products_list.currentItem()
                if current_item and current_item.text() == product:
                    self.load_product_components(product)
            else:
                QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")
    
    def add_component_to_product_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter un composant à un produit existant"""
        # Vérifier qu'un produit est sélectionné
        current_item = self.products_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun produit sélectionné")
            return
            
        product = current_item.text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajouter un composant à {product}")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Nom du composant
        component_edit = QLineEdit()
        layout.addRow("Nom du composant:", component_edit)
        
        # Quantité nécessaire
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 10)
        quantity_spin.setValue(1)
        layout.addRow("Quantité nécessaire:", quantity_spin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            component = component_edit.text()
            quantity = quantity_spin.value()
            
            if component:
                self.inventory_controller.add_product_component(product, component, quantity)
                
                # Marquer le produit comme ayant des composants
                current_item.setData(Qt.UserRole, True)
                
                # Mettre à jour l'affichage des composants
                self.load_product_components(product)
            else:
                QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")
    
    def edit_product_component(self, product, component):
        """Ouvre une boîte de dialogue pour modifier un composant existant"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifier le composant {component}")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Récupérer les informations actuelles du composant
        components = self.inventory_controller.get_product_components(product)
        current_component = None
        for comp in components:
            if comp['name'] == component:
                current_component = comp
                break
        
        if not current_component:
            QMessageBox.warning(self, "Erreur", f"Composant {component} introuvable")
            return
        
        # Quantité nécessaire
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 10)
        quantity_spin.setValue(current_component['quantity'])
        layout.addRow("Quantité nécessaire:", quantity_spin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        save_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            quantity = quantity_spin.value()
            
            # Pour modifier la quantité, il faut supprimer puis recréer le composant
            self.inventory_controller.remove_product_component(product, component)
            self.inventory_controller.add_product_component(product, component, quantity)
            
            # Mettre à jour l'affichage des composants
            self.load_product_components(product)
    
    def remove_product_component(self, product, component):
        """Supprime un composant d'un produit"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le composant '{component}' du produit '{product}'?\n\n"
            f"ATTENTION: Cela supprimera également tout le stock de ce composant.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Récupérer tous les items d'inventaire pour ce composant
            inventory = self.inventory_controller.get_inventory(include_components=True)
            components_to_delete = [item for item in inventory 
                                if item['product'] == product and 
                                item['component'] == component]
            
            # Supprimer chaque entrée d'inventaire pour ce composant
            for item in components_to_delete:
                # Utilisez une méthode supplémentaire du contrôleur pour supprimer complètement
                # cette entrée d'inventaire, pas seulement mettre le stock à 0
                self.inventory_controller.delete_inventory_item(
                    product, item['color'], component)
            
            # Supprimer la définition du composant
            self.inventory_controller.remove_product_component(product, component)
            
            # Vérifier s'il reste des composants pour ce produit
            remaining_components = self.inventory_controller.get_product_components(product)
            
            if not remaining_components:
                # Si plus de composants, marquer le produit comme n'ayant pas de composants
                for i in range(self.products_list.count()):
                    item = self.products_list.item(i)
                    if item.text() == product:
                        item.setData(Qt.UserRole, False)
                        break
            
            # Mettre à jour l'affichage des composants
            self.load_product_components(product)
            self.load_component_data()  # Rafraîchir aussi la liste des composants
  
    def update_forecasts(self):
        """Met à jour les prévisions d'inventaire"""
        self.inventory_controller.update_inventory_forecast()
        self.load_forecast_data()
        
        QMessageBox.information(
            self,
            "Prévisions mises à jour",
            "Les prévisions d'inventaire ont été mises à jour en fonction des ventes récentes."
        )
    
    def export_inventory(self):
        """Exporte l'inventaire vers un fichier CSV ou Excel"""
        # Cette fonctionnalité sera implémentée ultérieurement
        QMessageBox.information(
            self,
            "Fonctionnalité à venir",
            "L'export de l'inventaire sera disponible dans une prochaine version."
        )
    def add_component_to_product_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter un composant à un produit existant"""
        # Vérifier qu'un produit est sélectionné
        current_item = self.products_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun produit sélectionné")
            return
            
        product = current_item.text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajouter un composant à {product}")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Nom du composant
        component_edit = QLineEdit()
        layout.addRow("Nom du composant:", component_edit)
        
        # Quantité nécessaire
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 10)
        quantity_spin.setValue(1)
        layout.addRow("Quantité nécessaire:", quantity_spin)
        
        # Options de couleur
        color_group = QGroupBox("Options de couleur")
        color_layout = QVBoxLayout(color_group)
        
        all_colors_radio = QRadioButton("Toutes les couleurs")
        all_colors_radio.setChecked(True)
        color_layout.addWidget(all_colors_radio)
        
        specific_color_radio = QRadioButton("Couleur spécifique")
        color_layout.addWidget(specific_color_radio)
        
        specific_color_combo = QComboBox()
        specific_color_combo.addItems([c for c in COLORS if c != "Aléatoire"])
        specific_color_combo.setEnabled(False)
        color_layout.addWidget(specific_color_combo)
        
        # Activer/désactiver le combobox en fonction de la sélection
        specific_color_radio.toggled.connect(lambda checked: specific_color_combo.setEnabled(checked))
        
        layout.addRow(color_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(add_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            component = component_edit.text()
            quantity = quantity_spin.value()
            
            if component:
                # Déterminer la couleur spécifique si sélectionnée
                color_constraint = None
                if specific_color_radio.isChecked():
                    color_constraint = specific_color_combo.currentText()
                    
                # Stockez la contrainte de couleur dans les métadonnées du composant
                # Cette partie nécessite une extension de la méthode add_product_component
                self.inventory_controller.add_product_component(
                    product, component, quantity, color_constraint)
                
                # Marquer le produit comme ayant des composants
                current_item.setData(Qt.UserRole, True)
                
                # Mettre à jour l'affichage des composants
                self.load_product_components(product)
            else:
                QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")