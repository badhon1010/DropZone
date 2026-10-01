import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox, QInputDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

from ui import DropZoneWidget
from network import NetworkManager

def create_tray_icon():
    from ui import resource_path
    return QIcon(resource_path("assets/app_logo.png"))

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
            if os.path.isdir(path):
                import shutil
                import tempfile
                tray_icon.showMessage("Zipping Folder", f"Preparing {os.path.basename(path)}...", QSystemTrayIcon.Information, 1500)
                zip_path = os.path.join(tempfile.gettempdir(), os.path.basename(path))
                zip_path = shutil.make_archive(zip_path, 'zip', path)
                network_manager.send_file(zip_path, target_ip, delete_after=True)
            else:
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
    
    from PyQt5.QtWidgets import QFileDialog
    from PyQt5.QtGui import QIcon
    from ui import resource_path
    
    def send_via_dialog():
        file_paths, _ = QFileDialog.getOpenFileNames(None, "Select Files to Send")
        if file_paths:
            on_files_dropped(file_paths)
            
    def send_folder_dialog():
        folder_path = QFileDialog.getExistingDirectory(None, "Select Folder to Send")
        if folder_path:
            on_files_dropped([folder_path])
            
    show_action = QAction(QIcon(resource_path("assets/hide.svg")), "Show / Hide Widget", app)
    show_action.triggered.connect(lambda: widget.hide() if widget.isVisible() else widget.show())
    
    send_action = QAction(QIcon(resource_path("assets/details.svg")), "Send File(s)...", app)
    send_action.triggered.connect(send_via_dialog)
    
    send_folder_action = QAction(QIcon(resource_path("assets/folder.svg")), "Send Folder...", app)
    send_folder_action.triggered.connect(send_folder_dialog)
    
    history_action = QAction(QIcon(resource_path("assets/history.svg")), "Transfer History", app)
    history_action.triggered.connect(lambda: widget.history_requested.emit())
    
    settings_action = QAction(QIcon(resource_path("assets/settings.svg")), "Configure PC Name", app)
    settings_action.triggered.connect(lambda: widget.settings_requested.emit())
    
    autostart_action = QAction("Run on Startup", app)
    autostart_action.setCheckable(True)
    # We will set its checked state later when we know is_autostart_enabled()
    autostart_action.triggered.connect(lambda checked: widget.autostart_requested.emit(checked))
    
    open_folder_action = QAction(QIcon(resource_path("assets/folder.svg")), "Open Downloads Folder", app)
    open_folder_action.triggered.connect(lambda: os.startfile(download_dir))
    
    quit_action = QAction(QIcon(resource_path("assets/exit.svg")), "Exit", app)
    def quit_app():
        network_manager.stop()
        app.quit()
    quit_action.triggered.connect(quit_app)
    
    tray_menu.addAction(show_action)
    tray_menu.addSeparator()
    tray_menu.addAction(send_action)
    tray_menu.addAction(send_folder_action)
    tray_menu.addSeparator()
    tray_menu.addAction(history_action)
    tray_menu.addAction(settings_action)
    tray_menu.addAction(autostart_action)
    tray_menu.addSeparator()
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
    import winsound
    from datetime import datetime
    
    transfer_history = []
    
    def on_transfer_complete(filename):
        widget.hide_progress()
        msg = f"Sent: {filename}"
        tray_icon.showMessage("Transfer Complete", msg, QSystemTrayIcon.Information, 2000)
        transfer_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        try: winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except: pass
        
    def on_receive_complete(filename):
        widget.hide_progress()
        msg = f"Received: {filename}"
        tray_icon.showMessage("File Received", msg, QSystemTrayIcon.Information, 2000)
        transfer_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        try: winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except: pass

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
    
    widget.history_requested.connect(lambda: __import__('ui').HistoryDialog(transfer_history).exec_())
    
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
    
    # Autostart feature
    import winreg
    
    def is_autostart_enabled():
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "DropZone")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
            
    def set_autostart(enable):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, "DropZone", 0, winreg.REG_SZ, f'"{sys.executable}" "{os.path.abspath(__file__)}"')
                tray_icon.showMessage("Auto-Start Enabled", "DropZone will now run automatically on startup.", QSystemTrayIcon.Information, 2000)
            else:
                try:
                    winreg.DeleteValue(key, "DropZone")
                except FileNotFoundError:
                    pass
                tray_icon.showMessage("Auto-Start Disabled", "DropZone will no longer run on startup.", QSystemTrayIcon.Information, 2000)
            winreg.CloseKey(key)
        except Exception as e:
            QMessageBox.warning(None, "Error", f"Could not change startup settings: {e}")
            
    def on_autostart_changed(enable):
        widget.autostart_enabled = enable
        autostart_action.setChecked(enable)
        set_autostart(enable)

    widget.autostart_enabled = is_autostart_enabled()
    autostart_action.setChecked(widget.autostart_enabled)
    widget.autostart_requested.connect(on_autostart_changed)
    
    # Callback for submenu hover stats
    widget.set_network_info_callback(lambda: (network_manager.get_local_ip(), network_manager.get_active_peers()))
    
    widget.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
