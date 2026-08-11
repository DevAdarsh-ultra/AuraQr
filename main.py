import os
import sys
import io
import base64
from datetime import datetime
from pathlib import Path

# 1. Force the Qt Quick Controls style to Material Design
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

# 2. QtPy Imports
from qtpy.QtCore import QObject, Slot, Signal, Property
from qtpy.QtGui import QGuiApplication
from qtpy.QtQml import QQmlApplicationEngine

# 3. Third-party libraries
import qrcode

# 4. QML UI Layout Definition
QML_DATA = """
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

ApplicationWindow {
    id: window
    visible: true
    
    // Adaptive sizing for mobile and desktop preview
    width: Screen.width > 480 ? 360 : Screen.width
    height: Screen.height > 800 ? 640 : Screen.height
    title: "AuraQR"

    // Material Styling
    Material.theme: Material.System
    Material.accent: Material.Green
    Material.primary: Material.Green

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            
            Label {
                text: "AuraQR"
                font.pixelSize: 20
                font.bold: true
                Layout.fillWidth: true
                verticalAlignment: Text.AlignVCenter
                color: "white"
                leftPadding: 16 
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth
        
        topPadding: 24
        bottomPadding: 24
        leftPadding: 24
        rightPadding: 24

        ColumnLayout {
            width: parent.width
            spacing: 24

            Frame {
                Layout.fillWidth: true
                padding: 16
                
                ColumnLayout {
                    width: parent.width
                    spacing: 6
                    Label {
                        text: "How to Use ?"
                        font.pixelSize: 18
                        font.bold: true
                    }
                    Label {
                        text: "Type any URL or text below. The QR code will update instantly with every keystroke. Tap download to save it!"
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                        color: "#666666"
                    }
                }
            }

            TextField {
                id: qrInputField
                placeholderText: "Enter text or URL here..."
                Layout.fillWidth: true
                font.pixelSize: 16
                selectByMouse: true
                text: "Welcome to AuraQR !"
                
                onTextChanged: {
                    backend.generate_qr(text)
                }
            }

            Frame {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: Math.min(parent.width * 0.7, 240)
                Layout.preferredHeight: Layout.preferredWidth
                padding: 16
                background: Rectangle {
                    color: "white"
                    radius: 8
                    border.color: "#E0E0E0"
                    border.width: 1
                }

                Image {
                    id: qrDisplayImage
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectFit
                    source: backend.qrImageSource
                    
                    opacity: 0
                    Behavior on opacity { NumberAnimation { duration: 150 } }
                    onStatusChanged: {
                        if (status === Image.Ready) opacity = 1
                    }
                }
            }

            Button {
                text: "DOWNLOAD"
                highlighted: true
                Layout.fillWidth: true
                font.bold: true
                enabled: qrInputField.text.trim().length > 0
                onClicked: {
                    backend.save_qr(qrInputField.text)
                }
            }

            Label {
                text: backend.statusMessage
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
                color: "#4CAF50"
                wrapMode: Text.WordWrap
            }
        }
    }
}
"""

# 5. Backend Bridge logic
class QRBackend(QObject):
    qrChanged = Signal()
    statusChanged = Signal()

    def __init__(self):
        super().__init__()
        self._qr_image_source = ""
        self._status_message = ""
        self.generate_qr("Welcome to AuraQR !")

    @Property(str, notify=qrChanged)
    def qrImageSource(self):
        return self._qr_image_source

    @Property(str, notify=statusChanged)
    def statusMessage(self):
        return self._status_message

    @Slot(str)
    def generate_qr(self, target_text):
        if not target_text.strip():
            self._qr_image_source = ""
            self._status_message = ""
            self.qrChanged.emit()
            self.statusChanged.emit()
            return

        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(target_text)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        byte_stream = io.BytesIO()
        img.save(byte_stream, format="PNG")
        base64_data = base64.b64encode(byte_stream.getvalue()).decode("utf-8")
        
        self._qr_image_source = f"data:image/png;base64,{base64_data}"
        self.qrChanged.emit()

    @Slot(str)
    def save_qr(self, target_text):
        if not target_text.strip():
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(target_text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Determine storage location
            downloads_path = Path.home() / "Downloads"
            if not downloads_path.exists():
                downloads_path = Path("/sdcard/Download")
            downloads_path.mkdir(parents=True, exist_ok=True)

            # Generates timestamp: DDMMYYHHMMSS (e.g., 010727143025)
            timestamp = datetime.now().strftime("%d%m%y%H%M%S")
            filename = f"{timestamp}auraqr.png"
            file_path = downloads_path / filename

            img.save(str(file_path))
            
            self._status_message = f"Saved: {filename}"
        except Exception as e:
            self._status_message = f"Error saving: {str(e)}"
            
        self.statusChanged.emit()


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = QRBackend()
    engine.rootContext().setContextProperty("backend", backend)

    engine.loadData(QML_DATA.encode("utf-8"))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())
      
