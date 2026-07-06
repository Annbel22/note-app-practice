import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QSplitter, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Блокнот с заметками")
        self.resize(1000, 700)
        self.setMinimumSize(800, 500)

        self.db = database.DatabaseManager()
        self.current_note_id = None
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self._auto_save)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._setup_ui()
        self._bind_signals()
        self._refresh_notes_list()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    def _setup_ui(self):
        main_layout = QHBoxLayout()
        self.centralWidget().setLayout(main_layout)

        # Левая панель
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по заметкам...")
        left_layout.addWidget(self.search_edit)

        self.notes_list = QListWidget()
        left_layout.addWidget(self.notes_list)

        btn_layout = QHBoxLayout()
        self.btn_new = QPushButton("Новая заметка")
        self.btn_delete = QPushButton("Удалить")
        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_delete)
        left_layout.addLayout(btn_layout)

        # Правая панель
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Заголовок заметки")
        right_layout.addWidget(self.title_edit)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Введите текст заметки...")
        right_layout.addWidget(self.content_edit)

        image_layout = QHBoxLayout()
        self.image_label = QLabel("Обложка заметки")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(150)
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 5px;")
        self.btn_load_image = QPushButton("Загрузить изображение")
        self.btn_clear_image = QPushButton("Убрать изображение")
        image_layout.addWidget(self.image_label)
        image_layout.addWidget(self.btn_load_image)
        image_layout.addWidget(self.btn_clear_image)
        right_layout.addLayout(image_layout)

        self.word_count_label = QLabel("Слов: 0")
        right_layout.addWidget(self.word_count_label)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])
        main_layout.addWidget(splitter)

        # QSS-стилизация
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #a8c4e0;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #aaa;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed { background-color: #c0c0c0; }
            QLabel { color: #333; }
        """)

    def _bind_signals(self):
        self.btn_new.clicked.connect(self._on_new_note)
        self.btn_delete.clicked.connect(self._on_delete_note)
        self.btn_load_image.clicked.connect(self._on_load_image)
        self.btn_clear_image.clicked.connect(self._on_clear_image)

        self.notes_list.itemSelectionChanged.connect(self._on_select_note)
        self.search_edit.textChanged.connect(self._on_search)

        self.title_edit.textChanged.connect(self._on_content_changed)
        self.content_edit.textChanged.connect(self._on_content_changed)

    def _on_content_changed(self):
        text = self.content_edit.toPlainText()
        word_count = len(text.split()) if text else 0
        self.word_count_label.setText(f"Слов: {word_count}")

        if self.current_note_id is not None:
            self.auto_save_timer.start(2000)

    def _auto_save(self):
        if self.current_note_id is None:
            return
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText()
        self.db.update(self.current_note_id, title, content)
        self._refresh_notes_list(keep_selection=True)
        self.status_bar.showMessage("Заметка сохранена", 2000)

    def _refresh_notes_list(self, keep_selection=False):
        current_id = self.current_note_id
        self.notes_list.clear()
        notes = self.db.get_all()
        for note in notes:
            item = QListWidgetItem(note["title"] if note["title"] else "Без заголовка")
            item.setData(Qt.UserRole, note["id"])
            self.notes_list.addItem(item)

        if keep_selection and current_id is not None:
            for i in range(self.notes_list.count()):
                if self.notes_list.item(i).data(Qt.UserRole) == current_id:
                    self.notes_list.setCurrentRow(i)
                    break
        else:
            if self.notes_list.count() > 0:
                self.notes_list.setCurrentRow(0)
            else:
                self._clear_fields()

    def _on_select_note(self):
        if self.current_note_id is not None:
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
                self._auto_save()

        selected = self.notes_list.selectedItems()
        if not selected:
            self._clear_fields()
            self.current_note_id = None
            return

        item = selected[0]
        note_id = item.data(Qt.UserRole)
        note = self.db.get_by_id(note_id)
        if note is None:
            return

        self.current_note_id = note_id
        self.title_edit.setText(note["title"] or "")
        self.content_edit.setPlainText(note["content"] or "")
        text = note["content"] or ""
        self.word_count_label.setText(f"Слов: {len(text.split())}")

        if note["image_path"] and os.path.exists(note["image_path"]):
            self._set_image_from_path(note["image_path"])
        else:
            self.image_label.setText("Обложка заметки")
            self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 5px;")

        self.status_bar.showMessage(f"Заметка #{note_id} загружена")

    def _clear_fields(self):
        self.title_edit.clear()
        self.content_edit.clear()
        self.word_count_label.setText("Слов: 0")
        self.image_label.setText("Обложка заметки")
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 5px;")
        self.current_note_id = None

    def _on_new_note(self):
        note_id = self.db.insert("Новая заметка", "")
        self._refresh_notes_list(keep_selection=False)
        for i in range(self.notes_list.count()):
            if self.notes_list.item(i).data(Qt.UserRole) == note_id:
                self.notes_list.setCurrentRow(i)
                break
        self.title_edit.setFocus()
        self.title_edit.selectAll()
        self.status_bar.showMessage("Создана новая заметка", 2000)

    def _on_delete_note(self):
        if self.current_note_id is None:
            QMessageBox.warning(self, "Внимание", "Выберите заметку для удаления.")
            return
        reply = QMessageBox.question(self, "Подтверждение",
                                      "Удалить выбранную заметку?",
                                      QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete(self.current_note_id)
            self.current_note_id = None
            self._refresh_notes_list()
            self.status_bar.showMessage("Заметка удалена", 2000)

    def _on_load_image(self):
        if self.current_note_id is None:
            QMessageBox.warning(self, "Внимание", "Сначала выберите или создайте заметку.")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            return
        try:
            self.db.update(
                self.current_note_id,
                self.title_edit.text().strip(),
                self.content_edit.toPlainText(),
                image_path=file_path
            )
            self._set_image_from_path(file_path)
            self.status_bar.showMessage("Изображение загружено", 2000)
            self._refresh_notes_list(keep_selection=True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить изображение:\n{e}")

    def _on_clear_image(self):
        if self.current_note_id is None:
            return
        self.db.update(
            self.current_note_id,
            self.title_edit.text().strip(),
            self.content_edit.toPlainText(),
            image_path=None
        )
        self.image_label.setText("Обложка заметки")
        self.image_label.setStyleSheet("background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 5px;")
        self.status_bar.showMessage("Изображение убрано", 2000)

    def _set_image_from_path(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((200, 200), Image.LANCZOS)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimage)
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(False)
            self.image_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #aaa; border-radius: 5px;")
        except Exception as e:
            self.image_label.setText("Ошибка загрузки")
            QMessageBox.warning(self, "Ошибка", f"Не удалось отобразить изображение:\n{e}")

    def _on_search(self, text):
        if not text.strip():
            self._refresh_notes_list(keep_selection=True)
            return
        notes = self.db.search(text.strip())
        self.notes_list.clear()
        for note in notes:
            item = QListWidgetItem(note["title"] if note["title"] else "Без заголовка")
            item.setData(Qt.UserRole, note["id"])
            self.notes_list.addItem(item)
        if self.notes_list.count() > 0:
            self.notes_list.setCurrentRow(0)
        else:
            self._clear_fields()

    def closeEvent(self, event):
        if self.current_note_id is not None:
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
                self._auto_save()
        reply = QMessageBox.question(self, "Выход", "Выйти из приложения?",
                                      QMessageBox.Yes | QMessageBox.No,
                                      QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()
