import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, QInputDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

from ui import DropZoneWidget, DetailsDialog
from network import NetworkManager

def create_tray_icon():
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(76, 175, 80))  # Green circle
    painter.drawEllipse(2, 2, 28, 28)
    painter.end()
    return QIcon(pixmap)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Ensure Download Directory exists
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "DropZone")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        
    network_manager = NetworkManager(download_dir)
    widget = DropZoneWidget()
    
    # Handle files dropped
    def on_files_dropped(file_paths):
        peers = network_manager.get_active_peers()
        if not peers:
            QMessageBox.warning(None, "No Peers", "No other DropZone clients found on the network.")
            return
            
        selected_ip = getattr(widget, 'selected_target_ip', None)
        target_ip = selected_ip if selected_ip in peers else peers[0]
        
        if len(peers) > 1 and not (selected_ip in peers):
            item, ok = QInputDialog.getItem(None, "Select Peer", "Choose peer to send to:", peers, 0, False)
            if ok and item:
                target_ip = item
            else:
                return

        for path in file_paths:
            network_manager.send_file(path, target_ip)
            
    widget.files_dropped.connect(on_files_dropped)
    
    # Update peer count UI
    def update_peer_ui(ip=None):
        widget.update_peers(network_manager.get_active_peers())
        
    network_manager.peer_discovered.connect(update_peer_ui)
    network_manager.peer_lost.connect(update_peer_ui)
    
    # System Tray Setup
    tray_icon = QSystemTrayIcon(create_tray_icon(), app)
    tray_menu = QMenu()
    
    show_action = QAction("Show / Hide Widget", app)
    show_action.triggered.connect(lambda: widget.hide() if widget.isVisible() else widget.show())
    
    open_folder_action = QAction("Open Downloads Folder", app)
    open_folder_action.triggered.connect(lambda: os.startfile(download_dir))
    
    quit_action = QAction("Exit", app)
    def quit_app():
        network_manager.stop()
        app.quit()
    quit_action.triggered.connect(quit_app)
    
    tray_menu.addAction(show_action)
    tray_menu.addAction(open_folder_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)
    
    tray_icon.setContextMenu(tray_menu)
    tray_icon.setToolTip("DropZone - P2P File Transfer")
    tray_icon.show()
    
    # Tray icon click actions
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.Trigger:
            if widget.isVisible():
                widget.hide()
            else:
                widget.show()
                
    tray_icon.activated.connect(on_tray_activated)
    
    # Notifications for file transfers
    def on_transfer_complete(filename):
        widget.hide_progress()
        tray_icon.showMessage("Transfer Complete", f"Sent: {filename}", QSystemTrayIcon.Information, 2000)
        
    def on_receive_complete(filename):
        widget.hide_progress()
        tray_icon.showMessage("File Received", f"Received: {filename}", QSystemTrayIcon.Information, 2000)

    network_manager.transfer_complete.connect(on_transfer_complete)
    network_manager.receive_complete.connect(on_receive_complete)
    
    def on_progress(filename, percentage, speed):
        widget.show_progress(filename, percentage, speed)
        
    network_manager.transfer_progress.connect(on_progress)
    network_manager.receive_progress.connect(on_progress)
    
    # Cancellation bindings
    widget.cancel_clicked.connect(network_manager.cancel_transfers)
    
    def on_transfer_cancelled(filename):
        widget.hide_progress()
        tray_icon.showMessage("Transfer Cancelled", f"Cancelled sending: {filename}", QSystemTrayIcon.Warning, 2000)
        
    def on_receive_cancelled(filename):
        widget.hide_progress()
        tray_icon.showMessage("Transfer Cancelled", f"Cancelled receiving: {filename}", QSystemTrayIcon.Warning, 2000)
        
    network_manager.transfer_cancelled.connect(on_transfer_cancelled)
    network_manager.receive_cancelled.connect(on_receive_cancelled)
    
    # Widget Context Menu Bindings
    widget.open_downloads_requested.connect(lambda: os.startfile(download_dir))
    widget.hide_requested.connect(widget.hide)
    widget.exit_requested.connect(quit_app)
    
    def open_settings():
        name, ok = QInputDialog.getText(None, "Configure PC", "Enter PC Nickname:", text=network_manager.nickname)
        if ok and name.strip():
            network_manager.set_nickname(name.strip())
            tray_icon.showMessage("Settings Saved", f"Nickname set to {name.strip()}", QSystemTrayIcon.Information, 2000)
            
    widget.settings_requested.connect(open_settings)
    
    # Callback for submenu hover stats
    widget.set_network_info_callback(lambda: (network_manager.get_local_ip(), network_manager.get_active_peers()))
    
    widget.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
