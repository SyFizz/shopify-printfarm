import sys
import os
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from views.main_window import MainWindow
from controllers.order_controller import OrderController
from controllers.print_controller import PrintController
from controllers.inventory_controller import InventoryController
from controllers.import_controller import ImportController
from controllers.workflow_controller import WorkflowController
from utils.stats_manager import StatsManager
from utils.image_converter import create_app_icons, get_app_icon
from config import DATABASE_PATH, RESOURCES_DIR, APP_NAME, APP_VERSION

def create_resources():
    """Crée les ressources nécessaires à l'application"""
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    os.makedirs(os.path.join(RESOURCES_DIR, "icons"), exist_ok=True)
    os.makedirs(os.path.join(RESOURCES_DIR, "styles"), exist_ok=True)

    # Créer les icônes de l'application
    logo_svg = os.path.join(RESOURCES_DIR, "icons", "logo.svg")
    if not os.path.exists(logo_svg):
        print("Aucun logo SVG trouvé. Utilisera des icônes par défaut.")
    else:
        create_app_icons()

def show_splash_screen():
    """Affiche un écran de démarrage"""
    # Vérifier si l'image du splash screen existe
    splash_path = os.path.join(RESOURCES_DIR, "icons", "logo_256.png")
    if not os.path.exists(splash_path):
        # Utiliser une image par défaut si le logo n'existe pas
        from PyQt5.QtWidgets import QStyle
        splash_pixmap = QApplication.style().standardPixmap(QStyle.SP_ComputerIcon).scaled(256, 256)
    else:
        splash_pixmap = QPixmap(splash_path)
    
    splash = QSplashScreen(splash_pixmap)
    splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
    
    # Ajouter un message
    splash.showMessage(f"{APP_NAME} {APP_VERSION}\nChargement en cours...",
                      Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    return splash

def initialize_database(splash=None):
    """Initialise la base de données et les contrôleurs"""
    if splash:
        splash.showMessage("Initialisation de la base de données...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    # Initialiser les contrôleurs
    # Ces initialisations créent les tables nécessaires si elles n'existent pas
    order_controller = OrderController()
    
    if splash:
        splash.showMessage("Initialisation du contrôleur d'impression...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    print_controller = PrintController()
    
    if splash:
        splash.showMessage("Initialisation du contrôleur d'inventaire...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    inventory_controller = InventoryController()
    
    if splash:
        splash.showMessage("Initialisation du contrôleur d'importation...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    import_controller = ImportController()
    
    if splash:
        splash.showMessage("Initialisation du contrôleur de workflow...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    workflow_controller = WorkflowController()
    
    if splash:
        splash.showMessage("Initialisation du gestionnaire de statistiques...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    
    stats_manager = StatsManager()
    
    if splash:
        splash.showMessage("Base de données initialisée avec succès.",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)

def main():
    """Point d'entrée principal de l'application"""
    # Initialiser l'application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Créer les ressources
    create_resources()
    
    # Afficher l'écran de démarrage
    splash = show_splash_screen()
    splash.show()
    app.processEvents()
    
    # Initialiser la base de données
    QTimer.singleShot(300, lambda: initialize_database(splash))
    
    # Définir l'icône de l'application
    app.setWindowIcon(get_app_icon())
    
    # Créer et afficher la fenêtre principale
    def show_main_window():
        splash.showMessage("Chargement de l'interface utilisateur...",
                         Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        
        window = MainWindow()
        
        # Fermer l'écran de démarrage et afficher la fenêtre principale
        splash.finish(window)
        window.show()
    
    # Afficher la fenêtre principale après un court délai
    # pour permettre à l'écran de démarrage de s'afficher
    QTimer.singleShot(1500, show_main_window)
    
    # Lancer la boucle d'événements
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()