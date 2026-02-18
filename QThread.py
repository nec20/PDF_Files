"""import sys
from PyQt5 import QtWidgets, QtGui
from google import genai
import pathlib
from PyQt5.QtCore import QThread, pyqtSignal
class App(QtWidgets.QApplication):
    def __init__(self):
        super(self).__init_ui__()
    def __init_ui__(self,Response,AskGemini,UploadPdf,SelectPdf,AskingBlanks):
        self.Response=Response
        self.AskGemini=AskGemini
        self.UploadPdf=UploadPdf
        self.SelectPdf=SelectPdf
        self.AskingBlanks=AskingBlanks
        
        self.Response=QtWidgets.QLabel()
        self.SelectPdf=QtWidgets.QPushButton()
        self.UploadPdf=QtWidgets.QPushButton()
        self.AskGemini=QtWidgets.QPushButton()
        self.AskingBlanks=QtWidgets.QLineEdit()
        
        self.vb=QtWidgets.QVBoxLayout()
        self.vb=QtWidgets.QHBoxLayout()
"""
        
        
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
            """
        try:
            with open(self.pdf_path, "rb") as f:
                pdf_data = f.read()

            model = genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content([
                {"mime_type": "application/pdf", "data": pdf_data},
                self.question
            ])

            self.result.emit(response.text)

        except Exception as e:
            self.result.emit(f"Hata: {e}")
            """
        #self.result.emit(response_area)
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
#
#GUI
#
#
class OrbitPDFApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Gemini client
        self.client = genai.Client(api_key="AIzaSyCL6rJwA89zqOPiIViuFNrskGl9GgEoet0")

        # durum değişkenleri
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

        soru = self.prompt_line.text()#--------------------------------------------------------------------

        # Hatalı 'if self.active_threads[0]...' yerine:
        if any(t.isRunning() for t in self.active_threads):
            self.response_area.setText("Hala çalışan bir işlem var, bekleyin...")
            return # Yeni işleme başlama, fonksiyondan çık
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
        self.response_area.setText("Sorgulanıyor...")#--------------------------------------------------------------------

    # sonucu GUI'de göster
    def show_result(self, text):
        self.response_area.setText(text)
    def start_thread_upload_pdf(self):
        if not self.selected_path :
            self.response_area.setText("Önce PDF seç!")
            return

        self.response_area.setText("PDF Gemini'ye yükleniyor...")

        try:
            # Hatalı 'if self.active_threads[0]...' yerine:
            if any(t.isRunning() for t in self.active_threads):
                self.response_area.setText("Hala çalışan bir işlem var, bekleyin...")
                return # Yeni işleme başlama, fonksiyondan çık
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
    """
    def upload_pdf(self):
        if not self.selected_path:
            self.response_area.setText("Önce PDF seç!")
            return

        self.response_area.setText("PDF Gemini'ye yükleniyor...")

        try:
            self.uploaded_file_ref = self.client.files.upload(#--------------------------------------------------------------------
                file=pathlib.Path(self.selected_path)
            )
            self.response_area.setText("PDF başarıyla yüklendi ✔")

        except Exception as e:
            self.response_area.setText(str(e))
            """

    # ---------------- SORU SOR ----------------
    """
    def ask_gemini(self):
        if not self.uploaded_file_ref:
            self.response_area.setText("Önce PDF yükle!")
            return

        soru = self.prompt_line.text().strip()
        if not soru:
            self.response_area.setText("Soru yazmalısın!")
            return

        self.response_area.setText("Gemini düşünüyor...")

        try:
            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[self.uploaded_file_ref, soru]
            )

            self.response_area.setText(response.text)

        except Exception as e:
            self.response_area.setText(str(e))
            """


# ---------------- APP ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OrbitPDFApp()
    window.show()
    sys.exit(app.exec())
