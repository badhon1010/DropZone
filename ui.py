import sys
import os
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMenu, QDialog, QListWidget
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QLinearGradient, QIcon

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class DropZoneWidget(QWidget):
    files_dropped = pyqtSignal(list)
    cancel_clicked = pyqtSignal()
    show_details_requested = pyqtSignal()
    open_downloads_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    select_pc_requested = pyqtSignal(str)
    settings_requested = pyqtSignal()
    autostart_requested = pyqtSignal(bool)
    history_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setAcceptDrops(True)
        self.resize(130, 130)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel("DropZone")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #FFFFFF; font-weight: 800; font-family: 'Segoe UI', sans-serif; font-size: 16px; letter-spacing: 1px;")
        
        self.status_label = QLabel("0 Peers")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #CCCCCC; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #64FFDA; font-size: 12px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        self.progress_label.hide()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px 15px;
                font-weight: bold;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
        """)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.hide()
        
        layout.addWidget(self.label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        
        self.cancel_button.clicked.connect(self.cancel_clicked.emit)
        
        self.drag_position = QPoint()
        self.network_info_callback = None
        self.selected_target_ip = None
        self.autostart_enabled = False
        
    def set_network_info_callback(self, callback):
        self.network_info_callback = callback
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background for modern premium look
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor(40, 44, 52, 240))
        grad.setColorAt(1.0, QColor(33, 37, 43, 240))
        
        painter.setBrush(grad)
        painter.setPen(QColor(60, 64, 72, 255))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        details_menu = QMenu("Connection Details", self)
        details_menu.setIcon(QIcon(resource_path("assets/details.svg")))
        
        select_pc_menu = QMenu("Select Target PC", self)
        select_pc_menu.setIcon(QIcon(resource_path("assets/pc.svg")))
        
        if self.network_info_callback:
            local_ip, peers = self.network_info_callback() # peers is {ip: nickname}
            details_menu.addAction(f"Local IP: {local_ip}").setEnabled(False)
            details_menu.addSeparator()
            if not peers:
                details_menu.addAction("No peers found").setEnabled(False)
                select_pc_menu.addAction("No peers available").setEnabled(False)
            else:
                for ip, nick in peers.items():
                    details_menu.addAction(f"{nick} ({ip})").setEnabled(False)
                    
                    action = select_pc_menu.addAction(f"{nick} ({ip})")
                    action.setData(ip)
                    action.setCheckable(True)
                    if ip == self.selected_target_ip:
                        action.setChecked(True)
                    
        menu.addMenu(details_menu)
        menu.addMenu(select_pc_menu)
        menu.addSeparator()
        
        autostart_action = menu.addAction("Run on Startup")
        autostart_action.setCheckable(True)
        autostart_action.setChecked(self.autostart_enabled)
        
        history_action = menu.addAction(QIcon(resource_path("assets/history.svg")), "Transfer History")
        
        settings_action = menu.addAction(QIcon(resource_path("assets/settings.svg")), "Configure PC Name")
        open_folder_action = menu.addAction(QIcon(resource_path("assets/folder.svg")), "Open Downloads Folder")
        menu.addSeparator()
        hide_action = menu.addAction(QIcon(resource_path("assets/hide.svg")), "Hide Main Window")
        menu.addSeparator()
        exit_action = menu.addAction(QIcon(resource_path("assets/exit.svg")), "Exit")
        
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if action and action.parentWidget() == select_pc_menu:
            self.selected_target_ip = action.data()
            self.select_pc_requested.emit(self.selected_target_ip)
        elif action == autostart_action:
            self.autostart_enabled = action.isChecked()
            self.autostart_requested.emit(self.autostart_enabled)
        elif action == history_action:
            self.history_requested.emit()
        elif action == settings_action:
            self.settings_requested.emit()
        elif action == open_folder_action:
            self.open_downloads_requested.emit()
        elif action == hide_action:
            self.hide_requested.emit()
        elif action == exit_action:
            self.exit_requested.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setText("Drop Here 🚀")
            self.label.setStyleSheet("color: #64FFDA; font-weight: 900; font-family: 'Segoe UI', sans-serif; font-size: 16px; letter-spacing: 1px;")
            
    def dragLeaveEvent(self, event):
        self.label.setText("DropZone")
        self.label.setStyleSheet("color: #FFFFFF; font-weight: 800; font-family: 'Segoe UI', sans-serif; font-size: 16px; letter-spacing: 1px;")

    def dropEvent(self, event):
        self.label.setText("DropZone")
        self.label.setStyleSheet("color: #FFFFFF; font-weight: 800; font-family: 'Segoe UI', sans-serif; font-size: 16px; letter-spacing: 1px;")
        
        urls = event.mimeData().urls()
        if urls:
            file_paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
            if file_paths:
                self.files_dropped.emit(file_paths)

    def update_peers(self, peers):
        count = len(peers)
        self.status_label.setText(f"{count} Peer{'s' if count != 1 else ''}")
        if count > 0:
            self.status_label.setStyleSheet("color: #64FFDA; font-size: 12px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        else:
            self.status_label.setStyleSheet("color: #CCCCCC; font-size: 11px; font-family: 'Segoe UI', sans-serif;")

    def show_progress(self, filename, percentage, speed_str):
        self.status_label.hide()
        self.progress_label.show()
        self.cancel_button.show()
        self.progress_label.setText(f"{percentage}% | {speed_str}")
        self.label.setText("Transferring...")
        self.label.setStyleSheet("color: #64FFDA; font-weight: 900; font-family: 'Segoe UI', sans-serif; font-size: 14px;")
        
    def hide_progress(self):
        self.progress_label.hide()
        self.cancel_button.hide()
        self.status_label.show()
        self.label.setText("DropZone")
        self.label.setStyleSheet("color: #FFFFFF; font-weight: 800; font-family: 'Segoe UI', sans-serif; font-size: 16px; letter-spacing: 1px;")

class HistoryDialog(QDialog):
    def __init__(self, history):
        super().__init__()
        self.setWindowTitle("Transfer History")
        self.resize(350, 450)
        self.setStyleSheet("""
            QDialog { background-color: #282C34; color: #ABB2BF; font-family: 'Segoe UI'; }
            QListWidget { background-color: #21252B; color: #ABB2BF; border: 1px solid #181A1F; padding: 5px; font-size: 12px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #282C34; }
            QListWidget::item:selected { background-color: #3E4451; color: #FFFFFF; }
        """)
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        if not history:
            self.list_widget.addItem("No transfers yet.")
        else:
            for item in reversed(history): # show newest first
                self.list_widget.addItem(item)
        
        layout.addWidget(self.list_widget)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #3E4451; color: white; padding: 6px; border-radius: 4px;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
