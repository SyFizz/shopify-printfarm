"""
Vue pour la gestion de l'inventaire Plasmik3D.
Implémente l'interface utilisateur pour gérer les composants, produits et l'assemblage.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QComboBox, QSpinBox, QHeaderView, QMessageBox,
                             QDialog, QFormLayout, QLineEdit, QGroupBox,
                             QTabWidget, QSplitter, QFrame, QRadioButton,
                             QCheckBox, QListWidget, QListWidgetItem, QGridLayout,
                             QSizePolicy, QMenu, QAction, QInputDialog)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QBrush, QCursor, QFont
from controllers.inventory_controller import InventoryController
from config import COLORS, PRODUCTS, UI_COLORS, COLOR_HEX_MAP

class ColorIndicator(QFrame):
    """Widget pour afficher un indicateur de couleur"""
    
    def __init__(self, color, size=16, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        
        # Utiliser le code hexadécimal si disponible, sinon une couleur par défaut
        hex_color = COLOR_HEX_MAP.get(color, "#CCCCCC")
        
        self.setStyleSheet(f"""
            background-color: {hex_color};
            border: 1px solid #999;
            border-radius: {size // 4}px;
        """)

class AssembleDialog(QDialog):
    """Dialogue pour assembler un produit"""
    
    def __init__(self, product_name, product_details, available_colors, parent=None):
        super().__init__(parent)
        self.product_name = product_name
        self.product_details = product_details
        self.available_colors = available_colors
        self.component_colors = {}
        
        self.setWindowTitle(f"Assembler {product_name}")
        self.setMinimumWidth(450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Information sur le produit
        product_info = QLabel(f"<b>{self.product_name}</b>")
        product_info.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(product_info)
        
        # Description (si disponible)
        if self.product_details["description"]:
            desc_label = QLabel(self.product_details["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; margin-bottom: 15px;")
            layout.addWidget(desc_label)
        
        # Groupe pour la sélection de couleur principale
        color_group = QGroupBox("Couleur du produit")
        color_layout = QVBoxLayout(color_group)
        
        # Option pour la couleur principale
        self.color_combo = QComboBox()
        
        # Ajouter l'option "Aléatoire" si des assemblages sont possibles
        self.color_combo.addItem("Aléatoire")
        
        # Ajouter les couleurs spécifiques
        for color in sorted(self.available_colors):
            self.color_combo.addItem(color)
            
        # Si une seule couleur est disponible, la sélectionner
        if len(self.available_colors) == 1:
            self.color_combo.setCurrentText(list(self.available_colors)[0])
        
        # Connecter le changement de couleur
        self.color_combo.currentTextChanged.connect(self.update_component_colors)
        
        color_layout.addWidget(self.color_combo)
        layout.addWidget(color_group)
        
        # Groupe pour les options de couleur des composants (si des contraintes existent)
        has_color_constraints = any("color_constraint" in comp for comp in self.product_details["components"])
        
        if has_color_constraints:
            component_group = QGroupBox("Options de couleur des composants")
            self.component_layout = QFormLayout(component_group)
            
            for component in self.product_details["components"]:
                name = component["name"]
                
                if "color_constraint" in component:
                    constraint = component["color_constraint"]
                    
                    # Si la contrainte n'est pas fixe, ajouter un sélecteur
                    if constraint is None:
                        color_selector = QComboBox()
                        color_selector.addItem("Même que le produit")
                        
                        for color in sorted([c for c in COLORS if c != "Aléatoire"]):
                            color_selector.addItem(color)
                        
                        color_selector.currentTextChanged.connect(
                            lambda text, comp_name=name: self.on_component_color_changed(comp_name, text)
                        )
                        
                        self.component_layout.addRow(f"{name}:", color_selector)
                    else:
                        # Pour les contraintes fixes, montrer simplement l'information
                        constraint_desc = self.get_constraint_description(constraint)
                        self.component_layout.addRow(f"{name}:", QLabel(constraint_desc))
            
            layout.addWidget(component_group)
        
        # Quantité à assembler
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantité à assembler:"))
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(100)  # Ajuster selon les besoins
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(lambda: self.update_component_colors(self.color_combo.currentText()))
        quantity_layout.addWidget(self.quantity_spin)
        
        layout.addLayout(quantity_layout)
        
        # Informations sur les composants requis
        components_group = QGroupBox("Composants requis")
        components_layout = QVBoxLayout(components_group)
        
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(4)
        self.components_table.setHorizontalHeaderLabels(["Composant", "Couleur", "Requis", "Disponible"])
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        components_layout.addWidget(self.components_table)
        layout.addWidget(components_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        self.assemble_btn = QPushButton("Assembler")
        self.assemble_btn.clicked.connect(self.accept)
        self.assemble_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(self.assemble_btn)
        
        layout.addLayout(buttons_layout)
        
        # Mettre à jour l'affichage des composants requis
        self.update_component_colors(self.color_combo.currentText())
    
    def get_constraint_description(self, constraint):
        """Retourne une description lisible d'une contrainte de couleur"""
        if constraint == "same_as_main":
            return "Même couleur que le produit principal"
        elif constraint.startswith("fixed:"):
            color = constraint.split(":", 1)[1]
            return f"Toujours en {color}"
        elif constraint.startswith("same_as:"):
            ref_component = constraint.split(":", 1)[1]
            return f"Même couleur que le composant '{ref_component}'"
        return constraint
    
    def on_component_color_changed(self, component_name, text):
        """Gère le changement de couleur pour un composant spécifique"""
        if text == "Même que le produit":
            # Utiliser la même couleur que le produit principal
            if component_name in self.component_colors:
                del self.component_colors[component_name]
        else:
            # Utiliser une couleur spécifique
            self.component_colors[component_name] = text
        
        # Mettre à jour l'affichage
        self.update_component_colors(self.color_combo.currentText())
    
    def update_component_colors(self, main_color):
        """Met à jour l'affichage des composants en fonction de la couleur principale"""
        # Si la couleur est aléatoire, utiliser la première couleur disponible pour l'aperçu
        display_color = main_color
        if main_color == "Aléatoire" and self.available_colors:
            display_color = list(self.available_colors)[0]
        
        # Récupérer les composants nécessaires
        required_components = []
        
        for component in self.product_details["components"]:
            comp_name = component["name"]
            quantity = component["quantity"] * self.quantity_spin.value()
            
            # Déterminer la couleur du composant selon les contraintes
            comp_color = display_color  # Par défaut, même couleur que le produit
            
            if "color_constraint" in component:
                constraint = component["color_constraint"]
                
                if constraint == "same_as_main":
                    # Même couleur que le produit principal
                    comp_color = display_color
                elif constraint and constraint.startswith("fixed:"):
                    # Couleur fixe
                    comp_color = constraint.split(":", 1)[1]
                elif constraint and constraint.startswith("same_as:"):
                    # Même couleur qu'un autre composant
                    ref_component = constraint.split(":", 1)[1]
                    # Trouver la couleur du composant référencé
                    for c in required_components:
                        if c["name"] == ref_component:
                            comp_color = c["color"]
                            break
                
            # Si une couleur spécifique est définie dans component_colors, l'utiliser
            if comp_name in self.component_colors:
                comp_color = self.component_colors[comp_name]
            
            required_components.append({
                "name": comp_name,
                "color": comp_color,
                "quantity": quantity
            })
        
        # Mettre à jour le tableau des composants
        self.components_table.setRowCount(len(required_components))
        
        # Vérifier si l'assemblage est possible
        can_assemble = True
        
        for row, comp in enumerate(required_components):
            # Composant
            self.components_table.setItem(row, 0, QTableWidgetItem(comp["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(comp["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(comp["color"], "#CCCCCC")))
            self.components_table.setItem(row, 1, color_item)
            
            # Quantité requise
            self.components_table.setItem(row, 2, QTableWidgetItem(str(comp["quantity"])))
            
            # Stock disponible (peut être implémenté avec les données réelles)
            available = InventoryController().get_component_stock(comp["name"], comp["color"])
            available_item = QTableWidgetItem(str(available))
            
            # Mettre en rouge si le stock est insuffisant
            if available < comp["quantity"]:
                available_item.setForeground(QColor("red"))
                can_assemble = False
            
            self.components_table.setItem(row, 3, available_item)
        
        # Désactiver le bouton si l'assemblage n'est pas possible
        self.assemble_btn.setEnabled(can_assemble)
        
        # Redimensionner les lignes pour un meilleur affichage
        self.components_table.resizeRowsToContents()
    
    def get_assembly_data(self):
        """Retourne les données pour l'assemblage"""
        return {
            "product": self.product_name,
            "color": self.color_combo.currentText(),
            "quantity": self.quantity_spin.value(),
            "component_colors": self.component_colors.copy()
        }

class InventoryView(QWidget):
    """Widget principal pour la gestion de l'inventaire"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_controller = InventoryController()
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Titre de la page
        title_label = QLabel("Gestion de l'inventaire")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {UI_COLORS['primary']};")
        layout.addWidget(title_label)
        
        # Onglets pour organiser l'interface
        tab_widget = QTabWidget()
        
        # 1. Onglet composants
        self.components_tab = QWidget()
        self.setup_components_tab()
        tab_widget.addTab(self.components_tab, "Composants")
        
        # 2. Onglet produits assemblés
        self.products_tab = QWidget()
        self.setup_products_tab()
        tab_widget.addTab(self.products_tab, "Produits assemblés")
        
        # 3. Onglet produits (définitions)
        self.definitions_tab = QWidget()
        self.setup_definitions_tab()
        tab_widget.addTab(self.definitions_tab, "Définitions de produits")
        
        # 4. Onglet assemblage
        self.assembly_tab = QWidget()
        self.setup_assembly_tab()
        tab_widget.addTab(self.assembly_tab, "Assemblage")
        
        layout.addWidget(tab_widget)
        
        # Barre d'état
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Prêt")
        status_layout.addWidget(self.status_label)
        
        refresh_btn = QPushButton("Actualiser")
        refresh_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_btn.clicked.connect(self.load_data)
        status_layout.addWidget(refresh_btn)
        
        layout.addLayout(status_layout)
    
    def setup_components_tab(self):
        """Configure l'onglet des composants"""
        layout = QVBoxLayout(self.components_tab)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Composant:"))
        self.component_filter = QComboBox()
        self.component_filter.addItem("Tous")
        self.component_filter.currentTextChanged.connect(self.apply_component_filters)
        filters_layout.addWidget(self.component_filter)
        
        filters_layout.addWidget(QLabel("Couleur:"))
        self.color_filter = QComboBox()
        self.color_filter.addItem("Toutes")
        self.color_filter.addItems([c for c in COLORS if c != "Aléatoire"])
        self.color_filter.currentTextChanged.connect(self.apply_component_filters)
        filters_layout.addWidget(self.color_filter)
        
        # Nouveau filtre pour les produits qui utilisent ce composant
        filters_layout.addWidget(QLabel("Produit:"))
        self.product_component_filter = QComboBox()
        self.product_component_filter.addItem("Tous")
        self.product_component_filter.currentTextChanged.connect(self.apply_component_filters)
        filters_layout.addWidget(self.product_component_filter)
        
        filters_layout.addStretch()
        
        # Bouton pour ajouter un nouveau composant
        add_component_btn = QPushButton("Nouveau composant")
        add_component_btn.setIcon(self.style().standardIcon(self.style().SP_FileIcon))
        add_component_btn.clicked.connect(self.add_new_component_dialog)
        filters_layout.addWidget(add_component_btn)
        
        layout.addLayout(filters_layout)
        
        # Tableau des composants
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(6)  # Ajouté une colonne pour les produits qui utilisent ce composant
        self.components_table.setHorizontalHeaderLabels(
            ["Composant", "Couleur", "Utilisé dans", "Stock", "Seuil d'alerte", "Actions"]
        )
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.components_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Menu contextuel
        self.components_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.components_table.customContextMenuRequested.connect(self.show_component_context_menu)
        
        layout.addWidget(self.components_table)
    
    def setup_products_tab(self):
        """Configure l'onglet des produits assemblés"""
        layout = QVBoxLayout(self.products_tab)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Produit:"))
        self.product_filter = QComboBox()
        self.product_filter.addItem("Tous")
        self.product_filter.currentTextChanged.connect(self.apply_product_filters)
        filters_layout.addWidget(self.product_filter)
        
        filters_layout.addWidget(QLabel("Couleur:"))
        self.product_color_filter = QComboBox()
        self.product_color_filter.addItem("Toutes")
        self.product_color_filter.addItems(COLORS)
        self.product_color_filter.currentTextChanged.connect(self.apply_product_filters)
        filters_layout.addWidget(self.product_color_filter)
        
        filters_layout.addStretch()
        
        layout.addLayout(filters_layout)
        
        # Tableau des produits assemblés
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels(
            ["Produit", "Couleur", "Stock", "Composants", "Actions"]
        )
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Menu contextuel
        self.products_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.show_product_context_menu)
        
        layout.addWidget(self.products_table)
    
    def setup_definitions_tab(self):
        """Configure l'onglet des définitions de produits"""
        layout = QVBoxLayout(self.definitions_tab)
        
        # Splitter pour diviser l'écran en deux parties
        splitter = QSplitter(Qt.Horizontal)
        
        # Partie gauche: liste des produits
        products_list_widget = QWidget()
        products_list_layout = QVBoxLayout(products_list_widget)
        
        # Titre et boutons
        products_header = QHBoxLayout()
        products_header.addWidget(QLabel("<b>Produits</b>"))
        products_header.addStretch()
        
        add_product_btn = QPushButton("Ajouter")
        add_product_btn.clicked.connect(self.add_new_product_dialog)
        products_header.addWidget(add_product_btn)
        
        products_list_layout.addLayout(products_header)
        
        # Liste des produits
        self.products_list = QListWidget()
        self.products_list.currentItemChanged.connect(self.on_product_selected)
        products_list_layout.addWidget(self.products_list)
        
        # Partie droite: détails du produit
        product_details_widget = QWidget()
        self.product_details_layout = QVBoxLayout(product_details_widget)
        
        # Titre des détails
        self.product_detail_title = QLabel("<b>Détails du produit</b>")
        self.product_details_layout.addWidget(self.product_detail_title)
        
        # Informations sur le produit
        self.product_info_group = QGroupBox("Informations")
        product_info_layout = QFormLayout(self.product_info_group)
        
        self.product_description_label = QLabel("")
        product_info_layout.addRow("Description:", self.product_description_label)
        
        self.product_details_layout.addWidget(self.product_info_group)
        
        # Composants du produit
        self.components_group = QGroupBox("Composants nécessaires")
        components_layout = QVBoxLayout(self.components_group)
        
        self.components_detail_table = QTableWidget()
        self.components_detail_table.setColumnCount(3)
        self.components_detail_table.setHorizontalHeaderLabels(
            ["Composant", "Quantité", "Contrainte de couleur"]
        )
        self.components_detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.components_detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        components_layout.addWidget(self.components_detail_table)
        
        # Boutons pour gérer les composants
        components_buttons = QHBoxLayout()
        
        add_component_btn = QPushButton("Ajouter composant")
        add_component_btn.clicked.connect(self.add_component_to_product_dialog)
        components_buttons.addWidget(add_component_btn)
        
        remove_component_btn = QPushButton("Retirer composant")
        remove_component_btn.clicked.connect(self.remove_component_from_product)
        components_buttons.addWidget(remove_component_btn)
        
        components_layout.addLayout(components_buttons)
        
        self.product_details_layout.addWidget(self.components_group)
        
        # Ajouter les widgets au splitter
        splitter.addWidget(products_list_widget)
        splitter.addWidget(product_details_widget)
        
        # Définir les proportions initiales
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)
    
    def setup_assembly_tab(self):
        """Configure l'onglet d'assemblage"""
        layout = QVBoxLayout(self.assembly_tab)
        
        # Vue en deux parties: produits assemblables et composants disponibles
        splitter = QSplitter(Qt.Vertical)
        
        # Partie supérieure: produits assemblables
        assemblable_widget = QWidget()
        assemblable_layout = QVBoxLayout(assemblable_widget)
        
        assemblable_layout.addWidget(QLabel("<b>Produits assemblables</b>"))
        
        self.assemblable_table = QTableWidget()
        self.assemblable_table.setColumnCount(5)
        self.assemblable_table.setHorizontalHeaderLabels(
            ["Produit", "Couleur", "Assemblables", "Composants", "Actions"]
        )
        self.assemblable_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assemblable_table.setEditTriggers(QTableWidget.NoEditTriggers)
        assemblable_layout.addWidget(self.assemblable_table)
        
        # Partie inférieure: stock de composants disponibles
        components_widget = QWidget()
        components_layout = QVBoxLayout(components_widget)
        
        components_layout.addWidget(QLabel("<b>Stock de composants disponibles</b>"))
        
        self.assembly_components_table = QTableWidget()
        self.assembly_components_table.setColumnCount(3)
        self.assembly_components_table.setHorizontalHeaderLabels(
            ["Composant", "Couleur", "Stock"]
        )
        self.assembly_components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assembly_components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        components_layout.addWidget(self.assembly_components_table)
        
        # Ajouter les widgets au splitter
        splitter.addWidget(assemblable_widget)
        splitter.addWidget(components_widget)
        
        layout.addWidget(splitter)
        
        # Bouton pour raffraîchir les données
        refresh_btn = QPushButton("Actualiser les assemblables")
        refresh_btn.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_btn.clicked.connect(self.update_assemblable_products)
        layout.addWidget(refresh_btn)
    
    def load_data(self):
        """Charge toutes les données de l'inventaire"""
        self.load_components_data()
        self.load_products_data()
        self.load_definitions_data()
        self.update_assemblable_products()
        
        self.status_label.setText(f"Données actualisées: {self.count_components()} composants, {self.count_products()} produits assemblés")
    
    def load_components_data(self):
        """Charge les données des composants"""
        # Récupérer les données
        components = self.inventory_controller.get_all_components()
        
        # Mise à jour du filtre de composants
        self.component_filter.blockSignals(True)
        self.component_filter.clear()
        self.component_filter.addItem("Tous")
        
        # Collecter les noms uniques de composants
        component_names = sorted(list(set(comp["name"] for comp in components)))
        self.component_filter.addItems(component_names)
        self.component_filter.blockSignals(False)
        
        # Mise à jour du filtre de produits
        self.product_component_filter.blockSignals(True)
        self.product_component_filter.clear()
        self.product_component_filter.addItem("Tous")
        
        # Collecter les noms uniques de produits
        all_products = self.inventory_controller.get_all_products()
        product_names = sorted(list(set(prod["name"] for prod in all_products)))
        self.product_component_filter.addItems(product_names)
        self.product_component_filter.blockSignals(False)
        
        # Appliquer les filtres actuels
        self.apply_component_filters()
    
    def apply_component_filters(self):
        """Applique les filtres sur le tableau des composants"""
        # Récupérer les critères de filtre
        component_filter = self.component_filter.currentText()
        color_filter = self.color_filter.currentText()
        product_filter = self.product_component_filter.currentText()
        
        # Récupérer toutes les données
        all_components = self.inventory_controller.get_all_components()
        all_products = self.inventory_controller.get_all_products()
        
        # Créer un dictionnaire pour mapper les composants aux produits qui les utilisent
        component_to_products = {}
        for product in all_products:
            for comp in product["components"]:
                if comp["name"] not in component_to_products:
                    component_to_products[comp["name"]] = []
                if product["name"] not in component_to_products[comp["name"]]:
                    component_to_products[comp["name"]].append(product["name"])
        
        # Appliquer les filtres
        filtered_components = []
        for comp in all_components:
            if component_filter != "Tous" and comp["name"] != component_filter:
                continue
            if color_filter != "Toutes" and comp["color"] != color_filter:
                continue
            if product_filter != "Tous":
                # Vérifier si le composant est utilisé dans le produit sélectionné
                used_in_products = component_to_products.get(comp["name"], [])
                if product_filter not in used_in_products:
                    continue
            filtered_components.append(comp)
        
        # Mise à jour du tableau
        self.components_table.setRowCount(len(filtered_components))
        
        for row, comp in enumerate(filtered_components):
            # Composant
            self.components_table.setItem(row, 0, QTableWidgetItem(comp["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(comp["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(comp["color"], "#CCCCCC")))
            self.components_table.setItem(row, 1, color_item)
            
            # Produits qui utilisent ce composant
            used_in_products = component_to_products.get(comp["name"], [])
            self.components_table.setItem(row, 2, QTableWidgetItem(", ".join(sorted(used_in_products))))
            
            # Stock
            stock_item = QTableWidgetItem(str(comp["stock"]))
            if comp["stock"] <= comp["alert_threshold"]:
                stock_item.setBackground(QColor("#FFCCCC"))  # Rouge clair pour le stock bas
            self.components_table.setItem(row, 3, stock_item)
            
            # Seuil d'alerte
            self.components_table.setItem(row, 4, QTableWidgetItem(str(comp["alert_threshold"])))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton +
            add_btn = QPushButton("+")
            add_btn.setMaximumWidth(30)
            add_btn.clicked.connect(lambda checked=False, name=comp["name"], color=comp["color"]: 
                                  self.adjust_component_stock(name, color, 1))
            
            # Bouton -
            remove_btn = QPushButton("-")
            remove_btn.setMaximumWidth(30)
            remove_btn.clicked.connect(lambda checked=False, name=comp["name"], color=comp["color"]: 
                                     self.adjust_component_stock(name, color, -1))
            
            # Bouton de modification
            edit_btn = QPushButton("Modifier")
            edit_btn.clicked.connect(lambda checked=False, name=comp["name"], color=comp["color"], 
                                    stock=comp["stock"], threshold=comp["alert_threshold"]: 
                                   self.edit_component_dialog(name, color, stock, threshold))
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(remove_btn)
            actions_layout.addWidget(edit_btn)
            
            self.components_table.setCellWidget(row, 5, actions_widget)
        
        # Ajuster la hauteur des lignes
        self.components_table.resizeRowsToContents()
    
    def load_products_data(self):
        """Charge les données des produits assemblés"""
        # Récupérer les données des produits
        all_products = self.inventory_controller.get_all_products()
        
        # Mise à jour du filtre de produits
        self.product_filter.blockSignals(True)
        self.product_filter.clear()
        self.product_filter.addItem("Tous")
        self.product_filter.addItems(sorted(product["name"] for product in all_products))
        self.product_filter.blockSignals(False)
        
        # Appliquer les filtres actuels
        self.apply_product_filters()
    
    def apply_product_filters(self):
        """Applique les filtres sur le tableau des produits assemblés"""
        # Récupérer les critères de filtre
        product_filter = self.product_filter.currentText()
        color_filter = self.product_color_filter.currentText()
        
        # Récupérer toutes les données
        all_products = self.inventory_controller.get_all_products()
        
        # Préparer les données filtrées
        filtered_products = []
        
        for product in all_products:
            if product_filter != "Tous" and product["name"] != product_filter:
                continue
            
            # Pour chaque produit, extraire les entrées par couleur
            for color, quantity in product["assembled_stock"].items():
                if color_filter != "Toutes" and color != color_filter:
                    continue
                
                # Créer une entrée pour cette combinaison produit/couleur
                entry = {
                    "name": product["name"],
                    "color": color,
                    "stock": quantity,
                    "components": product["components"]
                }
                
                filtered_products.append(entry)
        
        # Trier par produit puis par couleur
        filtered_products.sort(key=lambda p: (p["name"], p["color"]))
        
        # Mise à jour du tableau
        self.products_table.setRowCount(len(filtered_products))
        
        for row, product in enumerate(filtered_products):
            # Produit
            self.products_table.setItem(row, 0, QTableWidgetItem(product["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(product["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(product["color"], "#CCCCCC")))
            self.products_table.setItem(row, 1, color_item)
            
            # Stock
            self.products_table.setItem(row, 2, QTableWidgetItem(str(product["stock"])))
            
            # Composants (résumé)
            components_summary = ", ".join(f"{c['quantity']} {c['name']}" for c in product["components"])
            self.products_table.setItem(row, 3, QTableWidgetItem(components_summary))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            # Bouton +
            add_btn = QPushButton("+")
            add_btn.setMaximumWidth(30)
            add_btn.clicked.connect(lambda checked=False, name=product["name"], color=product["color"]: 
                                  self.adjust_product_stock(name, color, 1))
            
            # Bouton -
            remove_btn = QPushButton("-")
            remove_btn.setMaximumWidth(30)
            remove_btn.clicked.connect(lambda checked=False, name=product["name"], color=product["color"]: 
                                     self.adjust_product_stock(name, color, -1))
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(remove_btn)
            
            self.products_table.setCellWidget(row, 4, actions_widget)
        
        # Ajuster la hauteur des lignes
        self.products_table.resizeRowsToContents()
    
    def load_definitions_data(self):
        """Charge les définitions de produits"""
        # Récupérer les données des produits
        all_products = self.inventory_controller.get_all_products()
        
        # Mise à jour de la liste des produits
        self.products_list.clear()
        
        for product in sorted(all_products, key=lambda p: p["name"]):
            item = QListWidgetItem(product["name"])
            # Stocker les données du produit pour référence ultérieure
            item.setData(Qt.UserRole, product)
            self.products_list.addItem(item)
        
        # Effacer les détails du produit
        self.product_detail_title.setText("<b>Détails du produit</b>")
        self.product_description_label.setText("")
        self.components_detail_table.setRowCount(0)
    
    def on_product_selected(self, current, previous):
        """Gère la sélection d'un produit dans la liste"""
        if not current:
            return
        
        # Récupérer les données du produit
        product = current.data(Qt.UserRole)
        
        # Mettre à jour le titre
        self.product_detail_title.setText(f"<b>Produit: {product['name']}</b>")
        
        # Mettre à jour la description
        self.product_description_label.setText(product["description"])
        
        # Mettre à jour le tableau des composants
        self.components_detail_table.setRowCount(len(product["components"]))
        
        for row, component in enumerate(product["components"]):
            # Composant
            self.components_detail_table.setItem(row, 0, QTableWidgetItem(component["name"]))
            
            # Quantité
            self.components_detail_table.setItem(row, 1, QTableWidgetItem(str(component["quantity"])))
            
            # Contrainte de couleur
            constraint_text = "Aucune"
            if "color_constraint" in component and component["color_constraint"]:
                constraint = component["color_constraint"]
                
                if constraint == "same_as_main":
                    constraint_text = "Même couleur que le produit"
                elif constraint.startswith("fixed:"):
                    color = constraint.split(":", 1)[1]
                    constraint_text = f"Fixe: {color}"
                elif constraint.startswith("same_as:"):
                    ref_component = constraint.split(":", 1)[1]
                    constraint_text = f"Même couleur que: {ref_component}"
                else:
                    constraint_text = constraint
            
            self.components_detail_table.setItem(row, 2, QTableWidgetItem(constraint_text))
        
        # Ajuster la hauteur des lignes
        self.components_detail_table.resizeRowsToContents()
    
    def update_assemblable_products(self):
        """Met à jour la liste des produits assemblables"""
        # Récupérer les données des produits assemblables
        assemblable = self.inventory_controller.get_assemblable_products()
        all_products = self.inventory_controller.get_all_products()
        
        # Préparer les données pour l'affichage
        assemblable_products = []
        
        for product_name, colors in assemblable.items():
            # Trouver les détails du produit
            product_details = next((p for p in all_products if p["name"] == product_name), None)
            
            if not product_details:
                continue
            
            # Pour chaque couleur assemblable
            for color, quantity in colors.items():
                if quantity > 0:
                    # Créer une entrée pour cette combinaison produit/couleur
                    entry = {
                        "name": product_name,
                        "color": color,
                        "quantity": quantity,
                        "components": product_details["components"]
                    }
                    
                    assemblable_products.append(entry)
        
        # Mise à jour du tableau des assemblables
        self.assemblable_table.setRowCount(len(assemblable_products))
        
        for row, product in enumerate(assemblable_products):
            # Produit
            self.assemblable_table.setItem(row, 0, QTableWidgetItem(product["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(product["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(product["color"], "#CCCCCC")))
            self.assemblable_table.setItem(row, 1, color_item)
            
            # Quantité assemblable
            self.assemblable_table.setItem(row, 2, QTableWidgetItem(str(product["quantity"])))
            
            # Composants (résumé)
            components_summary = ", ".join(f"{c['quantity']} {c['name']}" for c in product["components"])
            self.assemblable_table.setItem(row, 3, QTableWidgetItem(components_summary))
            
            # Action d'assemblage
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            assemble_btn = QPushButton("Assembler")
            assemble_btn.clicked.connect(lambda checked=False, name=product["name"], color=product["color"]:
                                       self.assemble_product_dialog(name, color))
            actions_layout.addWidget(assemble_btn)
            
            self.assemblable_table.setCellWidget(row, 4, actions_widget)
        
        # Mettre à jour le tableau des composants disponibles
        self.update_components_stock_table()
    
    def update_components_stock_table(self):
        """Met à jour le tableau des stocks de composants"""
        # Récupérer les données des composants
        components = self.inventory_controller.get_all_components()
        
        # Filtrer pour n'afficher que les composants avec un stock > 0
        available_components = [comp for comp in components if comp["stock"] > 0]
        
        # Mise à jour du tableau
        self.assembly_components_table.setRowCount(len(available_components))
        
        for row, comp in enumerate(available_components):
            # Composant
            self.assembly_components_table.setItem(row, 0, QTableWidgetItem(comp["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(comp["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(comp["color"], "#CCCCCC")))
            self.assembly_components_table.setItem(row, 1, color_item)
            
            # Stock
            stock_item = QTableWidgetItem(str(comp["stock"]))
            if comp["stock"] <= comp["alert_threshold"]:
                stock_item.setBackground(QColor("#FFCCCC"))  # Rouge clair pour le stock bas
            self.assembly_components_table.setItem(row, 2, stock_item)
        
        # Ajuster la hauteur des lignes
        self.assembly_components_table.resizeRowsToContents()
    
    def assemble_product_dialog(self, product_name, color):
        """Affiche le dialogue pour assembler un produit"""
        # Récupérer les détails du produit
        product_details = self.inventory_controller.get_product_details(product_name)
        
        if not product_details:
            return
        
        # Récupérer les couleurs disponibles pour ce produit
        assemblable = self.inventory_controller.get_assemblable_products()
        available_colors = {}
        
        if product_name in assemblable:
            available_colors = assemblable[product_name]
        
        # Filtrer pour exclure "Aléatoire" si une couleur spécifique est demandée
        if color != "Aléatoire":
            if color in available_colors:
                available_colors = {color: available_colors[color]}
        
        # Créer et afficher le dialogue
        dialog = AssembleDialog(product_name, product_details, available_colors, self)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Récupérer les données d'assemblage
            assembly_data = dialog.get_assembly_data()
            
            # Effectuer l'assemblage
            success, message = self.inventory_controller.assemble_product(
                assembly_data["product"],
                assembly_data["color"],
                assembly_data["quantity"],
                assembly_data["component_colors"]
            )
            
            # Afficher le résultat
            if success:
                QMessageBox.information(self, "Assemblage réussi", message)
            else:
                QMessageBox.warning(self, "Erreur d'assemblage", message)
            
            # Mettre à jour les données
            self.load_data()
    
    def adjust_component_stock(self, component_name, color, change):
        """Ajuste le stock d'un composant"""
        # Pour les ajustements importants, demander la quantité
        if change == 1 or change == -1:
            # Pour des changements simples, ajuster directement
            success = self.inventory_controller.update_component_stock(component_name, color, change)
            if not success:
                QMessageBox.warning(self, "Erreur", f"Impossible d'ajuster le stock de {component_name} ({color}).")
        else:
            # Pour des ajustements complexes, demander la quantité
            quantity, ok = QInputDialog.getInt(
                self, "Ajuster le stock", 
                f"Nouvelle quantité pour {component_name} ({color}):",
                0, 0, 1000, 1
            )
            
            if ok:
                # Calculer le changement nécessaire
                current_stock = self.inventory_controller.get_component_stock(component_name, color)
                change = quantity - current_stock
                
                # Appliquer le changement
                success = self.inventory_controller.update_component_stock(component_name, color, change)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Impossible d'ajuster le stock de {component_name} ({color}).")
        
        # Mettre à jour les données
        self.load_components_data()
    
    def edit_component_dialog(self, name, color, stock, threshold):
        """Affiche le dialogue pour modifier un composant"""
        # Dialogue pour éditer un composant
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modifier {name} ({color})")
        layout = QFormLayout(dialog)
        
        # Stock actuel
        stock_spin = QSpinBox()
        stock_spin.setMinimum(0)
        stock_spin.setMaximum(1000)
        stock_spin.setValue(stock)
        layout.addRow("Stock:", stock_spin)
        
        # Seuil d'alerte
        threshold_spin = QSpinBox()
        threshold_spin.setMinimum(0)
        threshold_spin.setMaximum(100)
        threshold_spin.setValue(threshold)
        layout.addRow("Seuil d'alerte:", threshold_spin)
        
        # Boutons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        save_btn = QPushButton("Enregistrer")
        save_btn.clicked.connect(dialog.accept)
        save_btn.setDefault(True)
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addRow("", buttons)
        
        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            # Mettre à jour le stock si nécessaire
            new_stock = stock_spin.value()
            if new_stock != stock:
                change = new_stock - stock
                success = self.inventory_controller.update_component_stock(name, color, change)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Impossible de mettre à jour le stock de {name} ({color}).")
            
            # Mettre à jour le seuil d'alerte
            new_threshold = threshold_spin.value()
            if new_threshold != threshold:
                success = self.inventory_controller.set_component_alert_threshold(name, color, new_threshold)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Impossible de mettre à jour le seuil d'alerte de {name} ({color}).")
            
            # Mettre à jour les données
            self.load_components_data()
    
    def show_component_context_menu(self, position):
        """Affiche un menu contextuel pour les actions sur les composants"""
        menu = QMenu()
        
        # Récupérer la ligne sélectionnée
        row = self.components_table.currentRow()
        if row < 0:
            return
        
        # Récupérer les informations du composant
        name = self.components_table.item(row, 0).text()
        color = self.components_table.item(row, 1).text()
        
        # Actions disponibles
        edit_action = menu.addAction("Modifier")
        add_10_action = menu.addAction("Ajouter 10")
        add_50_action = menu.addAction("Ajouter 50")
        set_action = menu.addAction("Définir quantité...")
        menu.addSeparator()
        delete_action = menu.addAction("Supprimer")
        
        # Afficher le menu et récupérer l'action sélectionnée
        action = menu.exec_(self.components_table.viewport().mapToGlobal(position))
        
        # Traiter l'action sélectionnée
        if action == edit_action:
            stock = int(self.components_table.item(row, 3).text())
            threshold = int(self.components_table.item(row, 4).text())
            self.edit_component_dialog(name, color, stock, threshold)
        
        elif action == add_10_action:
            self.adjust_component_stock(name, color, 10)
        
        elif action == add_50_action:
            self.adjust_component_stock(name, color, 50)
        
        elif action == set_action:
            self.adjust_component_stock(name, color, 0)  # 0 pour déclencher la demande de quantité
        
        elif action == delete_action:
            # Confirmation avant suppression
            if QMessageBox.question(self, "Confirmer la suppression", 
                                  f"Êtes-vous sûr de vouloir supprimer {name} ({color}) ?",
                                  QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                
                success = self.inventory_controller.delete_component(name, color)
                if not success:
                    QMessageBox.warning(self, "Erreur", f"Impossible de supprimer {name} ({color}).")
                else:
                    self.load_components_data()
    
    def show_product_context_menu(self, position):
        """Affiche un menu contextuel pour les actions sur les produits assemblés"""
        menu = QMenu()
        
        # Récupérer la ligne sélectionnée
        row = self.products_table.currentRow()
        if row < 0:
            return
        
        # Récupérer les informations du produit
        name = self.products_table.item(row, 0).text()
        color = self.products_table.item(row, 1).text()
        stock = int(self.products_table.item(row, 2).text())
        
        # Actions disponibles
        add_action = menu.addAction("Ajouter 1")
        add_more_action = menu.addAction("Ajouter...")
        remove_action = menu.addAction("Retirer 1")
        remove_more_action = menu.addAction("Retirer...")
        set_action = menu.addAction("Définir quantité...")
        
        # Désactiver certaines actions si le stock est insuffisant
        if stock < 1:
            remove_action.setEnabled(False)
            remove_more_action.setEnabled(False)
        
        # Afficher le menu et récupérer l'action sélectionnée
        action = menu.exec_(self.products_table.viewport().mapToGlobal(position))
        
        # Traiter l'action sélectionnée
        if action == add_action:
            self.adjust_product_stock(name, color, 1)
        
        elif action == add_more_action:
            quantity, ok = QInputDialog.getInt(self, "Ajouter au stock", 
                                              f"Quantité à ajouter pour {name} ({color}):",
                                              1, 1, 1000, 1)
            if ok:
                self.adjust_product_stock(name, color, quantity)
        
        elif action == remove_action:
            self.adjust_product_stock(name, color, -1)
        
        elif action == remove_more_action:
            quantity, ok = QInputDialog.getInt(self, "Retirer du stock", 
                                              f"Quantité à retirer pour {name} ({color}):",
                                              1, 1, stock, 1)
            if ok:
                self.adjust_product_stock(name, color, -quantity)
        
        elif action == set_action:
            quantity, ok = QInputDialog.getInt(self, "Définir le stock", 
                                              f"Nouvelle quantité pour {name} ({color}):",
                                              stock, 0, 1000, 1)
            if ok:
                change = quantity - stock
                self.adjust_product_stock(name, color, change)
    
    def adjust_product_stock(self, product_name, color, change):
        """Ajuste le stock d'un produit assemblé"""
        success = self.inventory_controller.update_assembled_product_stock(product_name, color, change)
        
        if not success:
            QMessageBox.warning(self, "Erreur", f"Impossible d'ajuster le stock de {product_name} ({color}).")
        else:
            # Mettre à jour les données
            self.load_products_data()
    
    def add_new_component_dialog(self):
        """Affiche le dialogue pour ajouter un nouveau composant"""
        # Dialogue pour ajouter un nouveau composant
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau composant")
        layout = QFormLayout(dialog)
        
        # Nom du composant
        name_edit = QLineEdit()
        layout.addRow("Nom du composant:", name_edit)
        
        # Description du composant (facultative)
        description_edit = QLineEdit()
        layout.addRow("Description (facultative):", description_edit)
        
        # Association à un produit
        product_group = QGroupBox("Associer à un produit")
        product_layout = QVBoxLayout(product_group)
        
        # Option pour associer à un produit existant
        associate_checkbox = QCheckBox("Associer ce composant à un produit existant")
        product_layout.addWidget(associate_checkbox)
        
        # Liste déroulante des produits
        products_combo = QComboBox()
        all_products = self.inventory_controller.get_all_products()
        products_combo.addItems([p["name"] for p in all_products])
        products_combo.setEnabled(False)
        product_layout.addWidget(products_combo)
        
        # Connecter la case à cocher pour activer/désactiver la liste déroulante
        associate_checkbox.toggled.connect(products_combo.setEnabled)
        
        layout.addRow("", product_group)
        
        # Stocks initiaux par couleur
        stocks_group = QGroupBox("Stocks initiaux par couleur")
        stocks_layout = QGridLayout(stocks_group)
        
        # Créer des spinboxes pour chaque couleur
        stock_spinboxes = {}
        
        row = 0
        col = 0
        for color in sorted([c for c in COLORS if c != "Aléatoire"]):
            color_layout = QHBoxLayout()
            
            # Indicateur de couleur
            color_indicator = ColorIndicator(color)
            color_layout.addWidget(color_indicator)
            
            # Label de couleur
            color_layout.addWidget(QLabel(color))
            
            # SpinBox pour la quantité
            spinbox = QSpinBox()
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000)
            spinbox.setValue(0)
            color_layout.addWidget(spinbox)
            
            # Stocker la spinbox pour récupérer la valeur plus tard
            stock_spinboxes[color] = spinbox
            
            # Ajouter à la grille
            stocks_layout.addLayout(color_layout, row, col)
            
            # Passer à la colonne suivante ou à la ligne suivante
            col += 1
            if col >= 2:  # 2 colonnes
                col = 0
                row += 1
        
        layout.addRow("", stocks_group)
        
        # Boutons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        save_btn = QPushButton("Ajouter")
        save_btn.clicked.connect(dialog.accept)
        save_btn.setDefault(True)
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addRow("", buttons)
        
        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            component_name = name_edit.text().strip()
            component_description = description_edit.text().strip()
            
            if not component_name:
                QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")
                return
            
            # Récupérer les stocks initiaux
            initial_stock = {}
            for color, spinbox in stock_spinboxes.items():
                value = spinbox.value()
                if value > 0:
                    initial_stock[color] = value
            
            # Ajouter le composant
            success = self.inventory_controller.add_new_component(component_name, initial_stock, component_description)
            
            if not success:
                QMessageBox.warning(self, "Erreur", f"Impossible d'ajouter le composant {component_name}.")
                return
            
            # Si l'utilisateur a choisi d'associer ce composant à un produit
            if associate_checkbox.isChecked() and products_combo.currentText():
                product_name = products_combo.currentText()
                # Ajouter ce composant au produit sélectionné
                self.inventory_controller.add_component_to_product(product_name, component_name, 1)
            
            # Mettre à jour les données
            self.load_data()
            
            QMessageBox.information(self, "Succès", f"Le composant '{component_name}' a été ajouté avec succès.")
    
    def add_new_product_dialog(self):
        """Affiche le dialogue pour ajouter un nouveau produit"""
        # Dialogue pour ajouter un nouveau produit
        dialog = QDialog(self)
        dialog.setWindowTitle("Nouveau produit")
        layout = QFormLayout(dialog)
        
        # Nom du produit
        name_edit = QLineEdit()
        layout.addRow("Nom du produit:", name_edit)
        
        # Description
        description_edit = QLineEdit()
        layout.addRow("Description:", description_edit)
        
        # Boutons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        save_btn = QPushButton("Ajouter")
        save_btn.clicked.connect(dialog.accept)
        save_btn.setDefault(True)
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addRow("", buttons)
        
        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            product_name = name_edit.text().strip()
            description = description_edit.text().strip()
            
            if not product_name:
                QMessageBox.warning(self, "Erreur", "Le nom du produit ne peut pas être vide.")
                return
            
            # Ajouter le produit
            success = self.inventory_controller.add_product(product_name, description)
            
            if not success:
                QMessageBox.warning(self, "Erreur", f"Impossible d'ajouter le produit {product_name}.")
            else:
                # Mettre à jour les données
                self.load_data()
                
                # Sélectionner le nouveau produit dans la liste
                for i in range(self.products_list.count()):
                    item = self.products_list.item(i)
                    if item.text() == product_name:
                        self.products_list.setCurrentItem(item)
                        break
    
    def add_component_to_product_dialog(self):
        """Affiche le dialogue pour ajouter un composant à un produit"""
        # Vérifier qu'un produit est sélectionné
        current_item = self.products_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Information", "Veuillez d'abord sélectionner un produit.")
            return
        
        product_name = current_item.text()
        
        # Dialogue pour ajouter un composant au produit
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ajouter un composant à {product_name}")
        layout = QFormLayout(dialog)
        
        # Option pour choisir un composant existant ou en créer un nouveau
        choice_group = QGroupBox("Type de composant")
        choice_layout = QVBoxLayout(choice_group)
        
        existing_radio = QRadioButton("Utiliser un composant existant")
        new_radio = QRadioButton("Créer un nouveau composant")
        existing_radio.setChecked(True)
        
        choice_layout.addWidget(existing_radio)
        choice_layout.addWidget(new_radio)
        layout.addRow("", choice_group)
        
        # Widget pour la sélection d'un composant existant
        existing_widget = QWidget()
        existing_layout = QFormLayout(existing_widget)
        
        # Liste des composants existants
        component_combo = QComboBox()
        
        # Récupérer tous les noms de composants uniques
        all_components = self.inventory_controller.get_all_components()
        unique_components = sorted(list(set(comp["name"] for comp in all_components)))
        
        component_combo.addItems(unique_components)
        existing_layout.addRow("Composant:", component_combo)
        layout.addRow("", existing_widget)
        
        # Widget pour la création d'un nouveau composant
        new_widget = QWidget()
        new_layout = QFormLayout(new_widget)
        
        new_component_name = QLineEdit()
        new_layout.addRow("Nom du composant:", new_component_name)
        
        new_component_desc = QLineEdit()
        new_layout.addRow("Description (facultative):", new_component_desc)
        
        new_widget.setEnabled(False)
        layout.addRow("", new_widget)
        
        # Connecter les boutons radio pour activer/désactiver les widgets
        existing_radio.toggled.connect(lambda checked: existing_widget.setEnabled(checked))
        new_radio.toggled.connect(lambda checked: new_widget.setEnabled(checked))
        
        # Quantité
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(1)
        quantity_spin.setMaximum(100)
        quantity_spin.setValue(1)
        layout.addRow("Quantité:", quantity_spin)
        
        # Contrainte de couleur
        constraint_group = QGroupBox("Contrainte de couleur")
        constraint_layout = QVBoxLayout(constraint_group)
        
        # Options pour la contrainte de couleur
        no_constraint_radio = QRadioButton("Aucune contrainte")
        same_as_main_radio = QRadioButton("Même couleur que le produit")
        fixed_color_radio = QRadioButton("Couleur fixe")
        same_as_other_radio = QRadioButton("Même couleur qu'un autre composant")
        
        # Sélectionner par défaut
        no_constraint_radio.setChecked(True)
        
        constraint_layout.addWidget(no_constraint_radio)
        constraint_layout.addWidget(same_as_main_radio)
        constraint_layout.addWidget(fixed_color_radio)
        constraint_layout.addWidget(same_as_other_radio)
        
        # Options supplémentaires pour les contraintes
        fixed_color_combo = QComboBox()
        fixed_color_combo.addItems(sorted([c for c in COLORS if c != "Aléatoire"]))
        fixed_color_combo.setEnabled(False)
        
        fixed_color_layout = QHBoxLayout()
        fixed_color_layout.addWidget(QLabel("Couleur:"))
        fixed_color_layout.addWidget(fixed_color_combo)
        constraint_layout.addLayout(fixed_color_layout)
        
        # Référence à un autre composant
        ref_combo = QComboBox()
        ref_combo.setEnabled(False)
        
        # Récupérer les composants du produit sélectionné
        product = current_item.data(Qt.UserRole)
        for comp in product["components"]:
            ref_combo.addItem(comp["name"])
        
        ref_layout = QHBoxLayout()
        ref_layout.addWidget(QLabel("Référence:"))
        ref_layout.addWidget(ref_combo)
        constraint_layout.addLayout(ref_layout)
        
        # Activer/désactiver les options en fonction de la sélection
        fixed_color_radio.toggled.connect(lambda checked: fixed_color_combo.setEnabled(checked))
        same_as_other_radio.toggled.connect(lambda checked: ref_combo.setEnabled(checked))
        
        layout.addRow("", constraint_group)
        
        # Boutons
        buttons = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        add_btn = QPushButton("Ajouter")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        
        buttons.addWidget(cancel_btn)
        buttons.addWidget(add_btn)
        layout.addRow("", buttons)
        
        # Afficher le dialogue
        if dialog.exec_() == QDialog.Accepted:
            # Déterminer le nom du composant selon le choix de l'utilisateur
            if existing_radio.isChecked():
                component_name = component_combo.currentText()
            else:
                component_name = new_component_name.text().strip()
                
                # Si l'utilisateur a choisi de créer un nouveau composant
                if component_name:
                    component_description = new_component_desc.text().strip()
                    # Créer le nouveau composant (avec un stock initial de 0)
                    success = self.inventory_controller.add_new_component(component_name, {}, component_description)
                    
                    if not success:
                        QMessageBox.warning(self, "Erreur", f"Impossible de créer le composant {component_name}.")
                        return
                else:
                    QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")
                    return
            
            quantity = quantity_spin.value()
            
            # Déterminer la contrainte de couleur
            color_constraint = None
            
            if same_as_main_radio.isChecked():
                color_constraint = "same_as_main"
            elif fixed_color_radio.isChecked():
                color_constraint = f"fixed:{fixed_color_combo.currentText()}"
            elif same_as_other_radio.isChecked():
                ref_component = ref_combo.currentText()
                if ref_component:
                    color_constraint = f"same_as:{ref_component}"
            
            # Ajouter le composant au produit
            success = self.inventory_controller.add_component_to_product(
                product_name, component_name, quantity, color_constraint)
            
            if not success:
                QMessageBox.warning(self, "Erreur", 
                                   f"Impossible d'ajouter {component_name} au produit {product_name}.")
            else:
                # Mettre à jour les données
                self.load_data()
                QMessageBox.information(self, "Succès", f"Composant '{component_name}' ajouté au produit '{product_name}'.")
    
    def remove_component_from_product(self):
        """Retire un composant d'un produit"""
        # Vérifier qu'un produit et un composant sont sélectionnés
        current_product = self.products_list.currentItem()
        if not current_product:
            return
        
        product_name = current_product.text()
        
        # Vérifier si une ligne est sélectionnée dans le tableau des composants
        current_row = self.components_detail_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Information", 
                                   "Veuillez sélectionner un composant à retirer.")
            return
        
        component_name = self.components_detail_table.item(current_row, 0).text()
        
        # Confirmation
        if QMessageBox.question(self, "Confirmer le retrait", 
                              f"Êtes-vous sûr de vouloir retirer le composant '{component_name}' du produit '{product_name}' ?",
                              QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        
        # Retirer le composant
        success = self.inventory_controller.remove_component_from_product(product_name, component_name)
        
        if not success:
            QMessageBox.warning(self, "Erreur", 
                               f"Impossible de retirer {component_name} du produit {product_name}.")
        else:
            # Mettre à jour les données
            self.load_data()
    
    def count_components(self):
        """Compte le nombre total de composants en stock"""
        components = self.inventory_controller.get_all_components()
        return sum(comp["stock"] for comp in components)
    
    def count_products(self):
        """Compte le nombre total de produits assemblés"""
        products = self.inventory_controller.get_all_products()
        return sum(sum(p["assembled_stock"].values()) for p in products)