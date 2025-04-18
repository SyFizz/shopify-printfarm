from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, 
                           QToolBar, QStatusBar, QAction, QMenu, QMessageBox, 
                           QHBoxLayout, QPushButton, QSplitter, QTreeWidget, 
                           QTreeWidgetItem, QShortcut, QStyle, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QTimer, QSettings
from PyQt5.QtGui import QIcon, QKeySequence, QFont, QPixmap
import os
import sys
from datetime import datetime
from config import APP_NAME, APP_VERSION, RESOURCES_DIR
from views.import_dialog import ImportDialog

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Gestion des commandes")
        self.setMinimumSize(1200, 800)
        
        # Charger les préférences
        self.settings = QSettings("Plasmik3D", "Gestion")
        self.restore_settings()
        
        # Initialiser l'interface utilisateur
        self.setup_ui()
        
        # Dernière mise à jour des données
        self.last_refresh = None
        self.setup_auto_refresh()
    
    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # En-tête avec logo et titre
        self.setup_header()
        
        # Layout pour le contenu principal
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Navigation latérale et onglets
        self.setup_navigation()
        
        # Ajouter le contenu principal au layout principal
        self.main_layout.addLayout(self.content_layout)
        
        # Configuration du pied de page
        self.setup_footer()
        
        # Configuration du menu
        self.setup_menu()
        
        # Configuration de la barre d'outils
        self.setup_toolbar()
        
        # Configuration de la barre d'état
        self.setup_status_bar()
        
        # Configuration des raccourcis clavier
        self.setup_shortcuts()
    
    def setup_header(self):
        """Configure l'en-tête de l'application"""
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #f0f0f0; border-bottom: 1px solid #ddd;")
        header_widget.setFixedHeight(70)
        
        header_layout = QHBoxLayout(header_widget)
        
        # Logo (placeholder)
        logo_label = QLabel()
        # Essayer de charger un logo s'il existe
        logo_path = os.path.join(RESOURCES_DIR, "icons", "logo.png")
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            # Logo placeholder
            logo_label.setText("🖨️")
            logo_label.setStyleSheet("font-size: 40px;")
        
        logo_label.setFixedSize(70, 60)
        header_layout.addWidget(logo_label)
        
        # Titre et sous-titre
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        
        title_label = QLabel(APP_NAME)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #366092;")
        
        subtitle_label = QLabel("Système de gestion d'impression 3D")
        subtitle_label.setStyleSheet("font-size: 14px; color: #555;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
        # Boutons rapides
        quick_buttons_widget = QWidget()
        quick_buttons_layout = QHBoxLayout(quick_buttons_widget)
        
        # Bouton Actualiser
        refresh_button = QPushButton("Actualiser")
        refresh_button.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_button.clicked.connect(self.refresh_data)
        quick_buttons_layout.addWidget(refresh_button)
        
        # Bouton Importer
        import_button = QPushButton("Importer")
        import_button.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        import_button.clicked.connect(self.show_import_dialog)
        quick_buttons_layout.addWidget(import_button)
        
        header_layout.addWidget(quick_buttons_widget)
        
        self.main_layout.addWidget(header_widget)
    
    def setup_navigation(self):
        """Configure la navigation latérale et les onglets"""
        # Création du splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de navigation
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setFixedWidth(220)
        self.nav_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #ddd;
                font-size: 14px;
            }
            QTreeWidget::item {
                height: 30px;
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #366092;
                color: white;
            }
        """)
        
        # Sections de navigation
        self.dashboard_item = QTreeWidgetItem(self.nav_tree, ["Tableau de bord"])
        self.dashboard_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogInfoView))
        
        self.orders_item = QTreeWidgetItem(self.nav_tree, ["Commandes"])
        self.orders_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogListView))
        
        # Sous-sections des commandes
        QTreeWidgetItem(self.orders_item, ["Toutes les commandes"])
        QTreeWidgetItem(self.orders_item, ["En attente"])
        QTreeWidgetItem(self.orders_item, ["En cours"])
        QTreeWidgetItem(self.orders_item, ["Prêtes"])
        QTreeWidgetItem(self.orders_item, ["Expédiées"])
        
        self.print_item = QTreeWidgetItem(self.nav_tree, ["Plan d'impression"])
        self.print_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        
        self.inventory_item = QTreeWidgetItem(self.nav_tree, ["Inventaire"])
        self.inventory_item.setIcon(0, self.style().standardIcon(QStyle.SP_DriveHDIcon))
        
        self.stats_item = QTreeWidgetItem(self.nav_tree, ["Statistiques"])
        self.stats_item.setIcon(0, self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        
        # Développer toutes les sections par défaut
        self.nav_tree.expandAll()
        
        # Connecter le signal de sélection
        self.nav_tree.itemClicked.connect(self.on_nav_item_clicked)
        
        # Ajouter au splitter
        self.splitter.addWidget(self.nav_tree)
        
        # Widget d'onglets
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        # Ajouter au splitter
        self.splitter.addWidget(self.tabs)
        
        # Définir les tailles initiales du splitter
        self.splitter.setSizes([220, 980])
        
        # Ajouter le splitter au layout
        self.content_layout.addWidget(self.splitter)
        
        # Ajouter l'onglet du tableau de bord par défaut
        self.open_dashboard()
    
    def setup_footer(self):
        """Configure le pied de page avec des informations sur l'application"""
        footer_widget = QWidget()
        footer_widget.setStyleSheet("background-color: #f0f0f0; border-top: 1px solid #ddd;")
        footer_widget.setFixedHeight(30)
        
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(10, 0, 10, 0)
        
        # Version de l'application
        version_label = QLabel(f"Version {APP_VERSION}")
        footer_layout.addWidget(version_label)
        
        footer_layout.addStretch()
        
        # Nombre de commandes en attente (placeholder)
        self.pending_orders_label = QLabel("Commandes en attente: 0")
        footer_layout.addWidget(self.pending_orders_label)
        
        footer_layout.addStretch()
        
        # Date et heure actuelles
        self.datetime_label = QLabel()
        self.update_datetime()
        footer_layout.addWidget(self.datetime_label)
        
        # Timer pour mettre à jour l'heure
        self.datetime_timer = QTimer(self)
        self.datetime_timer.timeout.connect(self.update_datetime)
        self.datetime_timer.start(1000)  # Mise à jour chaque seconde
        
        self.main_layout.addWidget(footer_widget)
    
    def setup_menu(self):
        """Configure le menu de l'application"""
        menu_bar = self.menuBar()
        
        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")
        
        import_action = QAction("Importer des commandes (CSV)", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)
        
        export_menu = QMenu("Exporter des données", self)
        
        export_orders_action = QAction("Exporter les commandes", self)
        export_orders_action.triggered.connect(self.export_orders)
        export_menu.addAction(export_orders_action)
        
        export_print_action = QAction("Exporter le plan d'impression", self)
        export_print_action.triggered.connect(self.export_print_plan)
        export_menu.addAction(export_print_action)
        
        export_inventory_action = QAction("Exporter l'inventaire", self)
        export_inventory_action.triggered.connect(self.export_inventory)
        export_menu.addAction(export_inventory_action)
        
        file_menu.addMenu(export_menu)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Quitter", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Édition
        edit_menu = menu_bar.addMenu("Édition")
        
        new_order_action = QAction("Nouvelle commande", self)
        new_order_action.setShortcut("Ctrl+N")
        new_order_action.triggered.connect(self.create_new_order)
        edit_menu.addAction(new_order_action)
        
        edit_menu.addSeparator()
        
        preferences_action = QAction("Préférences", self)
        preferences_action.setShortcut("Ctrl+P")
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        
        # Menu Affichage
        view_menu = menu_bar.addMenu("Affichage")
        
        refresh_action = QAction("Actualiser", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_data)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        toggle_sidebar_action = QAction("Afficher/masquer la barre latérale", self)
        toggle_sidebar_action.setShortcut("F11")
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(toggle_sidebar_action)
        
        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")
        
        help_action = QAction("Aide", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Configure la barre d'outils"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("""
            QToolBar {
                border-bottom: 1px solid #ddd;
                spacing: 5px;
            }
            QToolButton {
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        
        # Action Actualiser
        refresh_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Actualiser", self)
        refresh_action.triggered.connect(self.refresh_data)
        self.toolbar.addAction(refresh_action)
        
        self.toolbar.addSeparator()
        
        # Actions Commandes
        new_order_action = QAction(self.style().standardIcon(QStyle.SP_FileIcon), "Nouvelle commande", self)
        new_order_action.triggered.connect(self.create_new_order)
        self.toolbar.addAction(new_order_action)
        
        self.toolbar.addSeparator()
        
        # Actions Impression
        start_print_action = QAction(self.style().standardIcon(QStyle.SP_MediaPlay), "Démarrer impression", self)
        start_print_action.triggered.connect(self.start_printing)
        self.toolbar.addAction(start_print_action)
        
        finish_print_action = QAction(self.style().standardIcon(QStyle.SP_DialogApplyButton), "Terminer impression", self)
        finish_print_action.triggered.connect(self.finish_printing)
        self.toolbar.addAction(finish_print_action)
        
        self.toolbar.addSeparator()
        
        # Action Expédition
        ship_order_action = QAction(self.style().standardIcon(QStyle.SP_DialogYesButton), "Expédier commande", self)
        ship_order_action.triggered.connect(self.ship_order)
        self.toolbar.addAction(ship_order_action)
        
        self.addToolBar(self.toolbar)
    
    def setup_status_bar(self):
        """Configure la barre d'état"""
        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        
        # Message par défaut
        self.status_message = QLabel("Prêt")
        self.status_bar.addWidget(self.status_message, 1)
        
        # Dernière actualisation
        self.refresh_label = QLabel()
        self.status_bar.addPermanentWidget(self.refresh_label)
        
        self.setStatusBar(self.status_bar)
    
    def setup_shortcuts(self):
        """Configure les raccourcis clavier"""
        # Raccourcis pour les onglets
        self.shortcut_dash = QShortcut(QKeySequence("Ctrl+1"), self)
        self.shortcut_dash.activated.connect(self.open_dashboard)
        
        self.shortcut_orders = QShortcut(QKeySequence("Ctrl+2"), self)
        self.shortcut_orders.activated.connect(lambda: self.open_orders("all"))
        
        self.shortcut_print = QShortcut(QKeySequence("Ctrl+3"), self)
        self.shortcut_print.activated.connect(self.open_print_plan)
        
        self.shortcut_inventory = QShortcut(QKeySequence("Ctrl+4"), self)
        self.shortcut_inventory.activated.connect(self.open_inventory)
        
        # Raccourcis actions
        self.shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        self.shortcut_refresh.activated.connect(self.refresh_data)
    
    def setup_auto_refresh(self):
        """Configure le rafraîchissement automatique des données"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_data)
        
        # Rafraîchir toutes les 5 minutes
        self.refresh_timer.start(5 * 60 * 1000)
    
    def on_nav_item_clicked(self, item, column):
        """Gère les clics sur les éléments de la navigation"""
        if item is self.dashboard_item:
            self.open_dashboard()
        elif item is self.print_item:
            self.open_print_plan()
        elif item is self.inventory_item:
            self.open_inventory()
        elif item is self.stats_item:
            self.open_statistics()
        elif item.parent() is self.orders_item:
            # Sous-sections des commandes
            index = self.orders_item.indexOfChild(item)
            if index == 0:
                self.open_orders("all")
            elif index == 1:
                self.open_orders("pending")
            elif index == 2:
                self.open_orders("in_progress")
            elif index == 3:
                self.open_orders("ready")
            elif index == 4:
                self.open_orders("shipped")
    
    def open_dashboard(self):
        """Ouvre l'onglet du tableau de bord"""
        # Vérifier si l'onglet existe déjà
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Tableau de bord":
                self.tabs.setCurrentIndex(i)
                return
        
        # Créer un nouvel onglet de tableau de bord
        from views.dashboard_view import DashboardWidget
        dashboard_widget = DashboardWidget()
        
        # Ajouter l'onglet
        self.tabs.addTab(dashboard_widget, "Tableau de bord")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
    
    def open_orders(self, filter_type="all"):
        """Ouvre l'onglet des commandes avec un filtre spécifique"""
        # Titre de l'onglet en fonction du filtre
        if filter_type == "all":
            tab_title = "Toutes les commandes"
        elif filter_type == "pending":
            tab_title = "Commandes en attente"
        elif filter_type == "in_progress":
            tab_title = "Commandes en cours"
        elif filter_type == "ready":
            tab_title = "Commandes prêtes"
        elif filter_type == "shipped":
            tab_title = "Commandes expédiées"
        else:
            tab_title = "Commandes"
        
        # Vérifier si l'onglet existe déjà
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == tab_title:
                self.tabs.setCurrentIndex(i)
                return
        
        # Créer un nouvel onglet de commandes
        from views.orders_view import OrdersWidget
        orders_widget = OrdersWidget(self, filter_status=filter_type)
        
        # Ajouter l'onglet
        self.tabs.addTab(orders_widget, tab_title)
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
    
    def open_print_plan(self):
        """Ouvre l'onglet du plan d'impression"""
        # Vérifier si l'onglet existe déjà
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Plan d'impression":
                self.tabs.setCurrentIndex(i)
                return
        
        # Créer un nouvel onglet de plan d'impression
        from views.print_plan_view import PrintPlanWidget
        print_plan_widget = PrintPlanWidget(self)
        
        # Ajouter l'onglet
        self.tabs.addTab(print_plan_widget, "Plan d'impression")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
    
    def open_inventory(self):
        """Ouvre l'onglet de l'inventaire"""
        # Vérifier si l'onglet existe déjà
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Inventaire":
                self.tabs.setCurrentIndex(i)
                return
        
        # Créer un nouvel onglet d'inventaire
        from views.inventory_view import InventoryView
        inventory_widget = InventoryView(self)
        
        # Ajouter l'onglet
        self.tabs.addTab(inventory_widget, "Inventaire")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
    
    def open_statistics(self):
        """Ouvre l'onglet des statistiques"""
        # Vérifier si l'onglet existe déjà
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Statistiques":
                self.tabs.setCurrentIndex(i)
                return
        
        # Créer un nouvel onglet de statistiques
        stats_tab = QWidget()
        
        # Placeholder pour le contenu
        layout = QVBoxLayout(stats_tab)
        label = QLabel("Statistiques (à implémenter)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Ajouter l'onglet
        self.tabs.addTab(stats_tab, "Statistiques")
        self.tabs.setCurrentIndex(self.tabs.count() - 1)
    
    def close_tab(self, index):
        """Ferme un onglet"""
        # Ne pas fermer l'onglet s'il n'y en a qu'un
        if self.tabs.count() <= 1:
            return
        
        self.tabs.removeTab(index)
    
    def refresh_data(self):
        """Rafraîchit les données de l'application"""
        # À implémenter: actualiser les données
        self.status_message.setText("Actualisation des données...")
        
        # Simuler un délai d'actualisation
        QTimer.singleShot(500, lambda: self.status_message.setText("Données actualisées"))
        
        # Mettre à jour la date de dernière actualisation
        self.last_refresh = datetime.now()
        self.refresh_label.setText(f"Dernière actualisation: {self.last_refresh.strftime('%H:%M:%S')}")
    
    def update_datetime(self):
        """Met à jour l'affichage de la date et de l'heure"""
        now = datetime.now()
        self.datetime_label.setText(now.strftime("%d/%m/%Y %H:%M:%S"))
    
    def show_import_dialog(self):
        """Affiche le dialogue d'importation de commandes Shopify"""
        dialog = ImportDialog(self)
        result = dialog.exec_()
        
        if result == ImportDialog.Accepted:
            # Rafraîchir les vues après une importation réussie
            self.refresh_data()
    
    def export_orders(self):
        """Exporte les commandes"""
        # À implémenter
        self.status_message.setText("Exportation des commandes...")
        
        # Simuler un délai d'exportation
        QTimer.singleShot(500, lambda: self.status_message.setText("Commandes exportées"))
    
    def export_print_plan(self):
        """Exporte le plan d'impression"""
        # À implémenter
        self.status_message.setText("Exportation du plan d'impression...")
        
        # Simuler un délai d'exportation
        QTimer.singleShot(500, lambda: self.status_message.setText("Plan d'impression exporté"))
    
    def export_inventory(self):
        """Exporte l'inventaire"""
        # À implémenter
        self.status_message.setText("Exportation de l'inventaire...")
        
        # Simuler un délai d'exportation
        QTimer.singleShot(500, lambda: self.status_message.setText("Inventaire exporté"))
    
    def create_new_order(self):
        """Crée une nouvelle commande"""
        # À implémenter
        self.status_message.setText("Création d'une nouvelle commande...")
        
        # Simuler un délai
        QTimer.singleShot(500, lambda: self.status_message.setText("Nouvelle commande créée"))
    
    def start_printing(self):
        """Démarre un processus d'impression"""
        # À implémenter
        self.status_message.setText("Démarrage de l'impression...")
        
        # Simuler un délai
        QTimer.singleShot(500, lambda: self.status_message.setText("Impression démarrée"))
    
    def finish_printing(self):
        """Termine un processus d'impression"""
        # À implémenter
        self.status_message.setText("Finalisation de l'impression...")
        
        # Simuler un délai
        QTimer.singleShot(500, lambda: self.status_message.setText("Impression terminée"))
    
    def ship_order(self):
        """Expédie une commande"""
        # À implémenter
        self.status_message.setText("Expédition de la commande...")
        
        # Simuler un délai
        QTimer.singleShot(500, lambda: self.status_message.setText("Commande expédiée"))
    
    def show_preferences(self):
        """Affiche les préférences de l'application"""
        # À implémenter
        QMessageBox.information(self, "Préférences", "Préférences (à implémenter)")
    
    def toggle_sidebar(self):
        """Affiche ou masque la barre latérale"""
        current_sizes = self.splitter.sizes()
        if current_sizes[0] > 0:
            # Masquer la barre latérale
            self.splitter.setSizes([0, current_sizes[0] + current_sizes[1]])
        else:
            # Afficher la barre latérale
            self.splitter.setSizes([220, current_sizes[1] - 220])
    
    def show_help(self):
        """Affiche l'aide de l'application"""
        # À implémenter
        QMessageBox.information(self, "Aide", "Système d'aide (à implémenter)")
    
    def show_about(self):
        """Affiche les informations sur l'application"""
        about_text = f"""
        <h2>{APP_NAME}</h2>
        <p>Version: {APP_VERSION}</p>
        <p>Application de gestion pour l'impression 3D</p>
        <p>Développée pour Plasmik3D</p>
        <p>&copy; 2025 Plasmik3D</p>
        """
        
        QMessageBox.about(self, "À propos", about_text)
    
    def save_settings(self):
        """Enregistre les paramètres de l'application"""
        self.settings.setValue("windowGeometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("splitterSizes", self.splitter.sizes())
    
    def restore_settings(self):
        """Restaure les paramètres de l'application"""
        if self.settings.contains("windowGeometry"):
            self.restoreGeometry(self.settings.value("windowGeometry"))
        
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))
    
    def closeEvent(self, event):
        """Gère l'événement de fermeture de la fenêtre"""
        self.save_settings()
        event.accept()
        
    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Charger le style CSS
        self.load_stylesheet()
        
        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # En-tête avec logo et titre
        self.setup_header()
        
        # Layout pour le contenu principal
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Navigation latérale et onglets
        self.setup_navigation()
        
        # Ajouter le contenu principal au layout principal
        self.main_layout.addLayout(self.content_layout)
        
        # Configuration du pied de page
        self.setup_footer()
        
        # Configuration du menu
        self.setup_menu()
        
        # Configuration de la barre d'outils
        self.setup_toolbar()
        
        # Configuration de la barre d'état
        self.setup_status_bar()
        
        # Configuration des raccourcis clavier
        self.setup_shortcuts()

    def load_stylesheet(self):
        """Charge la feuille de style CSS de l'application"""
        style_path = os.path.join(RESOURCES_DIR, "styles", "style.css")
        
        # Vérifier si le fichier de style existe
        if not os.path.exists(style_path):
            # Créer le dossier styles s'il n'existe pas
            os.makedirs(os.path.dirname(style_path), exist_ok=True)
            
            # Créer un fichier de style vide
            with open(style_path, 'w', encoding='utf-8') as f:
                f.write("/* Style de l'application Plasmik3D */\n")
        
        # Charger le style
        try:
            with open(style_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Erreur lors du chargement du style: {e}")