# DropZone

DropZone is a seamless, peer-to-peer file and folder sharing application built with Python and PyQt5. It allows users to quickly transfer files across a local network simply by dragging and dropping them into a floating widget, without requiring any cloud services or external servers.

*Developed by **Badhon Saha***

## 🚀 Features

- **Drag and Drop Interface:** A minimalistic, floating widget where you can drop files and folders to send them instantly.
- **Auto Peer Discovery:** Automatically detects other computers running DropZone on your local network.
- **Folder Support:** Folders are automatically zipped before transferring and unzipped on the receiver's end.
- **System Tray Integration:** Runs quietly in the background. Right-click the tray icon to view history, change your PC's nickname, or configure startup settings.
- **Auto-Start:** Option to automatically run DropZone when Windows starts.
- **Transfer History:** Built-in history to keep track of files you've sent and received.
- **Native Notifications:** Sounds and tray alerts keep you notified of transfer progress and completions.

## 🛠️ Built With

- **Python 3**
- **PyQt5** - For the graphical user interface.
- **Sockets** - For peer-to-peer network file transferring.
- **Pillow** - For image processing.

## ⚙️ How to Run Locally

1. Clone this repository:
   ```bash
   git clone https://github.com/badhon1010/DropZone.git
   ```
2. Navigate to the project directory:
   ```bash
   cd DropZone
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python src/main.py
   ```

## 📦 Building the Executable (.exe)

You can build a standalone Windows executable for DropZone using **PyInstaller**. Run the following command in the project root:

```bash
pyinstaller --noconsole --onefile --icon="assets/app_logo.ico" --add-data "assets;assets" src/main.py
```

The compiled `main.exe` will be located in the `dist/` directory.

## 📄 License

This project is open-source and free to use.
