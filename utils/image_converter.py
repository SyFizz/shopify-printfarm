import os
import subprocess
import sys
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtSvg import QSvgRenderer
from config import RESOURCES_DIR

def svg_to_png(svg_path, output_path, width, height):
    """
    Convertit un fichier SVG en PNG.
    
    Args:
        svg_path (str): Chemin vers le fichier SVG source
        output_path (str): Chemin de destination pour le fichier PNG
        width (int): Largeur de l'image PNG en pixels
        height (int): Hauteur de l'image PNG en pixels
    
    Returns:
        bool: True si la conversion a réussi, False sinon
    """
    try:
        # Créer le répertoire de destination s'il n'existe pas
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Utiliser QSvgRenderer pour convertir SVG en PNG
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        # Enregistrer l'image PNG
        pixmap.save(output_path)
        
        return True
    except Exception as e:
        print(f"Erreur lors de la conversion de l'image: {e}")
        return False

def create_app_icons():
    """
    Crée des icônes pour l'application à partir du fichier SVG du logo.
    
    Cette fonction crée des versions PNG du logo en différentes tailles.
    """
    svg_logo_path = os.path.join(RESOURCES_DIR, "icons", "logo.svg")
    
    if not os.path.exists(svg_logo_path):
        print(f"Erreur: Logo SVG non trouvé à {svg_logo_path}")
        return False
    
    # Différentes tailles d'icônes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    
    for size in sizes:
        output_path = os.path.join(RESOURCES_DIR, "icons", f"logo_{size}.png")
        if svg_to_png(svg_logo_path, output_path, size, size):
            print(f"Icône {size}x{size} créée avec succès")
        else:
            print(f"Échec de la création de l'icône {size}x{size}")
    
    return True

def get_app_icon():
    """
    Retourne une QIcon pour l'application, avec plusieurs tailles.
    
    Returns:
        QIcon: Icône de l'application
    """
    icon = QIcon()
    
    # Ajouter les différentes tailles d'icônes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    for size in sizes:
        icon_path = os.path.join(RESOURCES_DIR, "icons", f"logo_{size}.png")
        if os.path.exists(icon_path):
            icon.addFile(icon_path, QSize(size, size))
    
    # Si aucune icône n'est trouvée, utiliser une icône système par défaut
    if icon.isNull():
        from PyQt5.QtWidgets import QStyle, QApplication
        icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
    
    return icon

if __name__ == "__main__":
    # Ce code s'exécute uniquement si ce fichier est exécuté directement
    from PyQt5.QtGui import QPainter
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    create_app_icons()