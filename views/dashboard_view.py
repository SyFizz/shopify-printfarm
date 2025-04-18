# views/dashboard_view.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QFrame, QScrollArea, QPushButton, QSizePolicy,
                           QGridLayout, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from controllers.order_controller import OrderController
from controllers.print_controller import PrintController
from controllers.inventory_controller import InventoryController
from utils.stats_manager import StatsManager
from utils.helpers import format_date
from config import COLOR_HEX_MAP, UI_COLORS

class DashboardWidget(QWidget):
    """Widget principal pour le tableau de bord"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.order_controller = OrderController()
        self.print_controller = PrintController()
        self.inventory_controller = InventoryController()
        self.stats_manager = StatsManager()
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Configure l'interface utilisateur du tableau de bord"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Titre du tableau de bord
        title_label = QLabel("Tableau de bord")
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {UI_COLORS['primary']};")
        main_layout.addWidget(title_label)
        
        # Zone de défilement pour le contenu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Widget de contenu pour le défilement
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # Ajouter les différentes sections du tableau de bord
        scroll_layout.addLayout(self.create_summary_section())
        scroll_layout.addLayout(self.create_printing_section())
        
        # Section des graphiques - utiliser un layout horizontal
        charts_section = self.create_charts_section()
        scroll_layout.addLayout(charts_section)
        
        scroll_layout.addLayout(self.create_low_stock_section())
        
        # Ajouter un espace extensible à la fin
        scroll_layout.addStretch()
        
        # Configurer la zone de défilement
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Bouton de rafraîchissement
        refresh_button = QPushButton("Actualiser le tableau de bord")
        refresh_button.setIcon(self.style().standardIcon(self.style().SP_BrowserReload))
        refresh_button.clicked.connect(self.load_data)
        main_layout.addWidget(refresh_button)
    
    def create_summary_section(self):
        """Crée la section de résumé avec les tuiles de statistiques"""
        summary_layout = QVBoxLayout()
        
        # Titre de la section
        section_title = QLabel("Aperçu général")
        section_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        summary_layout.addWidget(section_title)
        
        # Conteneur pour les tuiles - utiliser un layout en grille pour un meilleur contrôle
        tiles_layout = QGridLayout()
        tiles_layout.setSpacing(10)
        
        # Tuiles d'informations
        self.orders_tile = self.create_info_tile("Commandes en attente", "0", "red")
        self.printing_tile = self.create_info_tile("En cours d'impression", "0", "orange")
        self.ready_tile = self.create_info_tile("Prêtes à expédier", "0", "green")
        self.print_needed_tile = self.create_info_tile("À imprimer", "0", "blue")
        
        # Ajouter les tuiles à la grille
        tiles_layout.addWidget(self.orders_tile, 0, 0)
        tiles_layout.addWidget(self.printing_tile, 0, 1)
        tiles_layout.addWidget(self.ready_tile, 0, 2)
        tiles_layout.addWidget(self.print_needed_tile, 0, 3)
        
        summary_layout.addLayout(tiles_layout)
        
        return summary_layout
    
    def create_printing_section(self):
        """Crée la section sur l'état d'impression"""
        printing_layout = QVBoxLayout()
        
        # Titre de la section
        section_title = QLabel("Priorités d'impression")
        section_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        printing_layout.addWidget(section_title)
        
        # Tableau des couleurs prioritaires
        colors_frame = QFrame()
        colors_frame.setFrameShape(QFrame.StyledPanel)
        colors_frame.setStyleSheet("background-color: white; border-radius: 5px; padding: 10px;")
        
        colors_layout = QVBoxLayout(colors_frame)
        
        # En-tête avec une mise en page de grille
        header_layout = QGridLayout()
        header_layout.addWidget(QLabel("Couleur"), 0, 0, 1, 3)
        header_layout.addWidget(QLabel("Produits"), 0, 3, 1, 1)
        header_layout.addWidget(QLabel("Quantité"), 0, 4, 1, 1)
        colors_layout.addLayout(header_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        colors_layout.addWidget(separator)
        
        # Conteneur pour les lignes de couleurs (à remplir dynamiquement)
        self.colors_container = QVBoxLayout()
        colors_layout.addLayout(self.colors_container)
        
        printing_layout.addWidget(colors_frame)
        
        return printing_layout
    
    def create_charts_section(self):
        """Crée la section avec les graphiques"""
        charts_layout = QVBoxLayout()
        
        # Titre de la section
        section_title = QLabel("Statistiques")
        section_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        charts_layout.addWidget(section_title)
        
        # Conteneur pour les graphiques - utiliser QGridLayout
        charts_grid = QGridLayout()
        charts_grid.setSpacing(10)
        
        # Graphique des produits
        self.products_chart_view = QChartView()
        self.products_chart_view.setRenderHint(QPainter.Antialiasing)
        self.products_chart_view.setMinimumHeight(250)
        self.products_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        products_frame = self.create_chart_frame("Produits les plus populaires", self.products_chart_view)
        
        # Graphique des couleurs
        self.colors_chart_view = QChartView()
        self.colors_chart_view.setRenderHint(QPainter.Antialiasing)
        self.colors_chart_view.setMinimumHeight(250)
        self.colors_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        colors_frame = self.create_chart_frame("Couleurs les plus demandées", self.colors_chart_view)
        
        # Ajouter les graphiques à la grille
        charts_grid.addWidget(products_frame, 0, 0)
        charts_grid.addWidget(colors_frame, 0, 1)
        
        charts_layout.addLayout(charts_grid)
        
        return charts_layout
    
    def create_low_stock_section(self):
        """Crée la section des produits en stock bas"""
        low_stock_layout = QVBoxLayout()
        
        # Titre de la section
        section_title = QLabel("Produits en rupture de stock")
        section_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        low_stock_layout.addWidget(section_title)
        
        # Tableau des produits en rupture de stock
        stock_frame = QFrame()
        stock_frame.setFrameShape(QFrame.StyledPanel)
        stock_frame.setStyleSheet("background-color: white; border-radius: 5px; padding: 10px;")
        
        stock_layout = QVBoxLayout(stock_frame)
        stock_layout.setSpacing(10)
        
        # En-tête avec une mise en page de grille
        header_layout = QGridLayout()
        header_layout.addWidget(QLabel("Produit"), 0, 0, 1, 3)
        header_layout.addWidget(QLabel("Couleur"), 0, 3, 1, 2)
        header_layout.addWidget(QLabel("Stock"), 0, 5, 1, 1)
        header_layout.addWidget(QLabel("Seuil d'alerte"), 0, 6, 1, 1)
        stock_layout.addLayout(header_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        stock_layout.addWidget(separator)
        
        # Conteneur pour les lignes de produits (à remplir dynamiquement)
        self.stock_container = QVBoxLayout()
        stock_layout.addLayout(self.stock_container)
        
        low_stock_layout.addWidget(stock_frame)
        
        return low_stock_layout
    
    def create_info_tile(self, title, value, color):
        """Crée une tuile d'information avec titre et valeur"""
        tile = QFrame()
        tile.setFrameShape(QFrame.StyledPanel)
        tile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tile.setMinimumHeight(100)
        tile.setMaximumHeight(120)  # Limiter la hauteur maximum
        
        # Appliquer un style à la tuile
        if color == "red":
            color_code = UI_COLORS["danger"]
        elif color == "orange":
            color_code = UI_COLORS["warning"]
        elif color == "green":
            color_code = UI_COLORS["success"]
        else:
            color_code = UI_COLORS["info"]
        
        tile.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 5px solid {color_code};
                border-radius: 5px;
                padding: 10px;
            }}
        """)
        
        # Layout pour le contenu de la tuile
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #555;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Valeur
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignRight)
        layout.addWidget(value_label)
        
        # Stocker le label de la valeur pour pouvoir le mettre à jour
        tile.value_label = value_label
        
        return tile
    
    def create_chart_frame(self, title, chart_view):
        """Crée un cadre contenant un graphique avec titre"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("background-color: white; border-radius: 5px; padding: 10px;")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(frame)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Graphique
        layout.addWidget(chart_view)
        
        return frame
    
    def update_color_row(self, color, product_count, total_quantity):
        """Crée ou met à jour une ligne dans le tableau des couleurs prioritaires"""
        # Créer le widget de ligne
        row_widget = QWidget()
        row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Utiliser un layout en grille pour un meilleur contrôle
        row_layout = QGridLayout(row_widget)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setHorizontalSpacing(10)
        
        # Carré de couleur
        color_indicator = QFrame()
        color_indicator.setFixedSize(16, 16)
        color_indicator.setStyleSheet(f"background-color: {COLOR_HEX_MAP.get(color, '#CCCCCC')}; border: 1px solid #999;")
        row_layout.addWidget(color_indicator, 0, 0)
        
        # Nom de la couleur
        color_label = QLabel(color)
        row_layout.addWidget(color_label, 0, 1, 1, 2)
        
        # Nombre de produits
        product_label = QLabel(str(product_count))
        product_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(product_label, 0, 3)
        
        # Quantité totale
        quantity_label = QLabel(str(total_quantity))
        quantity_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(quantity_label, 0, 4)
        
        return row_widget
    
    def update_stock_row(self, product, color, stock, alert_threshold):
        """Crée une ligne dans le tableau des produits en rupture de stock"""
        # Créer le widget de ligne
        row_widget = QWidget()
        row_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Utiliser un layout en grille pour un meilleur contrôle
        row_layout = QGridLayout(row_widget)
        row_layout.setContentsMargins(0, 5, 0, 5)
        row_layout.setHorizontalSpacing(10)
        
        # Produit
        product_label = QLabel(product)
        row_layout.addWidget(product_label, 0, 0, 1, 3)
        
        # Carré de couleur
        color_indicator = QFrame()
        color_indicator.setFixedSize(16, 16)
        color_indicator.setStyleSheet(f"background-color: {COLOR_HEX_MAP.get(color, '#CCCCCC')}; border: 1px solid #999;")
        row_layout.addWidget(color_indicator, 0, 3)
        
        # Nom de la couleur
        color_label = QLabel(color)
        row_layout.addWidget(color_label, 0, 4)
        
        # Stock
        stock_label = QLabel(str(stock))
        stock_label.setAlignment(Qt.AlignCenter)
        # Mettre en rouge si stock < seuil d'alerte
        if stock < alert_threshold:
            stock_label.setStyleSheet("color: red; font-weight: bold;")
        row_layout.addWidget(stock_label, 0, 5)
        
        # Seuil d'alerte
        alert_label = QLabel(str(alert_threshold))
        alert_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(alert_label, 0, 6)
        
        return row_widget
    
    def create_products_chart(self, popular_products):
        """Crée un graphique en barres des produits les plus populaires"""
        # Créer le graphique
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("")
        
        # Vérifier si la liste est vide
        if not popular_products:
            # Créer un graphique vide avec un message
            no_data_series = QBarSeries()
            chart.addSeries(no_data_series)
            
            # Axes vides
            axis_x = QBarCategoryAxis()
            axis_x.append(["Aucune donnée"])
            chart.addAxis(axis_x, Qt.AlignBottom)
            no_data_series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            axis_y.setRange(0, 10)
            chart.addAxis(axis_y, Qt.AlignLeft)
            no_data_series.attachAxis(axis_y)
            
            self.products_chart_view.setChart(chart)
            return
        
        # Créer la série de données
        bar_set = QBarSet("Quantité")
        
        # Ajouter les données
        categories = []
        for product in popular_products:
            bar_set.append(product["total"])
            categories.append(product["product"])
        
        # Créer la série de barres
        series = QBarSeries()
        series.append(bar_set)
        
        # Ajouter la série au graphique
        chart.addSeries(series)
        
        # Créer l'axe des catégories
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        # Créer l'axe des valeurs
        axis_y = QValueAxis()
        max_value = max([p["total"] for p in popular_products]) if popular_products else 10
        axis_y.setRange(0, max_value * 1.1)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Configurer le graphique
        chart.legend().setVisible(False)
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        
        # Associer le graphique à la vue
        self.products_chart_view.setChart(chart)
    
    def create_colors_chart(self, popular_colors):
        """Crée un graphique en camembert des couleurs les plus populaires"""
        # Créer le graphique
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("")
        
        # Vérifier si la liste est vide
        if not popular_colors:
            # Créer une série vide
            series = QPieSeries()
            series.append("Aucune donnée", 1)
            
            # Ajouter la série au graphique
            chart.addSeries(series)
            
            # Configurer le graphique
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignRight)
            chart.setBackgroundVisible(False)
            chart.setPlotAreaBackgroundVisible(False)
            
            # Associer le graphique à la vue
            self.colors_chart_view.setChart(chart)
            return
        
        # Créer la série de données
        series = QPieSeries()
        
        # Ajouter les données
        for color_info in popular_colors:
            color_name = color_info["color"]
            value = color_info["total"]
            
            # Ajouter le segment de camembert
            slice = series.append(color_name, value)
            
            # Définir la couleur du segment
            color_hex = COLOR_HEX_MAP.get(color_name, "#CCCCCC")
            slice.setBrush(QColor(color_hex))
            
            # Afficher le libellé
            slice.setLabelVisible()
        
        # Ajouter la série au graphique
        chart.addSeries(series)
        
        # Configurer le graphique
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.setBackgroundVisible(False)
        chart.setPlotAreaBackgroundVisible(False)
        
        # Associer le graphique à la vue
        self.colors_chart_view.setChart(chart)
    
    def load_data(self):
        """Charge les données pour le tableau de bord"""
        # Récupérer les statistiques
        dashboard_stats = self.stats_manager.get_dashboard_stats()
        
        # Mettre à jour les tuiles d'informations
        self.orders_tile.value_label.setText(str(dashboard_stats["orders"]["En attente"]))
        self.printing_tile.value_label.setText(str(dashboard_stats["orders"]["En cours"]))
        self.ready_tile.value_label.setText(str(dashboard_stats["orders"]["Prêt"]))
        self.print_needed_tile.value_label.setText(str(dashboard_stats["print"]["total_to_print"]))
        
        # Mettre à jour le tableau des couleurs prioritaires
        self.update_color_priorities(dashboard_stats["color_summary"])
        
        # Mettre à jour les graphiques
        self.create_products_chart(dashboard_stats["popular_products"])
        self.create_colors_chart(dashboard_stats["popular_colors"])
        
        # Mettre à jour le tableau des produits en rupture de stock
        self.update_low_stock_list(dashboard_stats["low_stock"])
    
    def update_color_priorities(self, color_summary):
        """Met à jour la liste des couleurs prioritaires"""
        # Effacer le contenu actuel
        self.clear_layout(self.colors_container)
        
        # Ajouter les nouvelles couleurs
        for color_info in color_summary:
            color_row = self.update_color_row(
                color_info["color"],
                color_info["product_count"],
                color_info["total_quantity"]
            )
            self.colors_container.addWidget(color_row)
        
        # Ajouter un message si aucune couleur
        if not color_summary:
            no_data = QLabel("Aucune couleur à imprimer pour le moment.")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet("color: #888; padding: 10px;")
            self.colors_container.addWidget(no_data)
    
    def update_low_stock_list(self, low_stock):
        """Met à jour la liste des produits en rupture de stock"""
        # Effacer le contenu actuel
        self.clear_layout(self.stock_container)
        
        # Ajouter les nouveaux produits
        for product in low_stock:
            # Vérifier si on utilise 'name' ou 'product' comme clé
            product_name = product.get("name", product.get("product", "Inconnu"))
            
            stock_row = self.update_stock_row(
                product_name,
                product["color"],
                product["stock"],
                product["alert_threshold"]
            )
            self.stock_container.addWidget(stock_row)
        
        # Ajouter un message si aucun produit
        if not low_stock:
            no_data = QLabel("Aucun produit en rupture de stock.")
            no_data.setAlignment(Qt.AlignCenter)
            no_data.setStyleSheet("color: #888; padding: 10px;")
            self.stock_container.addWidget(no_data)
    
    def clear_layout(self, layout):
        """Efface tous les widgets d'un layout"""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()