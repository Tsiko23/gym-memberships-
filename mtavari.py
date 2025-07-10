import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QDateEdit, QFileDialog, QInputDialog
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap
from db import (
    create_table, add_member, get_all_members,
    update_days_left, delete_member
)
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


class GymApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gym Membership Management")
        self.setGeometry(300, 100, 1000, 650)

        self.subscriptions = {
            "Silver": (80, 12),
            "Gold": (100, 18),
            "Platinum": (150, 30)
        }

        self.init_ui()
        create_table()
        self.load_members()
        self.update_revenue_label()

    def init_ui(self):
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("სახელი და გვარი")

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID ნომერი")

        self.subscription_combo = QComboBox()
        self.subscription_combo.addItems(self.subscriptions.keys())

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.dateChanged.connect(self.update_end_date)

        self.end_label = QLabel("აბონემენტის დასრულება: -")

        self.add_button = QPushButton("➕ დამატება")
        self.add_button.clicked.connect(self.add_member)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 მოძებნე სახელი ან ID")
        self.search_input.textChanged.connect(self.search_member)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "სახელი", "ID ნომერი", "აბონემენტი",
            "ფასი", "თარიღი", "დარჩენილი დღე"
        ])
        self.table.setSelectionBehavior(self.table.SelectRows)

        self.checkin_button = QPushButton("Check-in (დროზე დათვლა)")
        self.checkin_button.clicked.connect(self.check_in)

        self.delete_button = QPushButton("წაშლა")
        self.delete_button.clicked.connect(self.delete_member)

        self.refresh_button = QPushButton("განახლება")
        self.refresh_button.clicked.connect(self.load_members)

        self.extend_button = QPushButton("გახანგრძლივება (აირჩიე დღეები)")
        self.extend_button.clicked.connect(self.extend_membership_custom)

        self.export_button = QPushButton("CSV ექსპორტი")
        self.export_button.clicked.connect(self.export_to_csv)

        self.stats_button = QPushButton("სტატისტიკა")
        self.stats_button.clicked.connect(self.show_stats)

        self.revenue_label = QLabel("მთლიანი შემოსავალი: 0 ლარი")
        self.member_count_label = QLabel("წევრების რაოდენობა: 0")

        # Layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.id_input)
        input_layout.addWidget(self.subscription_combo)
        input_layout.addWidget(self.date_input)
        input_layout.addWidget(self.add_button)

        options_layout = QHBoxLayout()
        options_layout.addWidget(self.end_label)
        options_layout.addWidget(self.search_input)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.checkin_button)
        buttons_layout.addWidget(self.extend_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.export_button)
        buttons_layout.addWidget(self.stats_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addLayout(options_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self.table)
        main_layout.addWidget(self.revenue_label)
        main_layout.addWidget(self.member_count_label)

        self.setLayout(main_layout)

    def update_end_date(self):
        sub_type = self.subscription_combo.currentText()
        days = self.subscriptions[sub_type][1]
        start = self.date_input.date()
        end = start.addDays(days)
        self.end_label.setText(f"აბონემენტის დასრულება: {end.toString('yyyy-MM-dd')}")

    def add_member(self):
        name = self.name_input.text().strip()
        id_number = self.id_input.text().strip()
        subscription = self.subscription_combo.currentText()
        price, days = self.subscriptions[subscription]
        start_date = self.date_input.date().toString("yyyy-MM-dd")

        if not name or not id_number:
            QMessageBox.warning(self, "გაფრთხილება", "გთხოვთ შეავსოთ ყველა ველი!")
            return

        if any(m[2] == id_number for m in get_all_members()):
            QMessageBox.warning(self, "დუბლიკატი", "ასეთი ID უკვე არსებობს!")
            return

        try:
            add_member(name, id_number, subscription, price, start_date, days)
            QMessageBox.information(self, "წარმატება", f"{name} დაემატა ბაზაში.")
            self.name_input.clear()
            self.id_input.clear()
            self.load_members()
            self.update_revenue_label()
        except Exception as e:
            QMessageBox.critical(self, "შეცდომა", str(e))

    def load_members(self):
        self.table.setRowCount(0)
        members = get_all_members()

        for m in members:
            if m[6] <= 0:
                delete_member(m[0])

        members = get_all_members()
        for row, m in enumerate(members):
            self.table.insertRow(row)
            for col, val in enumerate(m):
                item = QTableWidgetItem(str(val))
                if m[6] <= 0:
                    item.setBackground(Qt.red)
                self.table.setItem(row, col, item)

        self.member_count_label.setText(f"წევრების რაოდენობა: {len(members)}")

    def search_member(self):
        text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().lower()
            id_number = self.table.item(row, 2).text().lower()
            visible = text in name or text in id_number
            self.table.setRowHidden(row, not visible)

    def update_revenue_label(self):
        members = get_all_members()
        total = sum(m[4] for m in members)
        self.revenue_label.setText(f"მთლიანი შემოსავალი: {total:.2f} ლარი")

    def check_in(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "გაფრთხილება", "აირჩიეთ წევრი!")
            return
        row = selected[0].row()
        member_id = int(self.table.item(row, 0).text())
        days_left = int(self.table.item(row, 6).text())

        if days_left <= 0:
            QMessageBox.information(self, "შეწყდა", "ვადა ამოწურულია.")
            return

        update_days_left(member_id, days_left - 1)
        self.load_members()

    def extend_membership_custom(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "გაფრთხილება", "აირჩიეთ წევრი!")
            return

        options = {
            "Silver (12 დღე)": 12,
            "Gold (18 დღე)": 18,
            "Platinum (30 დღე)": 30
        }

        items = list(options.keys())
        item, ok = QInputDialog.getItem(self, "აირჩიე დამატება", "რომელი პაკეტის დამატება გსურს?", items, 0, False)

        if ok and item:
            days_to_add = options[item]
            row = selected[0].row()
            member_id = int(self.table.item(row, 0).text())
            current_days = int(self.table.item(row, 6).text())
            update_days_left(member_id, current_days + days_to_add)
            QMessageBox.information(self, "წარმატება", f"დაემატა {days_to_add} დღე.")
            self.load_members()

    def delete_member(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "გაფრთხილება", "აირჩიეთ წევრი წასაშლელად!")
            return
        row = selected[0].row()
        member_id = int(self.table.item(row, 0).text())
        reply = QMessageBox.question(self, "დადასტურება", "წავშალოთ?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            delete_member(member_id)
            self.load_members()
            self.update_revenue_label()

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(self, "ექსპორტი", "ფაილი შენახულია!")

    def show_stats(self):
        members = get_all_members()
        data = {"Silver": 0, "Gold": 0, "Platinum": 0}
        for m in members:
            data[m[3]] += 1

        labels = list(data.keys())
        sizes = list(data.values())
        colors = ['#c0c0c0', '#ffd700', '#e5e4e2']

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.axis('equal')
        plt.title("აბონემენტების ტიპები")
        plt.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GymApp()
    window.show()
    sys.exit(app.exec_())
