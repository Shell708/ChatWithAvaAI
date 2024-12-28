from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLineEdit, QLabel, QPushButton, QFileDialog, 
                             QGraphicsOpacityEffect, QTextBrowser, QScrollBar, QGraphicsDropShadowEffect, 
                             QStackedWidget, QDesktopWidget, QInputDialog, QDialog, QMessageBox, QToolBar, QAction, QProgressBar)
from PyQt5.QtGui import (QPixmap, QFont, QPainter, QColor, QLinearGradient, QImage, QPalette, QBrush,
                         QPainterPath, QRegion,)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QTimer, QUrl, 
                          QParallelAnimationGroup, QSequentialAnimationGroup, 
                          QThread, pyqtSignal, QSize, QPoint, QRectF, QTime)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import requests
from bs4 import BeautifulSoup
import sys
import google.generativeai as genai
import io
import base64
import traceback
import os


genai.configure(api_key='YOUR-API-KEY')


model = genai.GenerativeModel('gemini-2.0-flash-exp')

system_prompt = """
Your-System-Prompt-Here
"""



class AnimatedButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super(AnimatedButton, self).__init__(*args, **kwargs)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.animate_release()
        super().mouseReleaseEvent(event)

    def animate_press(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(100)
        anim.setStartValue(self.geometry())
        anim.setEndValue(self.geometry().adjusted(2, 2, -2, -2))
        anim.start()

    def animate_release(self):
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(100)
        anim.setStartValue(self.geometry())
        anim.setEndValue(self.geometry().adjusted(-2, -2, 2, 2))
        anim.start()

class CustomNameDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        self.setLayout(layout)

     
        welcome_label = QLabel("Welcome to Ava AI")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("""
            font-size: 24px;
            color: #4CAF50;
            margin-bottom: 20px;
        """)
        layout.addWidget(welcome_label)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 10px;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.8);
            }
            QLineEdit:focus {
                border-color: #45a049;
            }
        """)
        layout.addWidget(self.name_input)

       
        self.ok_button = QPushButton("Start Chat")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        layout.addWidget(self.ok_button)

    
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
    
    def fade_out(self):
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(1)
        self.opacity_animation.setEndValue(0)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.opacity_animation.finished.connect(self.close)
        self.opacity_animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

       
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)

   
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(240, 240, 240))
        gradient.setColorAt(1, QColor(220, 220, 220))

        painter.fillPath(path, gradient)

    def get_name(self):
        return self.name_input.text()

class ChatWindow(QMainWindow):
    def __init__(self, user_name):
        super().__init__()
        self.user_name = user_name
        self.chat_history = []
        self.setWindowTitle("Chat with Ava")
        self.resize(800, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
      
        self.setup_media_components()
        self.setup_ui_components()
        self.setup_animations()
        
        self.is_closing = False
        self.thinking_label = None
        
    
        self.center_on_screen()
        self.show_greeting()

    def web_search(self, query):
      try:
        url = f"https://www.google.com/search?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for g in soup.find_all('div', class_='g'):
            anchors = g.find_all('a')
            if anchors:
                link = anchors[0]['href']
                title = g.find('h3')
                if title:
                    title = title.text
                    snippet = g.find('div', class_='VwiC3b')
                    if snippet:
                        snippet = snippet.text
                        results.append(f"{title}\n{link}\n{snippet}\n")
        
        return "\n".join(results[:3])  
      except Exception as e:
        return f"An error occurred during the web search: {str(e)}"
    
    def setup_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                background-color: transparent;
                border: none;
            }
            QToolButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 15px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #45a049;
            }
        """)

      
        self.add_toolbar_action(toolbar, "Upload Image", self.upload_image)
        self.add_toolbar_action(toolbar, "Upload Audio", self.upload_audio)
        self.add_toolbar_action(toolbar, "Upload Video", self.upload_video)
        self.add_toolbar_action(toolbar, "Clear Chat", self.clear_chat)

        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def clear_chat(self):
        self.chat_display.clear()
        self.show_greeting()

    def add_toolbar_action(self, toolbar, text, slot):
        action = toolbar.addAction(text)
        action.triggered.connect(slot)

    def setup_media_components(self):
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

    def setup_ui_components(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Setup components
        self.setup_title_bar(layout)
        self.setup_toolbar()  # Add this line
        self.setup_chat_display(layout)
        self.setup_media_stack(layout)
        self.setup_input_area(layout)
        
        self.apply_styles()

    def setup_title_bar(self, layout):
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Logo
        self.logo_label = QLabel("Ava AI")
        self.logo_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        """)
        title_bar_layout.addWidget(self.logo_label)

      
        title_bar_layout.addStretch()

       
        self.minimize_button = QPushButton("—")
        self.close_button = QPushButton("×")
        for button in (self.minimize_button, self.close_button):
            button.setFixedSize(30, 30)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4CAF50;
                    font-size: 16px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(76, 175, 80, 0.1);
                }
            """)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.close_button.clicked.connect(self.close)

        title_bar_layout.addWidget(self.minimize_button)
        title_bar_layout.addWidget(self.close_button)

        layout.addWidget(title_bar)

    def setup_logo(self, layout):
        self.logo_label = QLabel(self)
        logo_path = 'your-path-to-logo'  
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("Isaac's GF")
            self.logo_label.setStyleSheet("""
                font-size: 32px;
                font-weight: bold;
                color: #4CAF50;
            """)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFixedSize(120, 120)
        layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)

    def setup_chat_display(self, layout):
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 10px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.chat_display)

    def setup_media_stack(self, layout):
        self.media_stack = QStackedWidget()
        self.media_stack.addWidget(QWidget()) 
        self.media_stack.addWidget(self.video_widget)
        layout.addWidget(self.media_stack)

    def setup_input_area(self, layout):
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #dcdcdc;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgba(240, 240, 240, 230);
                border-radius: 20px;
            }
        """)

    def setup_animations(self):
        self.setWindowOpacity(0)
        
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        QTimer.singleShot(100, self.opacity_animation.start)

    def show_greeting(self):
        if self.user_name.lower() == "Your-Name-Here":
            greeting = f"Special-Greting-Here"
        else:
            greeting = f"Ava: Hello {self.user_name}. How can I assist you today?"
        self.add_message(greeting, '#4CAF50')

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, 20, 20)
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(240, 240, 240, 230))
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def closeEvent(self, event):
        if not hasattr(self, 'is_closing'):
            self.is_closing = False
        
        if not self.is_closing:
            self.is_closing = True
            self._fadeout()
            event.ignore()
        else:
            event.accept()
    
    def _fadeout(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(500)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_anim.finished.connect(self.finalize_close)
        self.fade_out_anim.start()

    def finalize_close(self):
        self.close()


    def send_message(self):
        user_input = self.input_field.text().strip()
        if user_input:
            self.add_message(f"You: {user_input}", '#1E88E5')
            self.input_field.clear()
            self.thinking_animation()
            QTimer.singleShot(1000, lambda: self.process_response(user_input))

    def add_message(self, message, color):
     current_time = QTime.currentTime().toString("hh:mm")
     formatted_message = f'<div style="margin-bottom: 10px;"><span style="color: #888888;">[{current_time}]</span> <span style="color: {color};">{message}</span></div>'
     self.chat_display.append(formatted_message)
     self.chat_display.moveCursor(self.chat_display.textCursor().End)
     self.chat_display.ensureCursorVisible()
     self.chat_history.append(message)  
     QApplication.processEvents()

    def thinking_animation(self):
        if self.thinking_label:
            self.statusBar().removeWidget(self.thinking_label)
            self.thinking_label.deleteLater()

        self.thinking_label = QLabel("Ava is thinking")
        self.thinking_label.setStyleSheet("""
            color: #4CAF50;
            font-style: italic;
        """)
        self.statusBar().addWidget(self.thinking_label)

        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_text)
        self.thinking_timer.start(500)

        self.opacity_effect = QGraphicsOpacityEffect(self.thinking_label)
        self.thinking_label.setGraphicsEffect(self.opacity_effect)

        self.pulse_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setStartValue(0.5)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setLoopCount(-1)
        self.pulse_animation.start()

    def update_thinking_text(self):
        current_text = self.thinking_label.text()
        if current_text.endswith("..."):
            self.thinking_label.setText("Ava is thinking")
        else:
            self.thinking_label.setText(current_text + ".")

    def process_response(self, user_input):
      try:
        if "search" in user_input.lower():
            self.add_message("Ava: Searching the web for you...", '#4CAF50')
            search_query = user_input.replace("search", "").strip()
            search_result = self.web_search(search_query)
            
            if search_result:
                response = f"Here's what I found about '{search_query}':\n\n{search_result}"
            else:
                response = f"I'm sorry, I couldn't find any relevant information about '{search_query}'."
            
            self.add_message(f"Ava: {response}", '#4CAF50')
        else:
            
            current_system_prompt = system_prompt + """
            Current_system_prompt_here
            """

            
            context = "\n".join(self.chat_history[-5:])
            full_prompt = f"{current_system_prompt}\n\nConversation context:\n{context}\n\nIsaac: {user_input}\nAva:"
            
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=150,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40
                )
            )
            response_text = response.text.strip()
            self.add_message(f"Ava: {response_text}", '#4CAF50')
        
     
        self.chat_history.append(f"Isaac: {user_input}")
        self.chat_history.append(f"Ava: {response_text}")
        
      except Exception as e:
        self.add_message(f"Ava: I'm sorry, I encountered an error: {str(e)}", '#FF0000')
      finally:
        if self.thinking_label:
            self.statusBar().removeWidget(self.thinking_label)
            self.thinking_label.deleteLater()
            self.thinking_label = None
        if self.thinking_timer:
            self.thinking_timer.stop()
        if self.pulse_animation:
            self.pulse_animation.stop()
            self.pulse_animation.deleteLater()
        if hasattr(self, 'opacity_effect'):
            self.opacity_effect.deleteLater()
    QApplication.processEvents()

    def upload_image(self):
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if image_path:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                image = QImage.fromData(image_data)
                if not image.isNull():
                    self.add_message("You: [Uploaded an image]", '#1E88E5')
                    self.process_image(image_data)
                else:
                    self.add_message("Error: Unable to load the image.", '#FF0000')

    def process_image(self, image_data):
        base64_image = base64.b64encode(image_data).decode('utf-8')
        try:
            vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = vision_model.generate_content([
                "Analyze this image and describe what you see:",
                {"mime_type": "image/jpeg", "data": base64_image}
            ])
            self.add_message(f"Ava: {response.text}", '#4CAF50')
        except Exception as e:
            self.add_message(f"Ava: Sorry, I encountered an error processing the image: {str(e)}", '#FF0000')

    def upload_audio(self):
     file_dialog = QFileDialog()
     audio_path, _ = file_dialog.getOpenFileName(self, "Select Audio", "", "Audio Files (*.mp3 *.wav *.ogg)")
     if audio_path:
        self.add_message("You: [Uploaded an audio file]", '#1E88E5')
        self.process_audio(audio_path)

    def upload_video(self):
     file_dialog = QFileDialog()
     video_path, _ = file_dialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
     if video_path:
        self.add_message("You: [Uploaded a video file]", '#1E88E5')
        self.process_video(video_path)

    def process_audio(self, audio_path):
     file_name = os.path.basename(audio_path)
     file_size = os.path.getsize(audio_path)
     file_size_mb = file_size / (1024 * 1024)  

     response = f"I've received your audio file '{file_name}'. It's approximately {file_size_mb:.2f} MB in size. " \
                f"While I can't listen to or analyze its contents directly, I can provide information about audio files " \
                f"if you have any questions. What would you like to know about this audio file or audio processing in general?"
 
     self.add_message(f"Ava: {response}", '#4CAF50')

    def process_video(self, video_path):
     file_name = os.path.basename(video_path)
     file_size = os.path.getsize(video_path)
     file_size_mb = file_size / (1024 * 1024)  

     response = f"I've received your video file '{file_name}'. It's approximately {file_size_mb:.2f} MB in size. " \
                f"While I can't watch or analyze its contents directly, I can provide information about video files " \
                f"if you have any questions. What would you like to know about this video file or video processing in general?"

     self.add_message(f"Ava: {response}", '#4CAF50')

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading Ava AI")
        self.setFixedSize(400, 300)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Logo
        self.logo_label = QLabel()
        logo_path = 'path/to/your/logo.png'  
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("Ava AI")
            self.logo_label.setStyleSheet("""
                font-size: 36px;
                font-weight: bold;
                color: #4CAF50;
            """)
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

       
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            font-size: 18px;
            color: #4CAF50;
            margin-top: 20px;
        """)
        layout.addWidget(self.loading_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4CAF50;
                border-radius: 5px;
                background-color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
        layout.addWidget(self.progress_bar)

        
        self.start_animations()

    def start_animations(self):
        
        self.setWindowOpacity(0)
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(1000)
        self.fade_in_anim.setStartValue(0)
        self.fade_in_anim.setEndValue(1)
        self.fade_in_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_in_anim.start()

       
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_anim.setDuration(3000)  # 3 seconds
        self.progress_anim.setStartValue(0)
        self.progress_anim.setEndValue(100)
        self.progress_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_anim.start()

        
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading_text)
        self.loading_timer.start(500)

    def update_loading_text(self):
        current_text = self.loading_label.text()
        if current_text.endswith("..."):
            self.loading_label.setText("Loading")
        else:
            self.loading_label.setText(current_text + ".")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

       
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 20, 20)

       
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(240, 240, 240, 230))
        gradient.setColorAt(1, QColor(220, 220, 220, 230))

        painter.fillPath(path, gradient)

    def setup_animations(self):
        self.logo_animation = QPropertyAnimation(self.logo_label, b"geometry")
        self.logo_animation.setDuration(1500)
        self.logo_animation.setLoopCount(-1)
        self.logo_animation.setKeyValueAt(0, self.logo_label.geometry())
        self.logo_animation.setKeyValueAt(0.5, self.logo_label.geometry().adjusted(-10, -10, 10, 10))
        self.logo_animation.setKeyValueAt(1, self.logo_label.geometry())

        self.text_animation = QPropertyAnimation(self.loading_label, b"geometry")
        self.text_animation.setDuration(1000)
        self.text_animation.setLoopCount(-1)
        self.text_animation.setKeyValueAt(0, self.loading_label.geometry())
        self.text_animation.setKeyValueAt(0.5, self.loading_label.geometry().adjusted(0, -5, 0, -5))
        self.text_animation.setKeyValueAt(1, self.loading_label.geometry())

        self.logo_animation.start()
        self.text_animation.start()

    def fadeOut(self):
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(1000)
        self.fade_out_anim.setStartValue(1)
        self.fade_out_anim.setEndValue(0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_out_anim.finished.connect(self.close)
        self.fade_out_anim.start()

def main():
    app = QApplication(sys.argv)
    
   
    loading_screen = LoadingScreen()
    loading_screen.show()
    
    def show_name_dialog():
        name_dialog = CustomNameDialog()
        if name_dialog.exec_() == QDialog.Accepted:
            user_name = name_dialog.get_name()
            if user_name:
                try:
                    window = ChatWindow(user_name)
                    window.show()
                except Exception as e:
                    print(f"Error creating chat window: {str(e)}")
                    error_dialog = QMessageBox()
                    error_dialog.setIcon(QMessageBox.Critical)
                    error_dialog.setText("An error occurred while starting the chat.")
                    error_dialog.setInformativeText(f"Error details: {str(e)}")
                    error_dialog.setWindowTitle("Error")
                    error_dialog.exec_()
                    sys.exit(1)
            else:
                print("No name entered. Exiting.")
                sys.exit()
        else:
            print("Name dialog cancelled. Exiting.")
            sys.exit()
    
    loading_screen.fade_out_anim.finished.connect(show_name_dialog)
    QTimer.singleShot(3000, loading_screen.fadeOut)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        
        loading_screen = LoadingScreen()
        loading_screen.show()
        
        def start_chat():
            try:
                name_dialog = CustomNameDialog()
                if name_dialog.exec_() == QDialog.Accepted:
                    user_name = name_dialog.get_name()
                    if user_name:
                        chat_window = ChatWindow(user_name)
                        loading_screen.fadeOut()
                        loading_screen.fade_out_anim.finished.connect(chat_window.show)
                    else:
                        QMessageBox.warning(None, "Error", "Please enter a valid name.")
                        QTimer.singleShot(0, start_chat)
                else:
                    app.quit()
            except Exception as e:
                QMessageBox.critical(None, "Error", f"An error occurred: {str(e)}\n\n{traceback.format_exc()}")
                app.quit()

        QTimer.singleShot(3000, start_chat)  
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)