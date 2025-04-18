# views/inventory_view.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QScrollArea, QPushButton, QSizePolicy,
                           QGridLayout, QSpacerItem, QTabWidget, QTableWidget,
                           QTableWidgetItem, QComboBox, QSpinBox, QHeaderView,
                           QDialog, QFormLayout, QLineEdit, QColorDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter
from controllers.inventory_controller import InventoryController
from models.inventory import InventoryItem, ColorVariant, ProductComponent
from config import COLORS, PRODUCTS, UI_COLORS

class InventoryWidget(QWidget):
    """Widget principal pour la gestion de l'inventaire"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.inventory_controller = InventoryController()
        
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
        
        # Onglet de l'inventaire principal
        self.inventory_tab = QWidget()
        self.setup_inventory_tab()
        self.tab_widget.addTab(self.inventory_tab, "Inventaire")
        
        # Onglet pour les composants
        self.components_tab = QWidget()
        self.setup_components_tab()
        self.tab_widget.addTab(self.components_tab, "Composants")
        
        # Onglet pour les variantes de couleurs
        self.colors_tab = QWidget()
        self.setup_colors_tab()
        self.tab_widget.addTab(self.colors_tab, "Variantes de couleurs")
        
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
    
    def setup_inventory_tab(self):
        """Configure l'onglet principal de l'inventaire"""
        layout = QVBoxLayout(self.inventory_tab)
        
        # Tableau de l'inventaire
        self.inventory_table = QTableWidget(0, 6)
        self.inventory_table.setHorizontalHeaderLabels([
            "Produit", "Couleur", "Composant", "Stock", "Seuil d'alerte", "Actions"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inventory_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.inventory_table)
        
        # Boutons d'action pour l'inventaire
        action_layout = QHBoxLayout()
        
        add_btn = QPushButton("Ajouter stock")
        add_btn.clicked.connect(self.add_stock_dialog)
        
        update_threshold_btn = QPushButton("Modifier seuil")
        update_threshold_btn.clicked.connect(self.update_threshold_dialog)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrer par produit:"))
        
        self.product_filter = QComboBox()
        self.product_filter.addItem("Tous")
        self.product_filter.addItems(PRODUCTS)
        self.product_filter.currentTextChanged.connect(self.apply_filters)
        
        self.show_components_check = QComboBox()
        self.show_components_check.addItem("Tous les items")
        self.show_components_check.addItem("Produits finis uniquement")
        self.show_components_check.addItem("Composants uniquement")
        self.show_components_check.currentTextChanged.connect(self.apply_filters)
        
        filter_layout.addWidget(self.product_filter)
        filter_layout.addWidget(QLabel("Afficher:"))
        filter_layout.addWidget(self.show_components_check)
        filter_layout.addStretch()
        
        action_layout.addLayout(filter_layout)
        action_layout.addStretch()
        action_layout.addWidget(add_btn)
        action_layout.addWidget(update_threshold_btn)
        
        layout.addLayout(action_layout)
    
    def setup_components_tab(self):
        """Configure l'onglet des composants"""
        layout = QVBoxLayout(self.components_tab)
        
        # Tableau des relations produits-composants
        self.components_table = QTableWidget(0, 4)
        self.components_table.setHorizontalHeaderLabels([
            "Produit", "Composant", "Quantité", "Actions"
        ])
        self.components_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.components_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.components_table)
        
        # Boutons d'action pour les composants
        action_layout = QHBoxLayout()
        
        add_component_btn = QPushButton("Ajouter composant")
        add_component_btn.clicked.connect(self.add_component_dialog)
        
        action_layout.addStretch()
        action_layout.addWidget(add_component_btn)
        
        layout.addLayout(action_layout)
    
    def setup_colors_tab(self):
        """Configure l'onglet des variantes de couleurs"""
        layout = QVBoxLayout(self.colors_tab)
        
        # Tableau des variantes de couleurs
        self.colors_table = QTableWidget(0, 4)
        self.colors_table.setHorizontalHeaderLabels([
            "Couleur de base", "Variante", "Code couleur", "Actions"
        ])
        self.colors_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.colors_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.colors_table)
        
        # Boutons d'action pour les variantes de couleurs
        action_layout = QHBoxLayout()
        
        add_variant_btn = QPushButton("Ajouter variante")
        add_variant_btn.clicked.connect(self.add_color_variant_dialog)
        
        action_layout.addStretch()
        action_layout.addWidget(add_variant_btn)
        
        layout.addLayout(action_layout)
    
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
        
        # Tableau des prévisions
        self.forecast_table = QTableWidget(0, 7)
        self.forecast_table.setHorizontalHeaderLabels([
            "Produit", "Couleur", "Composant", "Stock actuel", 
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
        """Charge les données dans tous les onglets"""
        self.load_inventory_data()
        self.load_components_data()
        self.load_color_variants_data()
        self.load_forecast_data()
    
    def load_inventory_data(self):
        """Charge les données de l'inventaire dans le tableau"""
        # Détermine s'il faut inclure les composants
        include_components = True
        if self.show_components_check.currentText() == "Produits finis uniquement":
            include_components = False
        
        # Filtrer par produit si nécessaire
        filtered_product = None
        if self.product_filter.currentText() != "Tous":
            filtered_product = self.product_filter.currentText()
        
        # Récupérer les données de l'inventaire
        inventory = self.inventory_controller.get_inventory_with_print_needs(include_components)
        
        # Filtrer les données si nécessaire
        filtered_inventory = []
        for item in inventory:
            if filtered_product and item['product'] != filtered_product:
                continue
                
            if self.show_components_check.currentText() == "Composants uniquement" and not item['component']:
                continue
                
            filtered_inventory.append(item)
        
        # Mettre à jour le tableau
        self.inventory_table.setRowCount(0)
        self.inventory_table.setRowCount(len(filtered_inventory))
        
        for row, item in enumerate(filtered_inventory):
            # Produit
            self.inventory_table.setItem(row, 0, QTableWidgetItem(item['product']))
            
            # Couleur
            self.inventory_table.setItem(row, 1, QTableWidgetItem(item['color']))
            
            # Composant
            component = item['component'] if item['component'] else "-"
            self.inventory_table.setItem(row, 2, QTableWidgetItem(component))
            
            # Stock
            stock_item = QTableWidgetItem(str(item['stock']))
            if item['status'] == 'Low':
                stock_item.setBackground(QColor('#FFDDDD'))
            self.inventory_table.setItem(row, 3, stock_item)
            
            # Seuil d'alerte
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(item['alert_threshold'])))
            
            # Actions - Boutons pour ajuster le stock
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            add_btn = QPushButton("+")
            add_btn.setMaximumWidth(30)
            add_btn.clicked.connect(lambda _, p=item['product'], c=item['color'], comp=item['component']: 
                                   self.quick_add_stock(p, c, comp))
            
            sub_btn = QPushButton("-")
            sub_btn.setMaximumWidth(30)
            sub_btn.clicked.connect(lambda _, p=item['product'], c=item['color'], comp=item['component']: 
                                   self.quick_remove_stock(p, c, comp))
            
            actions_layout.addWidget(add_btn)
            actions_layout.addWidget(sub_btn)
            actions_layout.addStretch()
            
            self.inventory_table.setCellWidget(row, 5, actions_widget)
    
    def load_components_data(self):
        """Charge les données des composants dans le tableau"""
        # Récupérer tous les produits qui ont des composants
        component_products = []
        
        for product in PRODUCTS:
            components = self.inventory_controller.get_product_components(product)
            if components:
                for component in components:
                    component_products.append({
                        'product': product,
                        'component': component['name'],
                        'quantity': component['quantity']
                    })
        
        # Mettre à jour le tableau
        self.components_table.setRowCount(0)
        self.components_table.setRowCount(len(component_products))
        
        for row, item in enumerate(component_products):
            # Produit
            self.components_table.setItem(row, 0, QTableWidgetItem(item['product']))
            
            # Composant
            self.components_table.setItem(row, 1, QTableWidgetItem(item['component']))
            
            # Quantité
            self.components_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
            
            # Actions - Bouton pour supprimer le composant
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, p=item['product'], c=item['component']: 
                                      self.remove_component(p, c))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.components_table.setCellWidget(row, 3, actions_widget)
    
    def load_color_variants_data(self):
        """Charge les données des variantes de couleurs dans le tableau"""
        color_variants = self.inventory_controller.get_color_variants()
        
        # Mettre à jour le tableau
        self.colors_table.setRowCount(0)
        self.colors_table.setRowCount(len(color_variants))
        
        for row, variant in enumerate(color_variants):
            # Couleur de base
            self.colors_table.setItem(row, 0, QTableWidgetItem(variant['base_color']))
            
            # Nom de la variante
            self.colors_table.setItem(row, 1, QTableWidgetItem(variant['variant_name']))
            
            # Code couleur avec aperçu visuel
            color_item = QTableWidgetItem(variant['hex_code'])
            color_item.setBackground(QColor(variant['hex_code']))
            self.colors_table.setItem(row, 2, color_item)
            
            # Actions - Bouton pour supprimer la variante
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            delete_btn = QPushButton("Supprimer")
            delete_btn.clicked.connect(lambda _, v=variant['variant_name']: 
                                      self.remove_color_variant(v))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.colors_table.setCellWidget(row, 3, actions_widget)
    
    def load_forecast_data(self):
        """Charge les données de prévisions dans le tableau"""
        forecasts = self.inventory_controller.get_inventory_with_forecast()
        
        # Mettre à jour le tableau
        self.forecast_table.setRowCount(0)
        self.forecast_table.setRowCount(len(forecasts))
        
        for row, item in enumerate(forecasts):
            # Produit
            self.forecast_table.setItem(row, 0, QTableWidgetItem(item['product']))
            
            # Couleur
            self.forecast_table.setItem(row, 1, QTableWidgetItem(item['color']))
            
            # Composant
            component = item['component'] if item['component'] else "-"
            self.forecast_table.setItem(row, 2, QTableWidgetItem(component))
            
            # Stock actuel
            stock_item = QTableWidgetItem(str(item['stock']))
            if item['status'] == 'Low' or item['status'] == 'Below Forecast':
                stock_item.setBackground(QColor('#FFDDDD'))
            self.forecast_table.setItem(row, 3, stock_item)
            
            # Ventes mensuelles moyennes
            sales = round(item['avg_monthly_sales'], 2)
            self.forecast_table.setItem(row, 4, QTableWidgetItem(str(sales)))
            
            # Stock recommandé
            self.forecast_table.setItem(row, 5, QTableWidgetItem(str(item['forecast_stock'])))
            
            # Tendance (facteur)
            trend_item = QTableWidgetItem(f"{item['trend_factor']:.2f}x")
            if item['trend_factor'] > 1:
                trend_item.setBackground(QColor('#DDFFDD'))
            elif item['trend_factor'] < 1:
                trend_item.setBackground(QColor('#FFDDDD'))
            self.forecast_table.setItem(row, 6, trend_item)
    
    def apply_filters(self):
        """Applique les filtres à l'inventaire"""
        self.load_inventory_data()
    
    def quick_add_stock(self, product, color, component):
        """Ajoute rapidement 1 au stock"""
        self.inventory_controller.adjust_stock(product, color, 1, component)
        self.load_inventory_data()
    
    def quick_remove_stock(self, product, color, component):
        """Retire rapidement 1 du stock"""
        self.inventory_controller.adjust_stock(product, color, -1, component)
        self.load_inventory_data()
    
    def add_stock_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter du stock"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter du stock")
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
        
        # Sélection du composant (optionnel)
        component_combo = QComboBox()
        component_combo.addItem("Produit fini")
        
        def update_components():
            # Mettre à jour la liste des composants en fonction du produit sélectionné
            product = product_combo.currentText()
            component_combo.clear()
            component_combo.addItem("Produit fini")
            
            components = self.inventory_controller.get_product_components(product)
            if components:
                for comp in components:
                    component_combo.addItem(comp['name'])
        
        product_combo.currentTextChanged.connect(update_components)
        update_components()  # Initialiser les composants
        
        layout.addRow("Composant:", component_combo)
        
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
            component_text = component_combo.currentText()
            component = None if component_text == "Produit fini" else component_text
            quantity = quantity_spin.value()
            
            self.inventory_controller.adjust_stock(product, color, quantity, component)
            self.load_inventory_data()
    
    def update_threshold_dialog(self):
        """Ouvre une boîte de dialogue pour modifier le seuil d'alerte"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Modifier le seuil d'alerte")
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
        
        # Sélection du composant (optionnel)
        component_combo = QComboBox()
        component_combo.addItem("Produit fini")
        
        def update_components():
            # Mettre à jour la liste des composants en fonction du produit sélectionné
            product = product_combo.currentText()
            component_combo.clear()
            component_combo.addItem("Produit fini")
            
            components = self.inventory_controller.get_product_components(product)
            if components:
                for comp in components:
                    component_combo.addItem(comp['name'])
        
        product_combo.currentTextChanged.connect(update_components)
        update_components()  # Initialiser les composants
        
        layout.addRow("Composant:", component_combo)
        
        # Nouveau seuil
        threshold_spin = QSpinBox()
        threshold_spin.setRange(1, 100)
        threshold_spin.setValue(3)
        layout.addRow("Nouveau seuil:", threshold_spin)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        
        update_btn = QPushButton("Mettre à jour")
        update_btn.clicked.connect(dialog.accept)
        update_btn.setDefault(True)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(update_btn)
        
        layout.addRow("", buttons_layout)
        
        if dialog.exec_() == QDialog.Accepted:
            product = product_combo.currentText()
            color = color_combo.currentText()
            component_text = component_combo.currentText()
            component = None if component_text == "Produit fini" else component_text
            threshold = threshold_spin.value()
            
            self.inventory_controller.update_alert_threshold(product, color, threshold, component)
            self.load_inventory_data()
    
    def add_component_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter un composant à un produit"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter un composant")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Sélection du produit
        product_combo = QComboBox()
        product_combo.addItems(PRODUCTS)
        layout.addRow("Produit:", product_combo)
        
        # Nom du composant
        component_edit = QLineEdit()
        layout.addRow("Nom du composant:", component_edit)
        
        # Quantité nécessaire
        quantity_spin = QSpinBox()
        quantity_spin.setRange(1, 10)
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
            component = component_edit.text()
            quantity = quantity_spin.value()
            
            if component:
                self.inventory_controller.add_product_component(product, component, quantity)
                self.load_components_data()
                self.load_inventory_data()
            else:
                QMessageBox.warning(self, "Erreur", "Le nom du composant ne peut pas être vide.")
    
    def remove_component(self, product, component):
        """Supprime un composant d'un produit"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le composant '{component}' du produit '{product}'?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.inventory_controller.remove_product_component(product, component)
            self.load_components_data()
            self.load_inventory_data()
    
    def add_color_variant_dialog(self):
        """Ouvre une boîte de dialogue pour ajouter une variante de couleur"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter une variante de couleur")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout(dialog)
        
        # Couleur de base
        base_color_combo = QComboBox()
        base_color_combo.addItems([c for c in COLORS if c != "Aléatoire"])
        layout.addRow("Couleur de base:", base_color_combo)
        
        # Nom de la variante
        variant_edit = QLineEdit()
        layout.addRow("Nom de la variante:", variant_edit)
        
        # Code couleur hexadécimal
        color_layout = QHBoxLayout()
        color_edit = QLineEdit("#000000")
        color_btn = QPushButton("Sélectionner")
        
        def select_color():
            color = QColorDialog.getColor(QColor(color_edit.text()), dialog)
            if color.isValid():
                color_edit.setText(color.name())
        
        color_btn.clicked.connect(select_color)
        
        color_layout.addWidget(color_edit)
        color_layout.addWidget(color_btn)
        
        layout.addRow("Code couleur:", color_layout)
        
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
            base_color = base_color_combo.currentText()
            variant_name = variant_edit.text()
            hex_code = color_edit.text()
            
            if variant_name:
                self.inventory_controller.add_color_variant(base_color, variant_name, hex_code)
                self.load_color_variants_data()
            else:
                QMessageBox.warning(self, "Erreur", "Le nom de la variante ne peut pas être vide.")
    
    def remove_color_variant(self, variant_name):
        """Supprime une variante de couleur"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer la variante de couleur '{variant_name}'?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.inventory_controller.remove_color_variant(variant_name)
            self.load_color_variants_data()
    
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