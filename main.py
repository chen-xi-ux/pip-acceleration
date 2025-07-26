import sys
import time
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QGroupBox, QTableWidget,
    QTableWidgetItem, QProgressBar, QMessageBox, QButtonGroup,
    QCheckBox, QHeaderView, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import os
import configparser

class PingThread(QThread):  # 修复了类名错误，移除了重复的PingThread
    """用于测试镜像站延迟的线程类"""
    update_signal = pyqtSignal(str, str, float)  # 发送更新信号 (名称, URL, 延迟)
    finish_signal = pyqtSignal()  # 发送完成信号

    def __init__(self, mirrors):
        super().__init__()
        self.mirrors = mirrors
        self.running = True

    def run(self):
        """线程运行函数，测试所有镜像站的延迟"""
        for name, url in self.mirrors.items():
            if not self.running:
                break
            try:
                start_time = time.time()
                # 发送HEAD请求测试连接
                response = requests.head(url, timeout=5, allow_redirects=True)
                end_time = time.time()
                
                # 计算延迟(毫秒)
                if response.status_code < 400:
                    delay = (end_time - start_time) * 1000
                    self.update_signal.emit(name, url, delay)
                else:
                    self.update_signal.emit(name, url, -1)  # 状态码错误
            except Exception:
                self.update_signal.emit(name, url, -1)  # 连接失败
            time.sleep(0.1)  # 避免请求过于密集
        self.finish_signal.emit()

    def stop(self):
        """停止线程"""
        self.running = False
        self.wait()


