from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QProgressBar, 
                            QTextEdit, QComboBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from controllers.import_controller import ImportController
import os

class ImportWorker(QThread):
    """Thread worker pour l'importation des données"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished_with_result = pyqtSignal(bool, str)
    
    def __init__(self, file_path, skip_existing=True, default_status="En attente", default_priority="Moyenne"):
        super().__init__()
        self.file_path = file_path
        self.skip_existing = skip_existing
        self.default_status = default_status
        self.default_priority = default_priority
        self.import_controller = ImportController()
        
        # Connecter les signaux du contrôleur aux signaux du worker
        self.import_controller.signals.progress.connect(self.progress)
        self.import_controller.signals.status.connect(self.status)
    
    def run(self):
        """Exécute l'importation en arrière-plan"""
        self.status.emit(f"Importation du fichier {os.path.basename(self.file_path)}...")
        self.progress.emit(10)
        
        # Importer les données
        success, message = self.import_controller.import_shopify_csv(
            self.file_path,
            skip_existing=self.skip_existing,
            default_status=self.default_status,
            default_priority=self.default_priority
        )
        
        self.progress.emit(100)
        self.finished_with_result.emit(success, message)
        
class ImportDialog(QDialog):
    """Dialogue pour l'importation de fichiers CSV de Shopify"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer des commandes Shopify")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # En-tête
        header_label = QLabel("Importer des commandes depuis un fichier CSV Shopify")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header_label)
        
        # Section de sélection de fichier
        file_group = QGroupBox("Sélectionner le fichier")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_label = QLabel("Aucun fichier sélectionné")
        file_layout.addWidget(self.file_path_label)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        layout.addWidget(file_group)
        
        # Options d'importation
        options_group = QGroupBox("Options d'importation")
        options_layout = QVBoxLayout(options_group)
        
        self.skip_existing_check = QCheckBox("Ignorer les commandes existantes")
        self.skip_existing_check.setChecked(True)
        options_layout.addWidget(self.skip_existing_check)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Statut initial des commandes:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["En attente", "En cours", "Prêt"])
        status_layout.addWidget(self.status_combo)
        options_layout.addLayout(status_layout)
        
        priority_layout = QHBoxLayout()
        priority_layout.addWidget(QLabel("Priorité par défaut:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Haute", "Moyenne", "Basse"])
        self.priority_combo.setCurrentText("Moyenne")
        priority_layout.addWidget(self.priority_combo)
        options_layout.addLayout(priority_layout)
        
        layout.addWidget(options_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Zone de journal
        log_group = QGroupBox("Journal d'importation")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.import_button = QPushButton("Importer")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.start_import)
        buttons_layout.addWidget(self.import_button)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def browse_file(self):
        """Ouvre un dialogue pour sélectionner un fichier CSV"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier CSV", "", "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            self.file_path_label.setText(file_path)
            self.import_button.setEnabled(True)
            self.log_text.clear()
            self.log_text.append(f"Fichier sélectionné: {file_path}")
            self.progress_bar.setValue(0)
    
    def start_import(self):
        """Démarre le processus d'importation"""
        file_path = self.file_path_label.text()
        if not os.path.exists(file_path):
            self.log_text.append("Erreur: Le fichier sélectionné n'existe pas.")
            return
        
        # Récupérer les options
        skip_existing = self.skip_existing_check.isChecked()
        default_status = self.status_combo.currentText()
        default_priority = self.priority_combo.currentText()
        
        # Désactiver les contrôles pendant l'importation
        self.import_button.setEnabled(False)
        
        # Créer et démarrer le worker thread
        self.worker = ImportWorker(file_path, skip_existing, default_status, default_priority)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished_with_result.connect(self.import_finished)
        self.worker.start()
    
    def update_progress(self, value):
        """Met à jour la barre de progression"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Ajoute un message au journal"""
        self.log_text.append(message)
    
    def import_finished(self, success, message):
        """Traite la fin de l'importation"""
        if success:
            self.log_text.append(f"Importation réussie: {message}")
        else:
            self.log_text.append(f"Erreur d'importation: {message}")
        
        # Réactiver les contrôles
        self.import_button.setEnabled(True)