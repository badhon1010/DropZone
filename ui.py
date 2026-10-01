import sys
import os
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMenu, QDialog, QFormLayout, QListWidget
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMenu, QDialog, QFormLayout, QListWidget
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient

class DropZoneWidget(QWidget):
    files_dropped = pyqtSignal(list)
    cancel_clicked = pyqtSignal()
    show_details_requested = pyqtSignal()
    open_downloads_requested = pyqtSignal()
    hide_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        # Window settings for frameless, floating, and tool (no taskbar)
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
        self.status_label.setStyleSheet("color: #BBBBBB; font-size: 11px; font-family: 'Segoe UI', sans-serif;")
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold; font-family: 'Segoe UI', sans-serif;")
        self.progress_label.hide()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E53935;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 4px 10px;
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
        self.active_peers = []
        self.network_info_callback = None
        
    def set_network_info_callback(self, callback):
        self.network_info_callback = callback
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background for modern look
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor(45, 50, 60, 240))
        gradient.setColorAt(1.0, QColor(25, 30, 35, 240))
        
        painter.setBrush(gradient)
        painter.setPen(QColor(100, 150, 255, 100))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 16, 16)
        
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
        if self.network_info_callback:
            local_ip, peers = self.network_info_callback()
            details_menu.addAction(f"Local IP: {local_ip}").setEnabled(False)
            details_menu.addSeparator()
            if not peers:
                details_menu.addAction("No peers found").setEnabled(False)
            else:
                for p in peers:
                    details_menu.addAction(f"Peer: {p}").setEnabled(False)
                    
        menu.addMenu(details_menu)
        
        open_folder_action = menu.addAction("Open Downloads Folder")
        menu.addSeparator()
        hide_action = menu.addAction("Hide Main Window")
        menu.addSeparator()
        exit_action = menu.addAction("Exit")
        
        action = menu.exec_(self.mapToGlobal(event.pos()))
        
        if action == open_folder_action:
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
        self.active_peers = peers
        count = len(peers)
        self.status_label.setText(f"{count} Peer{'s' if count != 1 else ''}")
        if count > 0:
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #a0a0a0; font-size: 10px;")

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

class DetailsDialog(QDialog):
    def __init__(self, local_ip, peers):
        super().__init__()
        self.setWindowTitle("Network Details")
        self.resize(300, 200)
        self.setStyleSheet("background-color: #2b2b2b; color: white; font-family: Segoe UI, sans-serif;")
        
        # Window settings
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        ip_label = QLabel(local_ip)
        ip_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        form_layout.addRow("Local IP:", ip_label)
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("Active Peers:"))
        self.peers_list = QListWidget()
        self.peers_list.setStyleSheet("background-color: #1e1e1e; border: 1px solid #444; border-radius: 4px; padding: 5px;")
        
        for peer in peers:
            self.peers_list.addItem(f"Peer: {peer}")
            
        if not peers:
            self.peers_list.addItem("No other peers found on local network.")
            self.peers_list.item(0).setForeground(QColor("#a0a0a0"))
            
        layout.addWidget(self.peers_list)
        self.setLayout(layout)