class PipSourceManager(QMainWindow):
    """Pip源管理工具主窗口类"""
    def __init__(self):
        super().__init__()
        # 镜像站列表
        self.mirrors = {
            "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
            "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple/",
            "网易": "https://mirrors.163.com/pypi/simple/",
            "清华大学（TUNA）": "https://pypi.tuna.tsinghua.edu.cn/simple/",
            "中国科学技术大学（USTC）": "https://pypi.mirrors.ustc.edu.cn/simple/",
            "北京大学": "https://mirrors.pku.edu.cn/pypi/simple/",
            "火山引擎": "https://mirrors.volces.com/pypi/simple/",
            "浙江大学": "https://mirrors.zju.edu.cn/pypi/web/simple/",
            "Python官方": "https://pypi.org/simple/"
        }
        self.delays = []  # 存储延迟测试结果
        self.multi_mirror_checkboxes = {}  # 多源选择框字典
        self.base_font_size = 10  # 基础字体大小
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        # 主窗口大小设置
        self.setWindowTitle("PIP源管理工具-项目遵循GPL-3.0许可-开源地址：https://github.com/chen-xi-ux/pip-acceleration")
        self.resize(1200, 700)
        self.setMinimumSize(800, 500)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局（水平布局，左右分栏）
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 创建界面元素
        self.create_widgets()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        self.apply_styles()
        self.detect_current_settings()
        
        # 初始调整大小
        self.adjust_elements_size()

    def create_widgets(self):
        """创建所有界面元素"""
        # 左侧测速面板
        left_panel = self.create_test_panel()
        self.main_layout.addWidget(left_panel, stretch=3)

        # 右侧侧设置面板（使用滚动区域，避免内容溢出）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        right_panel = self.create_settings_panel()
        scroll_layout.addWidget(right_panel)
        scroll_area.setWidget(scroll_content)
        
        self.main_layout.addWidget(scroll_area, stretch=2)

    def create_test_panel(self):
        """创建测速面板"""
        panel = QGroupBox("镜像站测速与排序")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(8)

        # 测试按钮 - 重点放大
        self.test_button = QPushButton("测试所有镜像站延迟（自动排序）")
        self.test_button.clicked.connect(self.start_test)
        self.test_button.setMinimumSize(300, 30)  # 宽度300，高度30
        panel_layout.addWidget(self.test_button)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        panel_layout.addWidget(self.progress_bar)

        # 测速结果表格
        self.mirror_table = QTableWidget()
        self.mirror_table.setColumnCount(3)
        # 修复拼写错误：setHorizontaladerLabels -> setHorizontalHeaderLabels
        self.mirror_table.setHorizontalHeaderLabels(["镜像站名称", "镜像站地址", "延迟(ms)"])
        self.mirror_table.setEditTriggers(QTableWidget.NoEditTriggers)  # 禁止编辑
        # 表格列宽设置
        self.mirror_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.mirror_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mirror_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.mirror_table.setAlternatingRowColors(True)  # 隔行变色
        panel_layout.addWidget(self.mirror_table)

        # 最快镜像站显示
        self.fastest_label = QLabel("最快的镜像站: 未测试")
        self.fastest_label.setAlignment(Qt.AlignCenter)
        panel_layout.addWidget(self.fastest_label)
        self.show_large_button_message("提示", "项目遵循GPL-3.0许可", QMessageBox.Warning)
        self.show_large_button_message("提示", "开源地址：https://github.com/chen-xi-ux/pip-acceleration", QMessageBox.Warning)
        return panel

    def create_settings_panel(self):
        """创建设置面板"""
        panel = QGroupBox("源设置")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(8)

        # 模式选择
        mode_group = QGroupBox("选择模式")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(5)

        self.single_radio = QRadioButton("单源模式")
        self.single_radio.setChecked(True)
        self.single_radio.toggled.connect(self.on_mode_changed)

        self.multi_radio = QRadioButton("多源模式(轮询)")

        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multi_radio)
        panel_layout.addWidget(mode_group)

        # 单源选择
        self.single_group = QGroupBox("单源选择（按延迟排序）")
        single_inner_layout = QVBoxLayout()
        single_inner_layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
        single_inner_layout.setSpacing(5)
        single_inner_layout.setContentsMargins(10, 5, 10, 5)

        self.single_mirror_group = QButtonGroup()
        self.single_mirror_buttons = {}
        for name, url in self.mirrors.items():
            radio = QRadioButton(f"{name}")
            self.single_mirror_group.addButton(radio)
            self.single_mirror_buttons[name] = (radio, url)
            single_inner_layout.addWidget(radio)
        self.single_group.setLayout(single_inner_layout)
        panel_layout.addWidget(self.single_group)

        # 多源选择
        self.multi_group = QGroupBox("多源选择（按延迟排序）")
        self.multi_group.setEnabled(False)  # 初始禁用
        multi_inner_layout = QVBoxLayout()
        multi_inner_layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
        multi_inner_layout.setSpacing(5)
        multi_inner_layout.setContentsMargins(10, 5, 10, 5)

        help_label = QLabel("推荐选择3-5个速度较快的源")
        multi_inner_layout.addWidget(help_label)

        # 添加多源选择框
        for name, url in self.mirrors.items():
            checkbox = QCheckBox(f"{name}")
            self.multi_mirror_checkboxes[name] = (checkbox, url)
            multi_inner_layout.addWidget(checkbox)
        self.multi_group.setLayout(multi_inner_layout)
        panel_layout.addWidget(self.multi_group)

        # 操作按钮 - 重点放大
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 增加按钮间距

        self.apply_button = QPushButton("应用设置")
        self.apply_button.clicked.connect(self.apply_settings)
        self.apply_button.setMinimumSize(110, 30)  # 宽度110，高度30

        self.reset_button = QPushButton("恢复默认")
        self.reset_button.clicked.connect(self.reset_settings)
        self.reset_button.setMinimumSize(110, 30)  # 宽度110，高度30

        self.view_config_button = QPushButton("查看配置文件")
        self.view_config_button.clicked.connect(self.view_config_file)
        self.view_config_button.setMinimumSize(130, 30)  # 宽度130，高度30

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.view_config_button)
        panel_layout.addLayout(button_layout)

        # 当前设置显示
        current_label = QLabel("当前配置:")
        panel_layout.addWidget(current_label)

        self.current_source = QLabel("未检测到自定义源")
        self.current_source.setWordWrap(True)
        panel_layout.addWidget(self.current_source)

        # 配置路径显示
        path_label = QLabel("配置文件路径:")
        panel_layout.addWidget(path_label)

        self.config_path_label = QLabel("")
        panel_layout.addWidget(self.config_path_label)

        # 添加伸缩项
        panel_layout.addStretch(1)
        
        return panel

    def resizeEvent(self, event):
        """重写窗口大小改变事件"""
        super().resizeEvent(event)
        self.adjust_elements_size()

    def adjust_elements_size(self):
        """根据窗口大小调整元素大小和字体"""
        scale_factor = self.width() / 1200
        font_size = max(8, int(self.base_font_size * scale_factor))
        
        app_font = QFont("SimHei", font_size)
        self.setFont(app_font)
        
        # 为目标按钮设置更大的字体
        button_font = QFont("SimHei", font_size + 2, QFont.Bold)  # 比普通字体大2号并加粗
        for btn in [self.test_button, self.apply_button, 
                   self.reset_button, self.view_config_button]:
            btn.setFont(button_font)
        
        # 调整其他元素字体
        for label in [self.fastest_label, self.current_source, 
                     self.config_path_label]:
            if label:
                label.setFont(app_font)
        
        group_title_font = QFont("SimHei", font_size, QFont.Bold)
        for group in self.findChildren(QGroupBox):
            group.setFont(group_title_font)
        
        control_font = QFont("SimHei", font_size)
        for radio in self.single_mirror_buttons.values():
            radio[0].setFont(control_font)
        
        for checkbox in self.multi_mirror_checkboxes.values():
            checkbox[0].setFont(control_font)
            
        self.single_radio.setFont(control_font)
        self.multi_radio.setFont(control_font)
        
        self.mirror_table.verticalHeader().setDefaultSectionSize(int(font_size * 2.5))
        
        self.progress_bar.setStyleSheet(f"QProgressBar {{ height: {int(18*scale_factor)}px; }}")

    def on_mode_changed(self):
        """模式切换时的处理"""
        is_single = self.single_radio.isChecked()
        self.single_group.setEnabled(is_single)
        self.multi_group.setEnabled(not is_single)

    def start_test(self):
        """开始测试所有镜像站延迟"""
        self.delays.clear()
        self.mirror_table.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.fastest_label.setText("测试中...")
        self.test_button.setEnabled(False)

        # 创建并启动测试线程
        self.ping_thread = PingThread(self.mirrors)
        self.ping_thread.update_signal.connect(self.update_delay)
        self.ping_thread.finish_signal.connect(self.test_finished)
        self.ping_thread.start()

    def update_delay(self, name, url, delay):
        """更新单个镜像站的延迟信息"""
        self.delays.append((name, url, delay))
        self.delays.sort(key=lambda x: x[2] if x[2] > 0 else float('inf'))
        self.update_table()
        progress = int(len(self.delays) / len(self.mirrors) * 100)
        self.progress_bar.setValue(progress)

    def update_table(self):
        """更新表格内容，保持排序状态"""
        self.mirror_table.setRowCount(0)
        
        for idx, (name, url, delay) in enumerate(self.delays):
            row = self.mirror_table.rowCount()
            self.mirror_table.insertRow(row)

            name_item = QTableWidgetItem(name)
            name_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.mirror_table.setItem(row, 0, name_item)

            url_item = QTableWidgetItem(url)
            url_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.mirror_table.setItem(row, 1, url_item)

            if delay > 0:
                delay_item = QTableWidgetItem(f"{delay:.2f}")
                delay_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                if delay < 100:
                    delay_item.setForeground(QColor(0, 128, 0))
                elif delay < 300:
                    delay_item.setForeground(QColor(255, 165, 0))
                else:
                    delay_item.setForeground(QColor(255, 0, 0))
                self.mirror_table.setItem(row, 2, delay_item)
            else:
                delay_item = QTableWidgetItem("无法连接")
                delay_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                delay_item.setForeground(QColor(128, 128, 128))
                self.mirror_table.setItem(row, 2, delay_item)

    def test_finished(self):
        """测试完成后的处理"""
        self.progress_bar.setVisible(False)
        self.test_button.setEnabled(True)

        fastest = None
        min_delay = float('inf')
        for name, url, delay in self.delays:
            if delay > 0 and delay < min_delay:
                min_delay = delay
                fastest = name

        if fastest:
            self.fastest_label.setText(f"最快的镜像站: {fastest} ({min_delay:.2f} ms)")
            if fastest in self.single_mirror_buttons:
                self.single_mirror_buttons[fastest][0].setChecked(True)

            self.update_single_source_order()
            self.update_multi_source_order()
        else:
            self.fastest_label.setText("无法连接到任何镜像站")

        # 测试完成消息，使用自定义大按钮
        self.show_large_button_message("测试完成", "镜像站延迟测试及排序已完成！", QMessageBox.Information)

    def update_single_source_order(self):
        """按延迟排序更新单源选择框顺序"""
        checked_name = None
        for name, (radio, _) in self.single_mirror_buttons.items():
            if radio.isChecked():
                checked_name = name
                break
                
        single_layout = self.single_group.layout()
        while single_layout.count():
            item = single_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        sorted_mirrors = sorted(self.delays, key=lambda x: x[2] if x[2] > 0 else float('inf'))
        for name, url, delay in sorted_mirrors:
            radio = QRadioButton(f"{name}")
            if delay <= 0:
                radio.setEnabled(False)
                radio.setToolTip("无法连接到该镜像站")
            self.single_mirror_buttons[name] = (radio, url)
            self.single_mirror_group.addButton(radio)
            single_layout.addWidget(radio)
        
        if checked_name and checked_name in self.single_mirror_buttons:
            self.single_mirror_buttons[checked_name][0].setChecked(True)
        elif sorted_mirrors and sorted_mirrors[0][2] > 0:
            self.single_mirror_buttons[sorted_mirrors[0][0]][0].setChecked(True)

    def update_multi_source_order(self):
        """按延迟排序更新多源选择框顺序"""
        checked_names = [name for name, (checkbox, _) in self.multi_mirror_checkboxes.items() 
                         if checkbox.isChecked()]
                
        multi_layout = self.multi_group.layout()
        while multi_layout.count() > 1:
            item = multi_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        sorted_mirrors = sorted(self.delays, key=lambda x: x[2] if x[2] > 0 else float('inf'))
        for name, url, delay in sorted_mirrors:
            checkbox = QCheckBox(f"{name}")
            checkbox.setEnabled(delay > 0)
            if name in checked_names and delay > 0:
                checkbox.setChecked(True)
            if delay > 0:
                if delay < 100:
                    checkbox.setStyleSheet("color: green;")
                elif delay < 300:
                    checkbox.setStyleSheet("color: orange;")
                else:
                    checkbox.setStyleSheet("color: red;")
            else:
                checkbox.setStyleSheet("color: gray;")
            self.multi_mirror_checkboxes[name] = (checkbox, url)
            multi_layout.addWidget(checkbox)

    def detect_current_settings(self):
        """检测当前的pip源设置"""
        try:
            user_home = os.path.expanduser("~")
            self.pip_config_path = os.path.join(user_home, "AppData", "Roaming", "pip", "pip.ini")
            self.config_path_label.setText(self.pip_config_path)

            if os.path.exists(self.pip_config_path):
                config = configparser.ConfigParser()
                config.read(self.pip_config_path, encoding="utf-8")
                settings_text = ""

                if "global" in config:
                    if "index-url" in config["global"]:
                        current_url = config["global"]["index-url"].strip()
                        source_name = "未知源"
                        for name, url in self.mirrors.items():
                            if current_url == url.strip():
                                source_name = name
                                break
                        settings_text += f"主源: {source_name} - {current_url}\n"
                        if source_name in self.single_mirror_buttons:
                            self.single_mirror_buttons[source_name][0].setChecked(True)

                    if "extra-index-url" in config["global"]:
                        extra_urls = config["global"]["extra-index-url"].splitlines()
                        if extra_urls:
                            settings_text += "额外源:\n"
                            for url in extra_urls:
                                url = url.strip()
                                if url:
                                    source_name = "未知源"
                                    for name, u in self.mirrors.items():
                                        if url == u.strip():
                                            source_name = name
                                            break
                                    settings_text += f"- {source_name} - {url}\n"
                            self.multi_radio.setChecked(True)
                            self.on_mode_changed()

                if settings_text:
                    self.current_source.setText(settings_text)
                else:
                    self.current_source.setText("配置文件存在但未设置源信息")
            else:
                self.current_source.setText("未检测到自定义源，使用默认源")

        except Exception as e:
            self.current_source.setText(f"检测设置时出错: {str(e)}")

    def apply_settings(self):
        """应用pip源设置"""
        try:
            if self.single_radio.isChecked():
                selected_name = None
                selected_url = None
                for name, (radio, url) in self.single_mirror_buttons.items():
                    if radio.isChecked():
                        selected_name = name
                        selected_url = url
                        break
                
                if not selected_name:
                    self.show_large_button_message("警告", "请选择一个镜像站", QMessageBox.Warning)
                    return

                self.update_pip_config(selected_url)
                self.show_large_button_message("成功",
                                      f"已将pip源设置为: {selected_name}\n"
                                      f"配置文件路径:\n{self.pip_config_path}",
                                      QMessageBox.Information)
            else:
                selected_mirrors = []
                selected_names = []
                for name, (checkbox, url) in self.multi_mirror_checkboxes.items():
                    if checkbox.isChecked():
                        selected_mirrors.append(url)
                        selected_names.append(name)
                
                if not selected_mirrors:
                    self.show_large_button_message("警告", "请至少选择一个镜像站", QMessageBox.Warning)
                    return

                primary_url = selected_mirrors[0]
                extra_urls = selected_mirrors[1:]
                self.update_pip_config(primary_url, extra_urls)
                self.show_large_button_message("成功",
                                      f"已将pip源设置为多个镜像站(轮询)\n"
                                      f"主源: {selected_names[0]}\n"
                                      f"额外源: {', '.join(selected_names[1:]) if selected_names[1:] else '无'}\n"
                                      f"配置文件路径:\n{self.pip_config_path}",
                                      QMessageBox.Information)

            self.detect_current_settings()

        except Exception as e:
            self.show_large_button_message("错误", f"设置pip源时出错: {str(e)}", QMessageBox.Critical)

    def update_pip_config(self, primary_url, extra_urls=None):
        """更新pip配置文件"""
        pip_dir = os.path.dirname(self.pip_config_path)
        if not os.path.exists(pip_dir):
            os.makedirs(pip_dir)

        config_content = f"[global]\nindex-url = {primary_url}\n"

        if extra_urls and len(extra_urls) > 0:
            config_content += "extra-index-url =\n"
            for url in extra_urls:
                config_content += f"    {url}\n"

        config_content += "\n[install]\ntrusted-host =\n"
        all_urls = [primary_url]
        if extra_urls:
            all_urls.extend(extra_urls)

        hosts = set()
        for url in all_urls:
            if url.startswith("https://"):
                host = url[8:]
            elif url.startswith("http://"):
                host = url[7:]
            else:
                host = url

            if "/" in host:
                host = host[:host.find("/")]
            hosts.add(host)

        for host in hosts:
            config_content += f"    {host}\n"

        with open(self.pip_config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

    def reset_settings(self):
        """恢复默认设置（删除配置文件）"""
        try:
            if os.path.exists(self.pip_config_path):
                os.remove(self.pip_config_path)
                self.show_large_button_message("成功", "已恢复pip默认源设置\n配置文件已删除", QMessageBox.Information)
                self.detect_current_settings()
            else:
                self.show_large_button_message("信息", "当前已是默认源设置，没有配置文件", QMessageBox.Information)

        except Exception as e:
            self.show_large_button_message("错误", f"恢复默认设置时出错: {str(e)}", QMessageBox.Critical)

    def view_config_file(self):
        """查看配置文件内容"""
        try:
            if os.path.exists(self.pip_config_path):
                with open(self.pip_config_path, "r", encoding="utf-8") as f:
                    content = f.read()

                msg = QMessageBox()
                msg.setWindowTitle("pip.ini 配置文件内容")
                msg.setIcon(QMessageBox.Information)
                msg.setText(f"<pre>{content}</pre>")
                msg.setTextFormat(Qt.RichText)
                msg.setMinimumWidth(int(self.width() * 0.6))
                msg.setMinimumHeight(int(self.height() * 0.5))
                
                # 调整OK按钮大小
                for btn in msg.buttons():
                    if msg.buttonRole(btn) == QMessageBox.AcceptRole:
                        btn.setText("确定")
                        btn.setMinimumHeight(40)
                        btn.setMinimumWidth(100)
                        btn.setFont(QFont("SimHei", 12, QFont.Bold))
                
                msg.exec_()
            else:
                self.show_large_button_message("信息", "尚未创建pip配置文件，使用默认源", QMessageBox.Information)

        except Exception as e:
            self.show_large_button_message("错误", f"查看配置文件时出错: {str(e)}", QMessageBox.Critical)

    def show_large_button_message(self, title, message, icon):
        """显示带有大OK按钮的消息框"""
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setIcon(icon)
        msg.setText(message)
        msg.setMinimumWidth(400)
        
        # 放大OK按钮
        for btn in msg.buttons():
            if msg.buttonRole(btn) == QMessageBox.AcceptRole:
                btn.setText("确定")  # 统一按钮文本
                btn.setMinimumHeight(45)  # 增大按钮高度
                btn.setMinimumWidth(120)  # 增大按钮宽度
                btn.setFont(QFont("SimHei", 12, QFont.Bold))  # 增大字体并加粗
        
        msg.exec_()

    def apply_styles(self):
        """应用样式表"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 4px;
                border: none;
                font-family: 'SimHei';
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 8px;
                padding: 8px;
                background-color: #f9f9f9;
                font-family: 'SimHei';
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                gridline-color: #eee;
            }
            QTableWidget::item:alternate {
                background-color: #f0f8ff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
                font-family: 'SimHei';
            }
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
            QRadioButton, QCheckBox {
                padding: 3px;
                margin: 1px;
                font-family: 'SimHei';
            }
            QRadioButton:hover, QCheckBox:hover {
                background-color: #f0f0f0;
                border-radius: 2px;
            }
            QLabel {
                font-family: 'SimHei';
            }
            QScrollArea {
                border: none;
            }
            pre {
                font-family: Consolas, monospace;
                white-space: pre-wrap;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 确保中文显示正常
    font = QFont("SimHei")
    app.setFont(font)
    
    window = PipSourceManager()
    window.show()
    
    sys.exit(app.exec_())
    