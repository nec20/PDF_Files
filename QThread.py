import sys
import time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from google import genai
import pathlib

class GeminiWorker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(str)
    from google import genai

    def __init__(self,client , pdf_path, question):
        super().__init__()
        self.client = client
        self.pdf_path = pdf_path
        self.question = question

    def run(self):
        if not self.pdf_path:
            self.result.emit("Önce PDF yükle!")
            

        soru = self.question
        if not soru:
            self.result.emit("Soru yazmalısın!")
        

        self.result.emit("Gemini düşünüyor...")

        try:
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[self.pdf_path, soru]
            )
            self.result.emit(response.text)
        except Exception as e:
            self.result.emit(str(e))
        self.finished.emit()
class Gemini_Pdf_Worker(QObject):
    finished = pyqtSignal()
    result = pyqtSignal(str)
    referans=pyqtSignal(object)
    def __init__(self,client,selected_path):
        super().__init__()
        self.client = client
        self.pdf_path = selected_path
    def run(self):
        
        self.uploaded_pdf_ref = self.client.files.upload(file=pathlib.Path(self.pdf_path))
        self.referans.emit(self.uploaded_pdf_ref)
        self.result.emit("Pdf Yüklendi...")
        self.finished.emit()
#
#GUI
#
class OrbitPDFApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Gemini client
        self.client = genai.Client(api_key="API KEY")

        self.selected_path = None
        self.uploaded_file_ref = None
        self.uploaded_pdf_ref = None
        self.active_threads = []

        self.init_ui()

    # ---------------- UI ----------------
    def init_ui(self):
        self.setWindowTitle("Orbit Soru Cevap (PDF)")
        #self.geometry(500,200,800,800)

        self.picture = QtWidgets.QLabel()
        self.picture.setPixmap(QtGui.QPixmap("orbit1.png"))

        self.btn_select = QtWidgets.QPushButton("Select Pdf")
        self.btn_upload = QtWidgets.QPushButton("Upload Pdf")
        self.btn_ask = QtWidgets.QPushButton("Ask Gemini")

        self.prompt_line = QtWidgets.QLineEdit()
        self.prompt_line.setPlaceholderText("Sorunuzu buraya yazın...")

        self.response_area = QtWidgets.QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("Gemini'nin cevabı burada görünecek...")

        # layout
        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(self.btn_select)
        hb.addWidget(self.btn_upload)
        hb.addWidget(self.btn_ask)

        vb = QtWidgets.QVBoxLayout()
        vb.addWidget(self.picture)
        vb.addWidget(self.response_area)
        vb.addWidget(self.prompt_line)
        vb.addLayout(hb)

        self.setLayout(vb)

        # bağlantılar
        self.btn_select.clicked.connect(self.select_pdf)
        self.btn_upload.clicked.connect(self.start_thread_upload_pdf)
        #self.btn_ask.clicked.connect(self.ask_gemini)
        self.btn_ask.clicked.connect(self.start_thread_ask_gemini)
        

    # ---------------- PDF SEÇ ----------------
    def select_pdf(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "PDF seç",
            "",
            "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
        )

        if file_path:
            self.selected_path = file_path
            self.response_area.setText(f"Seçilen dosya:\n{file_path}")
    # Thread başlat
    def start_thread_ask_gemini(self):
        if not self.uploaded_pdf_ref:
            self.response_area.setText("Önce PDF seç")
            return

        soru = self.prompt_line.text()

        if any(t.isRunning() for t in self.active_threads):
            self.response_area.setText("Hala çalışan bir işlem var, bekleyin...")
            return 
        self.thread = QThread()
        self.worker = GeminiWorker(self.client,self.uploaded_pdf_ref, soru)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(lambda: self.active_threads.append(self.thread))
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.show_result)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.active_threads.remove(self.thread))

        self.thread.start()
        self.response_area.setText("Sorgulanıyor...")

    # sonucu GUI'de göster
    def show_result(self, text):
        self.response_area.setText(text)
    def start_thread_upload_pdf(self):
        if not self.selected_path :
            self.response_area.setText("Önce PDF seç!")
            return

        self.response_area.setText("PDF Gemini'ye yükleniyor...")

        try:
            if any(t.isRunning() for t in self.active_threads):
                self.response_area.setText("Hala çalışan bir işlem var, bekleyin...")
                return 
            self.thread = QThread()
            self.worker = Gemini_Pdf_Worker(self.client,self.selected_path)
            
            self.response_area.setText("PDF yükleniyor ✔")

        except Exception as e:
            self.response_area.setText(str(e))
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: self.active_threads.append(self.thread))
        self.thread.started.connect(self.worker.run)
        self.worker.result.connect(self.show_result_pdf)
        self.worker.referans.connect(self.uploaded_pdf_referans)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: self.active_threads.remove(self.thread))

        self.thread.start()
    def show_result_pdf(self, text):
        self.response_area.setText(text)
    def uploaded_pdf_referans(self,ref):
        self.uploaded_pdf_ref=ref

    # ---------------- PDF YÜKLE ----------------
    
# ---------------- APP ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OrbitPDFApp()
    window.show()
    sys.exit(app.exec())
#------------------------------------------