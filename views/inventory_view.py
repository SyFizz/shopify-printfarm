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
                comp_name = component["name"]
                
                # Vérifier si le composant a une contrainte de couleur
                if "color_constraint" in component:
                    constraint = component["color_constraint"]
                    
                    # Si la contrainte est déjà fixée, afficher uniquement l'information
                    if constraint.startswith("fixed:") or constraint == "same_as_main" or constraint.startswith("same_as:"):
                        label = QLabel(f"<i>{self.get_constraint_description(constraint)}</i>")
                        label.setStyleSheet("color: #666;")
                        component_layout.addRow(f"{comp_name}:", label)
                    else:
                        # Permettre une sélection personnalisée
                        color_combo = QComboBox()
                        for color in sorted(COLORS):
                            if color != "Aléatoire":  # Ne pas inclure "Aléatoire" dans les options de composants
                                color_combo.addItem(color)
                        
                        component_layout.addRow(f"{comp_name}:", color_combo)
                        
                        # Stocker le combo pour référence ultérieure
                        self.component_colors[comp_name] = color_combo
            
            layout.addWidget(component_group)
        
        # Quantité à assembler
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Quantité à assembler:"))
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(100)  # Ajuster selon les besoins
        self.quantity_spin.setValue(1)
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
                    comp_color = display_color
                elif constraint.startswith("fixed:"):
                    comp_color = constraint.split(":", 1)[1]
                elif constraint.startswith("same_as:"):
                    ref_component = constraint.split(":", 1)[1]
                    # Pour simplifier, utiliser display_color pour l'instant
                    comp_color = display_color
                elif comp_name in self.component_colors:
                    # Utiliser la couleur sélectionnée manuellement
                    comp_color = self.component_colors[comp_name].currentText()
            
            required_components.append({
                "name": comp_name,
                "color": comp_color,
                "quantity": quantity
            })
        
        # Mettre à jour le tableau des composants
        self.components_table.setRowCount(len(required_components))
        
        for row, comp in enumerate(required_components):
            # Composant
            self.components_table.setItem(row, 0, QTableWidgetItem(comp["name"]))
            
            # Couleur
            color_item = QTableWidgetItem(comp["color"])
            color_item.setBackground(QColor(COLOR_HEX_MAP.get(comp["color"], "#CCCCCC")))
            self.components_table.setItem(row, 1, color_item)
            
            # Quantité requise
            self.components_table.setItem(row, 2, QTableWidgetItem(str(comp["quantity"])))
            
            # Disponible (à implémenter avec les données réelles)
            self.components_table.setItem(row, 3, QTableWidgetItem("..."))
        
        # Redimensionner les lignes pour un meilleur affichage
        self.components_table.resizeRowsToContents()

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
        
        filters_layout.addStretch()
        
        # Bouton pour ajouter un nouveau composant
        add_component_btn = QPushButton("Nouveau composant")
        add_component_btn.setIcon(self.style().standardIcon(self.style().SP_FileIcon))
        add_component_btn.clicked.connect(self.add_new_component_dialog)
        filters_layout.addWidget(add_component_btn)
        
        layout.addLayout(filters_layout)
        
        # Tableau des composants
        self.components_table = QTableWidget()
        self.components_table.setColumnCount(5)
        self.components_table.setHorizontalHeaderLabels(
            ["Composant", "Couleur", "Stock", "Seuil d'alerte", "Actions"]
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
        
        # Appliquer les filtres actuels
        self.apply_component_filters()
    
    def apply_component_filters(self):
        """Applique les filtres sur le tableau des composants"""
        # Récupérer les critères de filtre
        component_filter = self.component_filter.currentText()
        color_filter = self.color_filter.currentText()
        
        # Récupérer toutes les données
        all_components = self.inventory_controller.get_all_components()
        
        # Appliquer les filtres
        filtered_components = []
        for comp in all_components:
            if component_filter != "Tous" and comp["name"] != component_filter:
                continue
            if color_filter != "Toutes" and comp["color"] != color_filter:
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
            
            # Stock
            stock_item = QTableWidgetItem(str(comp["stock"]))
            if comp["stock"] <= comp["alert_threshold"]:
                stock_item.setBackground(QColor("#FFCCCC"))  # Rouge clair pour le stock bas
            self.components_table.setItem(row, 2, stock_item)
            
            # Seuil d'alerte
            self.components_table.setItem(row, 3, QTableWidgetItem(str(comp["alert_threshold"])))
            
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
            
            self.components_table.setCellWidget(row, 4, actions_widget)
        
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