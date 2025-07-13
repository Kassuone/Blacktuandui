import sys
import os
import random
import tempfile
import base64
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox,
                             QSlider, QColorDialog, QFileDialog, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPointF, QBuffer, QByteArray, QIODevice
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QFont, QFontMetrics, QImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import svgwrite


class SignatureGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级电子商务签名生成器")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #34495e;
                color: #ecf0f1;
                font-family: 'Segoe UI';
                font-size: 12px;
            }
            QGroupBox {
                border: 1px solid #3498db;
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                color: #3498db;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
            QLineEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2c3e50;
                color: #ecf0f1;
                selection-background-color: #3498db;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3498db;
                height: 8px;
                background: #2c3e50;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 18px;
                margin: -4px 0;
                border-radius: 9px;
            }
        """)

        self.signature_text = "电子商务签名"
        self.signature_style = "优雅型"
        self.signature_color = QColor(50, 50, 50)
        self.font_size = 48
        self.stroke_width = 2.0
        self.ink_flow = 0.8

        self.initUI()
        self.generate_signature()

    def initUI(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # 左侧控制面板
        control_panel = QGroupBox("签名设置")
        control_layout = QVBoxLayout()

        # 签名文本
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("签名文本:"))
        self.text_edit = QLineEdit(self.signature_text)
        self.text_edit.textChanged.connect(self.on_text_changed)
        text_layout.addWidget(self.text_edit)
        control_layout.addLayout(text_layout)

        # 签名风格
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("签名风格:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["优雅型", "商务型", "艺术型", "现代型", "手写型"])
        self.style_combo.setCurrentText(self.signature_style)
        self.style_combo.currentTextChanged.connect(self.on_style_changed)
        style_layout.addWidget(self.style_combo)
        control_layout.addLayout(style_layout)

        # 字体大小
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("字体大小:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(24, 96)
        self.size_slider.setValue(self.font_size)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.size_slider)
        size_layout.addWidget(QLabel(f"{self.font_size}px"))
        self.size_label = size_layout.itemAt(2).widget()
        control_layout.addLayout(size_layout)

        # 笔画粗细
        stroke_layout = QHBoxLayout()
        stroke_layout.addWidget(QLabel("笔画粗细:"))
        self.stroke_slider = QSlider(Qt.Horizontal)
        self.stroke_slider.setRange(1, 100)
        self.stroke_slider.setValue(int(self.stroke_width * 20))
        self.stroke_slider.valueChanged.connect(self.on_stroke_changed)
        stroke_layout.addWidget(self.stroke_slider)
        stroke_layout.addWidget(QLabel(f"{self.stroke_width:.1f}"))
        self.stroke_label = stroke_layout.itemAt(2).widget()
        control_layout.addLayout(stroke_layout)

        # 墨水流动
        ink_layout = QHBoxLayout()
        ink_layout.addWidget(QLabel("墨水流动:"))
        self.ink_slider = QSlider(Qt.Horizontal)
        self.ink_slider.setRange(0, 100)
        self.ink_slider.setValue(int(self.ink_flow * 100))
        self.ink_slider.valueChanged.connect(self.on_ink_changed)
        ink_layout.addWidget(self.ink_slider)
        ink_layout.addWidget(QLabel(f"{self.ink_flow:.1f}"))
        self.ink_label = ink_layout.itemAt(2).widget()
        control_layout.addLayout(ink_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("签名颜色:"))
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(30, 30)
        self.color_btn.setStyleSheet(f"background-color: {self.signature_color.name()};")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(QLabel(self.signature_color.name()))
        self.color_label = color_layout.itemAt(2).widget()
        control_layout.addLayout(color_layout)

        # 导出格式
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("导出格式:"))
        self.export_combo = QComboBox()
        self.export_combo.addItems(["PNG", "JPG", "SVG", "PDF", "BMP", "TIFF", "GIF"])
        export_layout.addWidget(self.export_combo)
        control_layout.addLayout(export_layout)

        # 按钮
        button_layout = QHBoxLayout()
        self.generate_btn = QPushButton("生成签名")
        self.generate_btn.clicked.connect(self.generate_signature)
        button_layout.addWidget(self.generate_btn)

        self.export_btn = QPushButton("导出签名")
        self.export_btn.clicked.connect(self.export_signature)
        button_layout.addWidget(self.export_btn)

        control_layout.addLayout(button_layout)

        control_panel.setLayout(control_layout)

        # 右侧预览区域
        preview_panel = QGroupBox("签名预览")
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(500, 300)
        self.preview_label.setStyleSheet("background-color: white; border: 1px solid #3498db;")
        preview_layout.addWidget(self.preview_label)

        preview_panel.setLayout(preview_layout)

        # 添加面板到主布局
        main_layout.addWidget(control_panel, 1)
        main_layout.addWidget(preview_panel, 2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def on_text_changed(self, text):
        self.signature_text = text
        self.generate_signature()

    def on_style_changed(self, style):
        self.signature_style = style
        self.generate_signature()

    def on_size_changed(self, size):
        self.font_size = size
        self.size_label.setText(f"{size}px")
        self.generate_signature()

    def on_stroke_changed(self, value):
        self.stroke_width = value / 20.0
        self.stroke_label.setText(f"{self.stroke_width:.1f}")
        self.generate_signature()

    def on_ink_changed(self, value):
        self.ink_flow = value / 100.0
        self.ink_label.setText(f"{self.ink_flow:.1f}")
        self.generate_signature()

    def choose_color(self):
        color = QColorDialog.getColor(self.signature_color, self, "选择签名颜色")
        if color.isValid():
            self.signature_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.color_label.setText(color.name())
            self.generate_signature()

    def generate_signature(self):
        try:
            # 创建签名图像
            width, height = 600, 300
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(Qt.transparent)

            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)

            # 根据选择的风格应用不同的字体
            fonts = {
                "优雅型": ("Script MT Bold", True),
                "商务型": ("Brush Script MT", True),
                "艺术型": ("Lucida Handwriting", True),
                "现代型": ("Segoe Script", True),
                "手写型": ("Bradley Hand ITC", True)
            }

            font_name, italic = fonts.get(self.signature_style, ("Segoe Script", True))
            font = QFont(font_name, self.font_size)
            font.setItalic(italic)
            font.setBold(True)
            painter.setFont(font)

            # 设置画笔 - 创建真实感效果
            pen = QPen(self.signature_color)
            pen.setWidthF(self.stroke_width)
            painter.setPen(pen)

            # 计算文本位置
            fm = QFontMetrics(font)
            text_width = fm.width(self.signature_text)
            text_height = fm.height()
            x = (width - text_width) / 2
            y = (height - text_height) / 2 + fm.ascent()

            # 添加手写效果 - 随机变化
            for i, char in enumerate(self.signature_text):
                char_x = x + fm.width(self.signature_text[:i])
                char_y = y

                # 添加微小的随机偏移，模拟手写
                offset_x = random.uniform(-1, 1) * self.ink_flow
                offset_y = random.uniform(-1, 1) * self.ink_flow

                # 添加笔画宽度变化
                if random.random() < 0.3:
                    pen.setWidthF(self.stroke_width * random.uniform(0.8, 1.2))
                    painter.setPen(pen)

                painter.drawText(QPointF(char_x + offset_x, char_y + offset_y), char)

            painter.end()

            # 显示预览
            pixmap = QPixmap.fromImage(image)
            self.preview_label.setPixmap(pixmap)
            self.current_signature = image
        except Exception as e:
            QMessageBox.critical(self, "生成错误", f"生成签名时出错: {str(e)}")

    def export_signature(self):
        if not hasattr(self, 'current_signature'):
            QMessageBox.warning(self, "警告", "请先生成签名")
            return

        format = self.export_combo.currentText().lower()
        file_filter = f"{format.upper()} 文件 (*.{format})"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存签名", f"{self.signature_text}_signature.{format}", file_filter
        )

        if not file_path:
            return

        try:
            # 保存为不同格式
            if format in ["png", "jpg", "bmp", "tiff", "gif"]:
                self.current_signature.save(file_path, format.upper())
            elif format == "svg":
                self.save_as_svg(file_path)
            elif format == "pdf":
                self.save_as_pdf(file_path)

            QMessageBox.information(self, "导出成功", f"签名已成功导出为 {format.upper()} 格式")
        except Exception as e:
            QMessageBox.critical(self, "导出错误", f"导出签名时出错: {str(e)}")

    def save_as_svg(self, file_path):
        """保存为SVG格式（使用base64嵌入PNG图像）"""
        # 将QImage转换为PNG数据
        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(QIODevice.WriteOnly)
        self.current_signature.save(buffer, "PNG")
        buffer.close()

        # 转换为base64字符串
        base64_data = ba.toBase64().data().decode('utf-8')

        # 获取图像尺寸
        width, height = self.current_signature.width(), self.current_signature.height()

        # 创建SVG文档
        dwg = svgwrite.Drawing(file_path, size=(f"{width}px", f"{height}px"))

        # 添加图像元素
        image = dwg.image(
            href=f"data:image/png;base64,{base64_data}",
            insert=(0, 0),
            size=(f"{width}px", f"{height}px")
        )
        dwg.add(image)
        dwg.save()

    def save_as_pdf(self, file_path):
        """保存为PDF格式"""
        width, height = self.current_signature.width(), self.current_signature.height()

        # 创建临时PNG文件
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            self.current_signature.save(tmp_path, "PNG")

        try:
            # 使用ReportLab创建PDF
            c = canvas.Canvas(file_path, pagesize=(width, height))
            c.drawImage(tmp_path, 0, 0, width=width, height=height)
            c.save()
        finally:
            # 确保删除临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SignatureGenerator()
    window.show()
    sys.exit(app.exec_())