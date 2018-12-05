from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QGroupBox, QLabel
from PyQt5.QtChart import QLineSeries, QValueAxis, QChart
from PyQt5.QtCore import Qt

from modules.ChartView import ChartView
from modules.DataAnalyzer import DataAnalyzer


class FftDialog(QDialog):

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Преобразование фурье')
        self.setMinimumSize(1200, 800)

        #Виджет с графиком
        chart_view = ChartView()
        chart_view.setMinimumSize(1000, 800)
        chart_view.build_plot(data, "Частотно-временой анализ", "Амплитуда", "Частота, Гц")

        #Виджет для коэффициентов
        fft_coef_list = QListWidget()
        fft_coef_label = QLabel('Коэффициенты фурье:')
        for elem in data[2]:
            fft_coef_list.addItem(str(elem))

        #layout - groupBox for fft info
        group_box_layout = QVBoxLayout()
        group_box_layout.addWidget(fft_coef_label)
        group_box_layout.addWidget(fft_coef_list)

        params_group_box = QGroupBox()
        params_group_box.setLayout(group_box_layout)

        layout = QVBoxLayout()
        child_layout = QHBoxLayout()

        layout.addLayout(child_layout)

        child_layout.addWidget(chart_view)
        child_layout.addWidget(params_group_box)

        self.setLayout(layout)