#------------------------------------------------------------------------------------------------------------------------------------------------------------------
"""
client = genai.Client(api_key="AIzaSyCL6rJwA89zqOPiIViuFNrskGl9GgEoet0")

# Seçilen dosya yolunu ve yüklenen dosyayı saklamak için değişkenler
selected_path = None
uploaded_file_ref = None

def pdf_sec_fonksiyonu():
    global selected_path
    # getOpenFileName bir tuple döner: (dosya_yolu, filtre)
    dosya_bilgisi = QtWidgets.QFileDialog.getOpenFileName(
        None, 
        "Lütfen bir PDF dosyası seçin", 
        "", 
        "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
    )
    
    dosya_yolu = dosya_bilgisi[0] # Gerçek dosya yolunu buradan alıyoruz

    if dosya_yolu:
        selected_path = dosya_yolu # Global değişkene kaydet
        print(f"Dosya seçildi: {selected_path}")
    else:
        print("Dosya seçilmedi.")

def pdf_yukle_gemini():
    global uploaded_file_ref
    if selected_path:
        print(f"Gemini'ye yükleniyor: {selected_path}")
        # Dosyayı yüklüyoruz ve dönen referansı saklıyoruz
        uploaded_file_ref = client.files.upload(file=pathlib.Path(selected_path))
        print("Yükleme başarılı!")
    else:
        print("Hata: Önce 'Select Pdf' butonu ile bir dosya seçin!")
def start_thread():
    #a = int(self.input.text())

    thread = QThread()
    worker = Worker(selected_path,Prompt_enter_line)

    worker.moveToThread(thread)

    thread.started.connect(worker.run)
    worker.result.connect(show_result)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

def show_result(response):
    response_area.setText(response.text)
    """
"""
def prompt_gonder():
    if not uploaded_file_ref:
        print("Hata: Önce PDF yüklemeniz lazım!")
        return
    
    soru = Prompt_enter_line.text()
    if not soru:
        print("Lütfen bir soru yazın!")
        return

    print("Gemini yanıtlıyor...")
    response = client.models.generate_content(
        model="gemini-3-flash-preview", # En güncel stabil model
        contents=[uploaded_file_ref, soru]
    )
    print("--- YANIT ---")
    response_area.setText(response.text)
    print(response.text)
"""
"""
# UI Kurulumu
App = QtWidgets.QApplication(sys.argv)
Window = QtWidgets.QWidget()
Window.setWindowTitle("Orbit Soru Cevap (PDF)")

picture = QtWidgets.QLabel()
picture.setPixmap(QtGui.QPixmap("orbit1.png"))

Pdf_select_button = QtWidgets.QPushButton("Select Pdf")
Pdf_upload_button = QtWidgets.QPushButton("Upload Pdf")
Prompt_upload_button = QtWidgets.QPushButton("Ask Gemini")
Prompt_enter_line = QtWidgets.QLineEdit()
# UI kısmına ekle
response_area = QtWidgets.QTextEdit()
response_area.setReadOnly(True) # Kullanıcı içine elle yazı yazamasın, sadece okusun
response_area.setPlaceholderText("Gemini'nin cevabı burada görünecek...")
#
Prompt_enter_line.setPlaceholderText("Sorunuzu buraya yazın...")

# Layoutlar
hb = QtWidgets.QHBoxLayout()
hb.addWidget(Pdf_select_button)
hb.addWidget(Pdf_upload_button)
hb.addWidget(Prompt_upload_button)

vb = QtWidgets.QVBoxLayout()
vb.addWidget(picture)
vb.addWidget(response_area)
vb.addWidget(Prompt_enter_line)
vb.addLayout(hb)
Window.setLayout(vb)

# BUTON BAĞLANTILARI
# Fonksiyonların sonuna () koymuyoruz, sadece isimlerini veriyoruz!
Pdf_select_button.clicked.connect(pdf_sec_fonksiyonu)
Pdf_upload_button.clicked.connect(start_thread)
#Prompt_upload_button.clicked.connect(prompt_gonder)

Window.show()
sys.exit(App.exec())
#button.clicked.connect(start_thread)
#
#
#GUI
#
#
"""
