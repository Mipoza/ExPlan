import sys
import os
import json
from calendar import monthrange
from functools import partial
from rwdata import *
from PyQt5.QtWidgets import QApplication, QGroupBox, QCheckBox, QAbstractItemView, QListView, QComboBox, QAction, QLineEdit, QMenu, QMainWindow, QListWidgetItem, QVBoxLayout, QPushButton, QWidget, QListWidget, QHBoxLayout, QLabel, QFileDialog, QCalendarWidget, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIntValidator, QStandardItemModel, QStandardItem, QColor, QPixmap

from datetime import datetime, timedelta

def get_week_range(date): #monthrange(date.year, date.month)[1] pour choper dernier jours du mois !!
    start_of_week = date - timedelta(days=date.weekday())

    end_of_week = start_of_week + timedelta(days=6)

    start_date_str = start_of_week.strftime("%d")
    end_date_str = end_of_week.strftime("%d") + " " + start_of_week.strftime("%B")
    
    month = end_date_str.split(" ")[1]
    if month in month_fr:
        end_date_str = end_date_str.replace(month, month_fr[month])
    
    phrase = f"Semaine du {start_date_str} au {end_date_str}"
    
    return phrase

class CustomListWidgetItem(QListWidgetItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unavailability = [False] * 14

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other

class AvDialog(QDialog):
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.setWindowTitle("Indisponibilités")

        main_layout = QVBoxLayout()

        # Création de la première QCheckBox pour cocher/décocher les autres
        select_all_checkbox = QCheckBox("Tout sélectionner")
        select_all_checkbox.setChecked(False)
        select_all_checkbox.stateChanged.connect(self.toggle_checkboxes)


        # Création du groupe pour les 14 QCheckBox
        group_box = QGroupBox("Demi-journées d'indisponibilité")
        group_layout = QVBoxLayout()

        group_layout.addWidget(select_all_checkbox) 
        # Création des 14 autres QCheckBox pour les demi-journées
        demi_journees = [
            "Lundi matin",
            "Lundi après-midi",
            "Mardi matin",
            "Mardi après-midi",
            "Mercredi matin",
            "Mercredi après-midi",
            "Jeudi matin",
            "Jeudi après-midi",
            "Vendredi matin",
            "Vendredi après-midi",
            "Samedi matin",
            "Samedi après-midi",
            "Dimanche matin",
            "Dimanche après-midi"
        ]

        self.checkbox_list = []

        for demi_journee in demi_journees:
            checkbox = QCheckBox(demi_journee)
            checkbox.setChecked(item.unavailability[demi_journees.index(demi_journee)])
            group_layout.addWidget(checkbox)
            self.checkbox_list.append(checkbox)

        group_box.setLayout(group_layout)
        main_layout.addWidget(group_box)

        ok_button = QPushButton("Ok")
        ok_button.clicked.connect(self.accept)
        main_layout.addWidget(ok_button)

        self.setLayout(main_layout)

    def toggle_checkboxes(self, state):
        for checkbox in self.checkbox_list:
            checkbox.setChecked(state == 2)

    def change_unav(self):
        self.item.unavailability = [checkbox.isChecked() for checkbox in self.checkbox_list]

class CustomListWidget(QListWidget):
    def __init__(self):
        self.dict = {}
        super().__init__()
        self.setStyleSheet("QListWidget::item:disabled { color: gray; }")

    def changeState(self, checked, pos):
        item = self.itemAt(pos)
        dialog = AvDialog(item)
        if dialog.exec_() == QDialog.Accepted:
            dialog.change_unav()
            

    def delete(self, checked, pos):
        item = self.itemAt(pos)
        self.dict.pop(item)
        self.takeItem(self.row(item))

    def add(self, checked):
        pass

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        context_menu = QMenu(self)

        if item is not None:
            unable_action = QAction("Indisponibilités", self)
            unable_action.triggered.connect(partial(self.changeState, pos=event.pos()))
            context_menu.addAction(unable_action)

            delete_action = QAction("Supprimer", self)
            delete_action.triggered.connect(partial(self.delete, pos=event.pos()))
            context_menu.addAction(delete_action)
        else:
            add_action = QAction("Ajouter", self)
            add_action.triggered.connect(self.add)
            context_menu.addAction(add_action)

        context_menu.exec_(self.mapToGlobal(event.pos()))


class BusListWidget(CustomListWidget):
    def __init__(self):
        super().__init__()

    def addClose(self, dialog, name, size, constraint, b_license):
        item = CustomListWidgetItem()
        item.setText(name() + " " + size())


        l = "B" if b_license().lower() == "permis classique" else "E"

        if l == "E":
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        c = []

        if constraint().strip() != "":
            c = constraint().strip().split(",")

        self.dict[item] = Bus(name(), int(size()), l, c)

        self.addItem(item)

        dialog.close()

    def add(self, checked):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajout de bus")

        Mlayout = QHBoxLayout()
        
        label_name = QLabel("Nom :")
        Mlayout.addWidget(label_name)

        line_name = QLineEdit(self)
        Mlayout.addWidget(line_name)

        label_size = QLabel("Taille :")
        Mlayout.addWidget(label_size)
        
        line_size= QLineEdit(self)
        validator = QIntValidator(1, 999)
        line_size.setValidator(validator)
        Mlayout.addWidget(line_size)
        
        label_constraint = QLabel("Contraintes :")
        Mlayout.addWidget(label_constraint)

        line_constraint = QLineEdit(self)
        line_constraint.setPlaceholderText("spe, via, esc")
        Mlayout.addWidget(line_constraint)

        license_box = QComboBox(self)
        license_box.addItem("Permis classique")
        license_box.addItem("Permis spécial")
        Mlayout.addWidget(license_box)

        button = QPushButton("Ajouter")
        button.setEnabled(False)
        button.clicked.connect(partial(self.addClose, dialog, line_name.text, line_size.text, line_constraint.text, license_box.currentText))
        Mlayout.addWidget(button)

        line_name.textChanged.connect(lambda text: button.setEnabled(text != "" and line_size.text() != ""))
        line_size.textChanged.connect(lambda text: button.setEnabled(text != "" and line_name.text() != ""))

        dialog.setLayout(Mlayout)
        dialog.exec_()

class DriverListWidget(CustomListWidget):
    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def addClose(self, dialog, name):
        item = CustomListWidgetItem()
        item.setText(name())

        self.dict[item] = name()
        self.addItem(item)


        dialog.close()

    def add(self, checked):
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajout de chauffeur")

        Mlayout = QHBoxLayout()
        
        label_name = QLabel("Nom :")
        Mlayout.addWidget(label_name)

        line_name = QLineEdit(self)
        Mlayout.addWidget(line_name)

        button = QPushButton("Ajouter")
        button.setEnabled(False)
        button.clicked.connect(partial(self.addClose, dialog, line_name.text))
        Mlayout.addWidget(button)

        line_name.textChanged.connect(lambda text: button.setEnabled(text != ""))
        dialog.setLayout(Mlayout)
        dialog.exec_()

class DateSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Date Selection")
        layout = QVBoxLayout()

        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setGridVisible(True)
        layout.addWidget(self.calendar_widget)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def selected_date(self):
        return self.calendar_widget.selectedDate()
    


class ExWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.time = datetime.now()
        self.plan_path = ""
        self.initUI()
        self.open()
    
    def generateRot(self):
        dir_path = os.path.dirname(self.plan_path)
        bs_list = [[self.list_widget1.dict[item], item.unavailability] for item in [self.list_widget1.item(index) for index in range(self.list_widget1.count())]] 
        d_list = [[self.list_widget2.dict[item], item.unavailability] for item in [self.list_widget2.item(index) for index in range(self.list_widget2.count())]]
        write_planning(get_planning(self.plan_path, self.time, bs_list, d_list), dir_path)
        print(self.time)

    def closeEvent(self, event):
        self.save()
        event.accept()  

    def save(self):
        path = self.plan_path
        drivers = [self.list_widget2.item(index).text() for index in range(self.list_widget2.count())]
        b_list = [self.list_widget1.dict[item] for item in [self.list_widget1.item(index) for index in range(self.list_widget1.count())]]
        data = {"plan_path" : path, "drivers" : drivers, "bus" : []}
        for b in b_list:
            data["bus"].append({"name" : b.name, "size" : str(b.size), "license" : b.license, "constraints" : b.constraints})
        
        try: 
            with open(os.path.join(os.path.dirname(path),"save.json"), "w") as save_file:
                json.dump(data, save_file)
        except Exception as e:
            print(e)

    def open(self):
        file_flag = True
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"save.json"), "r") as current_file:
                data = json.load(current_file)
        except Exception as e:
            file_flag = False

        if file_flag == False or data["plan_path"] == "":
            self.open_file()
        else:
            self.plan_path = data["plan_path"]
            
            drivers = data["drivers"]

            for d in drivers:
                item = CustomListWidgetItem()
                item.setText(d)
                self.list_widget2.dict[item] = d
                self.list_widget2.addItem(item)

            bus_list = data["bus"]

            for b in bus_list:
                bus = Bus(b["name"],int(b["size"]),b["license"],b["constraints"])
                item = CustomListWidgetItem()
                font = item.font()
                item.setText(bus.name + " " + str(bus.size))
                if bus.license == "E":
                    font.setBold(True)
                item.setFont(font)
                self.list_widget1.dict[item] = bus
                self.list_widget1.addItem(item)

    def initUI(self):
        self.setWindowTitle('ExPlan')
        self.resize(600, 525)

        menubar = self.menuBar()

        plan_menu = menubar.addMenu('Planning')

        open_action = QAction("Chemin planning", self)
        open_action.triggered.connect(self.open_file)
        plan_menu.addAction(open_action)

        date_action = QAction("Date planification", self)
        date_action.triggered.connect(self.select_date)
        plan_menu.addAction(date_action)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        Mlayout = QVBoxLayout(central_widget)
        Hlayout = QHBoxLayout()

        label_img = QLabel()
        pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)),"explo.png")) 
        
        label_img.setPixmap(pixmap)
        label_img.setAlignment(Qt.AlignCenter)

        Mlayout.addWidget(label_img)


        self.label_week = QLabel(get_week_range(self.time))
        font = self.label_week.font()
        font.setPointSize(12)  
        font.setBold(True)
        font.setUnderline(True)
        self.label_week.setFont(font)
        self.label_week.setAlignment(Qt.AlignCenter)

        Mlayout.addWidget(self.label_week)

        font.setPointSize(10) 
        font.setBold(False)
        font.setUnderline(False)

        self.list_widget1 = BusListWidget()
        

        label_l1 = QLabel("Bus :")
        label_l1.setFont(font)
        V1Layout = QVBoxLayout()
        V1Layout.addWidget(label_l1)
        V1Layout.addWidget(self.list_widget1)
        Hlayout.addLayout(V1Layout)

        self.list_widget2 = DriverListWidget()
        label_l2 = QLabel("Chauffeurs :")
        label_l2.setFont(font)

        V2Layout = QVBoxLayout()
        V2Layout.addWidget(label_l2)
        V2Layout.addWidget(self.list_widget2)
        Hlayout.addLayout(V2Layout)


        Blayout = QVBoxLayout()
        button = QPushButton('Générer Rotation', central_widget)
        button.setMinimumSize(self.width(), 30)
        font = button.font()
        font.setPointSize(10)  # Set the desired font size
        button.setFont(font)
        button.clicked.connect(self.generateRot)

        Blayout.addWidget(button)
        Blayout.setAlignment(button, Qt.AlignCenter | Qt.AlignBottom)

        Mlayout.addLayout(Hlayout)
        Mlayout.addLayout(Blayout)

    def open_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Excel Files (*.xlsx)")

        if file_dialog.exec_():
            file_names = file_dialog.selectedFiles()
            for file_name in file_names:
                self.plan_path = file_name
                print("Selected file:", self.plan_path)

    def select_date(self):
        dialog = DateSelectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_date = dialog.selected_date()
            old_time = self.time
            self.time = datetime.strptime(selected_date.toString("dd/MM/yyyy"), "%d/%m/%Y")
            self.label_week.setText(get_week_range(self.time))
            if old_time != self.time:
                for i in range(self.list_widget1.count()):
                    self.list_widget1.item(i).unavailability = [False] * 14
                for i in range(self.list_widget2.count()):
                    self.list_widget2.item(i).unavailability = [False] * 14
            
    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ExWindow()
    window.show()
    sys.exit(app.exec_())