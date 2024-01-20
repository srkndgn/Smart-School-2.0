from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QListWidgetItem, QComboBox, QListWidget, QHeaderView, QMessageBox, QWidget, QCalendarWidget, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtGui
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor
import psycopg2
import re
import datetime
from message import BorderDelegate


class TeacherApp(QMainWindow):
    login = pyqtSignal(bool)

    def __init__(self, conn, cur, database, user):
        super(TeacherApp, self).__init__()
        self.setupUi()
        self.connectDatabase(conn, cur, database)
        self.user = user
        self.initializeUi()

    def setupUi(self):
        try:
            loadUi('teacher.ui', self)
            self.selected_lesson_index = None
            self.selected_meeting_index = None
            self.comboBox_instructor.currentIndexChanged.connect(self.onInstructorChanged)
        except Exception as e:
            self.showErrorMessage("Initialization Error", f"Error during TeacherApp initialization: {e}")

    def connectDatabase(self, conn, cur, database):
        self.conn = conn
        self.cur = cur
        self.database = database
        self.populate_instructors()

    def initializeUi(self):
        self.setupTabs()
        self.setupMenuActions()
        self.setupButtonActions()
        self.setupCalendar()
        self.setupMeetingCalendar()

    def setupTabs(self):
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.tabBar().setVisible(False)

    def setupMenuActions(self):
        self.menu11_t.triggered.connect(self.showEditProfileTab)
        self.menu21_t.triggered.connect(self.showLessonScheduleTab)
        self.menu22_t.triggered.connect(self.showLessonAttendanceTab)
        self.menu31_t.triggered.connect(self.showMeetingScheduleTab)
        self.menu32_t_2.triggered.connect(self.showMeetingAttendanceTab)
        self.menu41_t.triggered.connect(self.add_todolist_tab)
        self.menu51_t.triggered.connect(self.add_message_tab)
        self.announcementMenu.triggered.connect(self.add_announce_tab)
        self.menu71_t.triggered.connect(self.logout)

    def setupButtonActions(self):
        self.b6.clicked.connect(self.updateTeacherDetails)
        self.sendButton3_t.clicked.connect(self.send_message)

    def setupCalendar(self):
        self.calendar = QCalendarWidget(self)
        self.calendar.setWindowFlags(Qt.Popup)
        self.calendar.setGridVisible(True)
        self.calendar.hide()
        self.calendar.clicked.connect(self.updateDateInput)

    def onInstructorChanged(self, index):
        if index == 0:
            pass  # Placeholder is selected, handle this case separately if needed
        else:
            selected_instructor = self.comboBox_instructor.currentText()

    def getInstructorId(self, instructor_name):
        try:
            query = "SELECT user_id FROM users WHERE CONCAT(name, ' ', surname) = %s"
            self.cur.execute(query, (instructor_name,))
            result = self.cur.fetchone()
            return result[0] if result else None
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
            return None

    def showEditProfileTab(self):
        self.tabWidget.setCurrentIndex(1)
        self.tb22.setText(self.user.email)
        self.tb23.setText(self.user.name)
        self.tb24.setText(self.user.surname)
        self.tb26.setText(self.user.phone)

    def updateDateInput(self, date):
        formatted_date = date.toString("yyyy-MM-dd")
        self.date_input.setText(formatted_date)
        self.calendar.hide()
###################################################################################
    def showLessonScheduleTab(self):
        self.tabWidget.setCurrentIndex(2)
        # Initialize UI elements for lesson schedule management
        self.date_input = self.findChild(QLineEdit, 'dateInput')
        self.lesson_name = self.findChild(QLineEdit, 'lessonName')
        self.time_slot = self.findChild(QLineEdit, 'timeSlot')
        self.add_lesson_btn = self.findChild(QPushButton, 'addLessonBtn')
        self.edit_lesson_btn = self.findChild(QPushButton, 'editLessonBtn')
        self.reset_lesson_btn = self.findChild(QPushButton, 'resetLessonBtn')
        self.delete_lesson_btn = self.findChild(QPushButton, 'deleteLessonBtn')
        self.delete_all_lessons_btn = self.findChild(QPushButton, 'deleteAllLessonsBtn')
        self.comboBox_instructor = self.findChild(QComboBox, 'comboBox_instructor')
        self.lesson_table = self.findChild(QTableWidget, 'lessonTable')
        self.populate_instructors()

        self.lesson_table.setColumnCount(5)
        self.lesson_table.setHorizontalHeaderLabels(["Lesson ID","Lesson Name", "Date", "Time Slot", "Instructor"])
        header = self.lesson_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        self.add_lesson_btn.clicked.connect(self.addLesson)
        self.edit_lesson_btn.clicked.connect(self.editLesson)
        self.reset_lesson_btn.clicked.connect(self.resetButton)
        self.date_input.mousePressEvent = self.showCalendar
        self.delete_lesson_btn.clicked.connect(self.deleteLesson)
        self.delete_all_lessons_btn.clicked.connect(self.deleteAllLessons)
        self.lesson_table.itemClicked.connect(self.selectLesson)

        # Set column widths
        character_width = 12
        self.lesson_table.setColumnWidth(0, 10 * character_width)
        self.lesson_table.setColumnWidth(1, 50 * character_width)
        self.lesson_table.setColumnWidth(2, 12 * character_width)
        self.lesson_table.setColumnWidth(3, 12 * character_width)
        self.lesson_table.setColumnWidth(4, 17 * character_width)
        
        # Fetch and display lessons from the database
        self.loadLessons()
    
    def setupLessonTable(self):
        self.lesson_table.setHorizontalHeaderLabels(["Lesson ID", "Lesson Name", "Date", "Time Slot", "Instructor"])
        header = self.lesson_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
       
    def loadLessons(self):
        try:
            self.lesson_table.setRowCount(0)  # Clear the table before repopulating
            query = "SELECT lesson_id, lesson_name, lesson_date, lesson_time_slot, lesson_instructor FROM lesson ORDER BY lesson_date ASC"
            self.cur.execute(query)
            lessons = self.cur.fetchall()
            for lesson in lessons:
                rowPosition = self.lesson_table.rowCount()
                self.lesson_table.insertRow(rowPosition)
                # Inserting items into the table in the correct column order
                self.lesson_table.setItem(rowPosition, 0, QTableWidgetItem(str(lesson[0])))  # Lesson ID
                self.lesson_table.setItem(rowPosition, 1, QTableWidgetItem(str(lesson[1])))  # Lesson Name
                self.lesson_table.setItem(rowPosition, 2, QTableWidgetItem(str(lesson[2])))  # Date
                self.lesson_table.setItem(rowPosition, 3, QTableWidgetItem(str(lesson[3])))  # Time Slot
                self.lesson_table.setItem(rowPosition, 4, QTableWidgetItem(str(lesson[4])))  # Instructor
            
            # Hide the lesson_id column after populating the table
            self.lesson_table.setColumnHidden(0, True)  # Hides the first column (Lesson ID)
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Error', f'An error occurred while loading lessons: {e}')

    def addLesson(self):
        lesson_name = self.lesson_name.text().strip()
        date = self.date_input.text().strip()
        time_slot = self.time_slot.text().strip()
        instructor_name = self.comboBox_instructor.currentText()
        instructor_id = self.getInstructorId(instructor_name)
        created_by = self.user.id  # Assuming self.user.id holds the ID of the current user

        if not lesson_name or not date or not time_slot or not instructor_name :
            QMessageBox.warning(self, "Input Error", "All fields must be filled out and a valid instructor must be selected.")
            return

        if not self.isValidTimeSlot(time_slot):
            QMessageBox.warning(self, "Input Error", "Time slot must be in the format xx:xx-xx:xx.")
            return

        try:
            query = """
            INSERT INTO lesson (lesson_name, lesson_date, lesson_time_slot, lesson_instructor, created_by)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cur.execute(query, (lesson_name, date, time_slot, instructor_name, created_by))
            self.conn.commit()
            QMessageBox.information(self, 'Success', 'Lesson added successfully')
            

            self.loadLessons()  # Reload the lessons to reflect changes
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

        self.resetForm()
        self.selected_lesson_index = None  # Reset the selected index

    def editLesson(self):
        lesson_name = self.lesson_name.text().strip()
        date = self.date_input.text().strip()
        time_slot = self.time_slot.text().strip()
        instructor_name = self.comboBox_instructor.currentText()
        instructor_id = self.getInstructorId(instructor_name)
        created_by = self.user.id  # Assuming self.user.id holds the ID of the current user

        if not lesson_name or not date or not time_slot or not instructor_name :
            QMessageBox.warning(self, "Input Error", "All fields must be filled out and a valid instructor must be selected.")
            return

        if not self.isValidTimeSlot(time_slot):
            QMessageBox.warning(self, "Input Error", "Time slot must be in the format xx:xx-xx:xx.")
            return

        try:
            # Update existing lesson
            lesson_id = self.getLessonIdFromTable(self.selected_lesson_index)
            query = """
            UPDATE lesson
            SET lesson_name = %s, lesson_date = %s, lesson_time_slot = %s, lesson_instructor = %s, created_by = %s
            WHERE lesson_id = %s
            """
            self.cur.execute(query, (lesson_name, date, time_slot, instructor_name, created_by, lesson_id))
            self.conn.commit()
            QMessageBox.information(self, 'Success', 'Lesson updated successfully')

            self.loadLessons()  # Reload the lessons to reflect changes
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

        self.resetForm()
        self.selected_lesson_index = None  # Reset the selected index

    def resetButton(self):
        self.resetForm()
        self.selected_lesson_index = None
    
    def selectLesson(self, item):
        current_row = self.lesson_table.row(item)
        if current_row >= 0:
            lesson_name_item = self.lesson_table.item(current_row, 1)  # lesson_name
            date_item = self.lesson_table.item(current_row, 2)  # lesson_date
            time_item = self.lesson_table.item(current_row, 3)  # lesson_time_slot
            instructor_item = self.lesson_table.item(current_row, 4)  # lesson_instructor
            
            if lesson_name_item and date_item and time_item and instructor_item:
                self.lesson_name.setText(lesson_name_item.text())
                self.date_input.setText(date_item.text())
                self.time_slot.setText(time_item.text())
                instructor_index = self.comboBox_instructor.findText(instructor_item.text(), Qt.MatchFixedString)
                if instructor_index >= 0:
                    self.comboBox_instructor.setCurrentIndex(instructor_index)
                self.selected_lesson_index = current_row
            else:
                QMessageBox.warning(self, 'Selection Error', 'Failed to retrieve lesson details.')

    def deleteLesson(self):
        selected_rows = set()
        for item in self.lesson_table.selectedItems():
            selected_rows.add(item.row())
        for row in sorted(selected_rows, reverse=True):
            lesson_id = self.getLessonIdFromTable(row)
            if lesson_id:
                try:
                    query = "DELETE FROM lesson WHERE lesson_id = %s"
                    self.cur.execute(query, (lesson_id,))
                    self.conn.commit()
                    self.lesson_table.removeRow(row)
                except psycopg2.Error as e:
                    self.conn.rollback()
                    QMessageBox.critical(self, 'Error', f'An error occurred while deleting the lesson: {e}')
            else:
                QMessageBox.warning(self, 'Selection Error', 'Could not find the lesson ID.')

        self.resetForm()
        self.selected_lesson_index = None

    def deleteAllLessons(self):
        try:
            query = "DELETE FROM lesson"
            self.cur.execute(query)
            self.conn.commit()
            self.lesson_table.setRowCount(0)
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Error', f'An error occurred while deleting all lessons: {e}')

        self.resetForm()

    def resetForm(self):
        self.lesson_name.clear()
        self.date_input.clear()
        self.time_slot.clear()
        self.comboBox_instructor.setCurrentIndex(0)

    def getLessonIdFromTable(self, row_index):
        lesson_id_item = self.lesson_table.item(row_index, 0)  # Assuming lesson_id is in the first column
        return int(lesson_id_item.text()) if lesson_id_item else None

    def showCalendar(self, event):
        calendar_pos = self.date_input.mapToGlobal(self.date_input.rect().bottomLeft())
        self.calendar.move(calendar_pos)
        self.calendar.show()

    def populate_instructors(self):
        try:
            self.comboBox_instructor.clear()
            self.comboBox_instructor.addItem("Select an instructor")
            teachers = self.database.get_teachers(self.cur)
            for name, surname in teachers:
                self.comboBox_instructor.addItem(f"{name} {surname}")
        except Exception as e:
            self.showErrorMessage("Database Error", f"Error populating instructors: {e}")

    def showErrorMessage(self, title, message):
        QMessageBox.critical(self, title, message)

        
###########################################################################################################
    def showLessonAttendanceTab(self):
        self.tabWidget.setCurrentIndex(3)
        
        # Initialize UI elements for lesson attendance management
        self.lessonComboBox = self.findChild(QComboBox, 'lessonComboBox')
        self.studentComboBox = self.findChild(QComboBox, 'studentComboBox')
        self.statusComboBox = self.findChild(QComboBox, 'statusComboBox')
        self.markAttendanceBtn = self.findChild(QPushButton, 'markAttendanceBtn')
        self.recordsList = self.findChild(QListWidget, 'recordsList')
        
        # Initialize delete buttons
        self.deleteAttendanceBtn = self.findChild(QPushButton, 'deleteAttendanceBtn')
        self.deleteAllAttendanceBtn = self.findChild(QPushButton, 'deleteAllAttendanceBtn')
        self.deleteSelectedStudentAttendanceBtn = self.findChild(QPushButton, 'deleteSelectedStudentAttendanceBtn')


        # Connect buttons to their respective methods
        self.deleteAttendanceBtn.clicked.connect(self.deleteSelectedAttendance)
        self.deleteAllAttendanceBtn.clicked.connect(self.deleteAllAttendance)
        self.deleteSelectedStudentAttendanceBtn.clicked.connect(self.deleteSelectedStudentAttendance)

        
         # Connect the studentComboBox's signal to the loadAttendanceRecords method
        self.studentComboBox.currentIndexChanged.connect(self.loadAttendanceRecords)

        # Populate combo boxes
        self.populateLessonComboBox()
        self.populateStudentComboBox()

        # Connect the 'Mark Attendance' button click to the method
        self.markAttendanceBtn.clicked.connect(self.markAttendance)
        
        # Connect the itemClicked signal to the populateFields method
        self.recordsList.itemClicked.connect(self.populateFields)
        
        # Clear existing items in recordsList and reset combo boxes
        self.recordsList.clear()
        self.lessonComboBox.setCurrentIndex(0)
        self.studentComboBox.setCurrentIndex(0)
        self.statusComboBox.setCurrentIndex(0)
        
        # Initialize statusComboBox with placeholder and options
        self.statusComboBox.clear()  # Clear existing items
        self.statusComboBox.addItem("Please select a status...")  # Add placeholder text
        for status in ['Present', 'Absent', 'Late', 'Excused']:
            self.statusComboBox.addItem(status)

    def populateLessonComboBox(self):
        self.lessonComboBox.clear()  # Clear existing items
        font = self.lessonComboBox.font()  # Get the current font
        font.setPointSize(12)  # Set the font size
        self.lessonComboBox.setFont(font)  # Apply the font
        
        self.lessonComboBox.addItem("Please select a lesson...")  # Add placeholder text
        self.cur.execute("SELECT lesson_id, lesson_name, lesson_date, lesson_time_slot FROM lesson")
        lessons = self.cur.fetchall()
        for lesson_id, lesson_name, lesson_date, lesson_time_slot in lessons:
            display_text = f"{lesson_name} - {lesson_date} - {lesson_time_slot}"
            self.lessonComboBox.addItem(display_text, lesson_id)

    def populateStudentComboBox(self):
        self.studentComboBox.clear()  # Clear existing items
        font = self.studentComboBox.font()  # Get the current font
        font.setPointSize(12)  # Set the font size
        self.studentComboBox.setFont(font)  # Apply the font
        
        self.studentComboBox.addItem("Please select a student...")  # Add placeholder text
        self.cur.execute("SELECT user_id, name, surname, email FROM users WHERE user_type = 'student'")
        students = self.cur.fetchall()
        for user_id, name, surname, email in students:
            display_text = f"{name} {surname} - {email}"
            self.studentComboBox.addItem(display_text, user_id)


    def loadAttendanceRecords(self):
        self.recordsList.clear()  # Clear existing items
        self.recordsList.setFont(QtGui.QFont("Courier New", 12))  # Set monospaced font
        
        user_id = self.studentComboBox.currentData()
        if user_id:
            try:
                query = """
                SELECT la.attendance_id, l.lesson_name, l.lesson_date, l.lesson_time_slot, la.status
                FROM lessonattendance la
                JOIN lesson l ON la.lesson_id = l.lesson_id
                WHERE la.user_id = %s
                """
                self.cur.execute(query, (user_id,))
                records = self.cur.fetchall()
                for attendance_id, lesson_name, lesson_date, lesson_time_slot, status in records:
                    # Convert lesson_date to string if it's a date object (adjust format as needed)
                    lesson_date_str = lesson_date.strftime("%Y-%m-%d") if isinstance(lesson_date, datetime.date) else lesson_date
                    record_text = f"Lesson: {lesson_name:40s} Date: {lesson_date_str:10s}  Time: {lesson_time_slot:13s}  Status: {status.capitalize():10s}"
                    listItem = QListWidgetItem(record_text)
                    listItem.setData(Qt.UserRole, attendance_id)  # Storing attendance_id as user data
                    self.recordsList.addItem(listItem)
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

                
    def markAttendance(self):
        lesson_id = self.lessonComboBox.currentData()
        user_id = self.studentComboBox.currentData()
        status = self.statusComboBox.currentText().lower()  # Convert status to lowercase
        created_by = self.user.id  # Assuming self.user.id holds the ID of the current user

        if not lesson_id or self.lessonComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid lesson.")
            return
        if not user_id or self.studentComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid student.")
            return
        if not status or self.statusComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid status.")
            return

        try:
            # Check if an attendance record already exists for the selected student and lesson
            query = """
            SELECT attendance_id FROM lessonattendance
            WHERE user_id = %s AND lesson_id = %s
            """
            self.cur.execute(query, (user_id, lesson_id))
            existing_record = self.cur.fetchone()

            if existing_record:  # Record exists, so update it
                attendance_id = existing_record[0]
                query = """
                UPDATE lessonattendance
                SET status = %s, created_by = %s
                WHERE attendance_id = %s
                """
                self.cur.execute(query, (status, created_by, attendance_id))
            else:  # No existing record, insert new
                query = """
                INSERT INTO lessonattendance (user_id, lesson_id, status, created_by)
                VALUES (%s, %s, %s, %s)
                """
                self.cur.execute(query, (user_id, lesson_id, status, created_by))
            
            self.conn.commit()
            self.loadAttendanceRecords()  # Reload the attendance records
            QMessageBox.information(self, 'Success', 'Attendance record updated successfully' if existing_record else 'Attendance marked successfully')
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')





    def populateFields(self, item):
        attendance_id = item.data(Qt.UserRole)  # Retrieve the attendance_id directly from the item's user data
        if attendance_id:
            try:
                # Query to fetch the attendance record details based on attendance_id
                query = """
                SELECT la.user_id, la.lesson_id, la.status
                FROM lessonattendance la
                WHERE la.attendance_id = %s
                """
                self.cur.execute(query, (attendance_id,))
                record = self.cur.fetchone()
                if record:
                    user_id, lesson_id, status = record
                    
                    # Find and set the index of the studentComboBox based on user_id
                    index = self.studentComboBox.findData(user_id)
                    if index >= 0:
                        self.studentComboBox.setCurrentIndex(index)
                    
                    # Find and set the index of the lessonComboBox based on lesson_id
                    index = self.lessonComboBox.findData(lesson_id)
                    if index >= 0:
                        self.lessonComboBox.setCurrentIndex(index)
                    
                    # Find and set the index of the statusComboBox based on status
                    index = self.statusComboBox.findText(status, Qt.MatchFixedString)
                    if index >= 0:
                        self.statusComboBox.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, 'Not Found', 'Attendance record not found.')
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

            
    
    def deleteSelectedAttendance(self):
        selected_items = self.recordsList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Selection Error', 'Please select an attendance record to delete.')
            return

        for item in selected_items:
            attendance_id = item.data(Qt.UserRole)  # Retrieve the attendance_id directly from the item's user data
            if attendance_id is None:
                QMessageBox.warning(self, 'Selection Error', 'Failed to retrieve attendance ID.')
                continue

            try:
                query = "DELETE FROM lessonattendance WHERE attendance_id = %s"
                self.cur.execute(query, (attendance_id,))
                self.conn.commit()
                # Remove the item from the QListWidget
                self.recordsList.takeItem(self.recordsList.row(item))
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
                self.conn.rollback()

        # Reload the attendance records to reflect the changes
        self.loadAttendanceRecords()


    def deleteSelectedStudentAttendance(self):
        user_id = self.studentComboBox.currentData()
        if not user_id:
            QMessageBox.warning(self, "Selection Error", "Please select a student.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete all attendance records for the selected student?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM lessonattendance WHERE user_id = %s"
                self.cur.execute(query, (user_id,))
                self.conn.commit()
                self.loadAttendanceRecords()  # Reload the attendance records to reflect the changes
                QMessageBox.information(self, 'Success', 'All attendance records for the selected student have been deleted.')
            except psycopg2.Error as e:
                self.conn.rollback()
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')


    def deleteAllAttendance(self):
        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete all attendance records?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM lessonattendance"
                self.cur.execute(query)
                self.conn.commit()
                # Clear all items from the QListWidget
                self.recordsList.clear()
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
                self.conn.rollback()

    def parseAttendanceId(self, record_text):
        # Extract the attendance_id from the record_text
        try:
            # Assuming the attendance_id is stored as user data in the QListWidgetItem
            return int(record_text)
        except (ValueError):
            QMessageBox.critical(self, 'Error', 'Failed to parse attendance ID.')
            return None
                
                
            
            
            
            
        
###########################################################################################################
  # Meeting Schedule Tab
    def showMeetingScheduleTab(self):
        try:
            self.tabWidget.setCurrentIndex(4)
            
            # Find or create UI elements for meeting schedule management
            self.meeting_date_input = self.findChild(QLineEdit, 'meetingDateInput')
            self.meeting_title = self.findChild(QLineEdit, 'meetingTitle')
            self.meeting_time_slot = self.findChild(QLineEdit, 'meetingTimeSlot')
            self.add_meeting_btn = self.findChild(QPushButton, 'addMeetingBtn')
            self.reset_meeting_btn = self.findChild(QPushButton, 'resetMeetingBtn')
            self.delete_meeting_btn = self.findChild(QPushButton, 'deleteMeetingBtn')
            self.delete_all_meetings_btn = self.findChild(QPushButton, 'deleteAllMeetingsBtn')
            self.meeting_table = self.findChild(QTableWidget, 'meetingTable')

            # Initialize the meeting table
            self.meeting_table.setColumnCount(3)
            self.meeting_table.setHorizontalHeaderLabels(["Meeting Title", "Meeting Date", "Meeting Time"])
            header = self.meeting_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Interactive)
            self.meeting_table.setSelectionBehavior(QTableWidget.SelectRows)
            
            # Connect buttons to their respective functions
            self.add_meeting_btn.clicked.connect(self.addMeeting)
            self.reset_meeting_btn.clicked.connect(self.resetMeetingButton)
            self.meeting_date_input.mousePressEvent = self.showMeetingCalendar
            self.delete_meeting_btn.clicked.connect(self.deleteMeeting)
            self.delete_all_meetings_btn.clicked.connect(self.deleteAllMeetings)
            self.meeting_table.itemClicked.connect(self.selectMeeting)
            
            # Set column widths
            character_width = 12
            self.meeting_table.setColumnWidth(0, 35 * character_width)
            self.meeting_table.setColumnWidth(1, 12 * character_width)
            self.meeting_table.setColumnWidth(2, 12 * character_width)
            
            # Load meetings from the database
            self.loadMeetings()
            
            self.selected_meeting_index = None  # Initialize the selected meeting index
            self.loadMeetings()
        except Exception as e:
            print(f"Error in showMeetingScheduleTab: {e}")
            QMessageBox.warning(self, "Error", f"An error occurred in showMeetingScheduleTab: {str(e)}")

    def setupMeetingCalendar(self):
        self.meeting_calendar = QCalendarWidget(self)
        self.meeting_calendar.setWindowFlags(Qt.Popup)
        self.meeting_calendar.setGridVisible(True)
        self.meeting_calendar.hide()
        self.meeting_calendar.clicked.connect(self.updateMeetingDateInput)

    def updateMeetingDateInput(self, date):
        formatted_meeting_date = date.toString("yyyy-MM-dd")
        self.meeting_date_input.setText(formatted_meeting_date)
        self.meeting_calendar.hide()

    def isValidTimeSlot(self, time_slot):
        pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}$'
        return re.match(pattern, time_slot)

    def showMeetingCalendar(self, event):
        meeting_calendar_pos = self.meeting_date_input.mapToGlobal(self.meeting_date_input.rect().bottomLeft())
        self.meeting_calendar.move(meeting_calendar_pos)
        self.meeting_calendar.show()
        
    
    def selectMeeting(self, item):
        current_row = self.meeting_table.row(item)
        if current_row >= 0:
            meeting_item = self.meeting_table.item(current_row, 0)
            date_item = self.meeting_table.item(current_row, 1)
            time_item = self.meeting_table.item(current_row, 2)
            if meeting_item and date_item and time_item:
                meeting_name = meeting_item.text()
                date = date_item.text()
                time = time_item.text()
                self.meeting_title.setText(meeting_name)
                self.meeting_date_input.setText(date)
                self.meeting_time_slot.setText(time)
                self.selected_meeting_index = current_row
            else:
                print("Some items are None!")

    def loadMeetings(self):
        self.meeting_table.clearContents()
        self.meeting_table.setRowCount(0)
        query = "SELECT meeting_id, meeting_name, meeting_date, meeting_time_slot FROM meeting WHERE teacher_id = %s ORDER BY meeting_date ASC"
        self.cur.execute(query, (self.user.id,))
        meetings = self.cur.fetchall()
        for meeting_id, meeting_name, meeting_date, meeting_time_slot in meetings:
            rowPosition = self.meeting_table.rowCount()
            self.meeting_table.insertRow(rowPosition)
            self.meeting_table.setItem(rowPosition, 0, QTableWidgetItem(meeting_name))
            # Format meeting_date as a string in the format "yyyy-MM-dd"
            meeting_date_str = meeting_date.strftime("%Y-%m-%d") if isinstance(meeting_date, datetime.date) else meeting_date
            self.meeting_table.setItem(rowPosition, 0, QTableWidgetItem(meeting_name))
            self.meeting_table.setItem(rowPosition, 1, QTableWidgetItem(meeting_date_str))
            self.meeting_table.setItem(rowPosition, 2, QTableWidgetItem(meeting_time_slot))
            # Set meeting_id as user data for the first column's item
            self.meeting_table.item(rowPosition, 0).setData(Qt.UserRole, meeting_id)

    def addMeeting(self):
        title = self.meeting_title.text().strip()
        date = self.meeting_date_input.text().strip()
        time = self.meeting_time_slot.text().strip()
        created_by = self.user.id

        if not title or not date or not time:
            QMessageBox.warning(self, "Input Error", "All fields must be filled out.")
            return

        if not self.isValidTimeSlot(time):
            QMessageBox.warning(self, "Input Error", "Time slot must be in the format xx:xx-xx:xx.")
            return

        try:
            if self.selected_meeting_index is not None:
                meeting_id = self.meeting_table.item(self.selected_meeting_index, 0).data(Qt.UserRole)
                query = "UPDATE meeting SET meeting_name = %s, meeting_date = %s, meeting_time_slot = %s, created_by = %s WHERE meeting_id = %s"
                self.cur.execute(query, (title, date, time, created_by, meeting_id))
            else:
                query = "INSERT INTO meeting (meeting_name, meeting_date, meeting_time_slot, teacher_id, created_by) VALUES (%s, %s, %s, %s, %s)"
                self.cur.execute(query, (title, date, time, self.user.id, created_by))
            
            self.conn.commit()
            self.loadMeetings()
            QMessageBox.information(self, 'Success', 'Meeting updated successfully' if self.selected_meeting_index is not None else 'Meeting added successfully')
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
        self.meeting_title.clear()
        self.meeting_date_input.clear()
        self.meeting_time_slot.clear()
        self.selected_meeting_index = None  # Reset the selected meeting index

    def resetMeetingButton(self):
        self.meeting_title.clear()
        self.meeting_date_input.clear()
        self.meeting_time_slot.clear()
        self.selected_meeting_index = None

    def deleteMeeting(self):
        selected_rows = set()
        for item in self.meeting_table.selectedItems():
            selected_rows.add(item.row())
        for row in sorted(selected_rows, reverse=True):
            meeting_id = self.meeting_table.item(row, 0).data(Qt.UserRole)
            if meeting_id:
                try:
                    query = "DELETE FROM meeting WHERE meeting_id = %s"
                    self.cur.execute(query, (meeting_id,))
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")
            self.meeting_table.removeRow(row)

        # Clear the line edits
        self.meeting_title.clear()
        self.meeting_date_input.clear()
        self.meeting_time_slot.clear()
        self.selected_meeting_index = None  # Reset the selected meeting index

    def deleteAllMeetings(self):
        try:
            query = "DELETE FROM meeting WHERE teacher_id = %s"
            self.cur.execute(query, (self.user.id,))
            self.conn.commit()
            self.loadMeetings()
            QMessageBox.information(self, 'Success', 'All meetings have been deleted.')
        except Exception as e:
            self.conn.rollback()
            QMessageBox.warning(self, "Error", f"An error occurred: {str(e)}")

        # Clear the line edits
        self.meeting_title.clear()
        self.meeting_date_input.clear()
        self.meeting_time_slot.clear()
        self.selected_meeting_index = None  # Reset the selected meeting index

    def selectMeeting(self, item):
        current_row = self.meeting_table.row(item)
        if current_row >= 0:
            title_item = self.meeting_table.item(current_row, 0)
            date_item = self.meeting_table.item(current_row, 1)
            time_item = self.meeting_table.item(current_row, 2)
            if title_item and date_item and time_item:
                title = title_item.text()
                date = date_item.text()
                time = time_item.text()
                self.meeting_title.setText(title)
                self.meeting_date_input.setText(date)
                self.meeting_time_slot.setText(time)
                self.selected_meeting_index = current_row
            else:
                QMessageBox.warning(self, "Selection Error", "Failed to retrieve meeting details.")
 
    
###########################################################################################################
    def showMeetingAttendanceTab(self):
        self.tabWidget.setCurrentIndex(5)
            
        # Initialize UI elements for meeting attendance management
        self.meetingComboBox = self.findChild(QComboBox, 'meetingComboBox_2')
        self.studentComboBox = self.findChild(QComboBox, 'studentComboBox_2')
        self.statusComboBox = self.findChild(QComboBox, 'statusComboBox_2')
        self.markAttendanceBtn = self.findChild(QPushButton, 'markAttendanceBtn_2')
        self.recordsList = self.findChild(QListWidget, 'recordsList_2')
            
        # Initialize delete buttons
        self.deleteAttendanceBtn = self.findChild(QPushButton, 'deleteAttendanceBtn_2')
        self.deleteAllAttendanceBtn = self.findChild(QPushButton, 'deleteAllAttendanceBtn_2')
        self.deleteSelectedStudentAttendanceBtn = self.findChild(QPushButton, 'deleteSelectedStudentAttendanceBtn_2')
        # Connect buttons to their respective methods
        self.deleteAttendanceBtn.clicked.connect(self.deleteSelectedMeetingAttendance)
        self.deleteAllAttendanceBtn.clicked.connect(self.deleteAllMeetingAttendance)
        self.deleteSelectedStudentAttendanceBtn.clicked.connect(self.deleteSelectedStudentMeetingAttendance)
            
        # Connect the studentComboBox's signal to the loadAttendanceRecords method
        self.studentComboBox.currentIndexChanged.connect(self.loadMeetingAttendanceRecords)

        # Populate combo boxes
        self.populateMeetingComboBox()
        self.populateStudentComboBox()

        # Connect the 'Mark Attendance' button click to the method
        self.markAttendanceBtn.clicked.connect(self.markMeetingAttendance)
            
        # Connect the itemClicked signal to the populateFields method
        self.recordsList.itemClicked.connect(self.populateMeetingFields)
            
        # Clear existing items in recordsList and reset combo boxes
        self.recordsList.clear()
        self.meetingComboBox.setCurrentIndex(0)
        self.studentComboBox.setCurrentIndex(0)
        self.statusComboBox.setCurrentIndex(0)
            
        # Initialize statusComboBox with placeholder and options
        self.statusComboBox.clear()  # Clear existing items
        self.statusComboBox.addItem("Please select a status...")  # Add placeholder text
        for status in ['Present', 'Absent', 'Late']:
            self.statusComboBox.addItem(status)    
               
                
        

    def populateMeetingComboBox(self):
        self.meetingComboBox.clear()  # Clear existing items
        font = self.meetingComboBox.font()  # Get the current font
        font.setPointSize(12)  # Set the font size
        self.meetingComboBox.setFont(font)  # Apply the font
        
        self.meetingComboBox.addItem("Please select a meeting...")  # Add placeholder text
        
        self.cur.execute("SELECT meeting_id, meeting_name, meeting_date, meeting_time_slot FROM meeting")
        meetings = self.cur.fetchall()
        for meeting_id, meeting_name, meeting_date, meeting_time_slot in meetings:
            display_text = f"{meeting_name} - {meeting_date} - {meeting_time_slot}"
            self.meetingComboBox.addItem(display_text, meeting_id)
            
    def populateStudentComboBox(self):
        self.studentComboBox.clear()  # Clear existing items
        font = self.studentComboBox.font()  # Get the current font
        font.setPointSize(12)  # Set the font size
        self.studentComboBox.setFont(font)  # Apply the font
        
        self.studentComboBox.addItem("Please select a student...")  # Add placeholder text
        self.cur.execute("SELECT user_id, name, surname, email FROM users WHERE user_type = 'student'")
        students = self.cur.fetchall()
        for user_id, name, surname, email in students:
            display_text = f"{name} {surname} - {email}"
            self.studentComboBox.addItem(display_text, user_id)        
              

    def loadMeetingAttendanceRecords(self):
        self.recordsList.clear()  # Clear existing items
        self.recordsList.setFont(QtGui.QFont("Courier New", 12))  # Set monospaced font

        
        user_id = self.studentComboBox.currentData()
        if user_id:
            try:
                query = """
                SELECT ma.attendance_id, m.meeting_name, m.meeting_date, m.meeting_time_slot, ma.status
                FROM meetingattendance ma
                JOIN meeting m ON ma.meeting_id = m.meeting_id
                WHERE ma.user_id = %s
                """
                self.cur.execute(query, (user_id,))
                records = self.cur.fetchall()
                for attendance_id, meeting_name, meeting_date, meeting_time_slot, status in records:
                    # Convert lesson_date to string if it's a date object (adjust format as needed)
                    meeting_date_str = meeting_date.strftime("%Y-%m-%d") if isinstance(meeting_date, datetime.date) else meeting_date
                    
                    record_text = f"Meeting: {meeting_name:40s} Date: {meeting_date_str:10s} Time: {meeting_time_slot:13s} Status: {status.capitalize():10s}"
                    listItem = QListWidgetItem(record_text)
                    listItem.setData(Qt.UserRole, attendance_id)  # Storing attendance_id as user data
                    self.recordsList.addItem(listItem)
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def markMeetingAttendance(self):
        meeting_id = self.meetingComboBox.currentData()
        user_id = self.studentComboBox.currentData()
        status = self.statusComboBox.currentText().lower()  # Convert status to lowercase
        created_by = self.user.id  # Assuming self.user.id holds the ID of the current user

        if not meeting_id or self.meetingComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid meeting.")
            return
        if not user_id or self.studentComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid student.")
            return
        if not status or self.statusComboBox.currentIndex() == 0:
            QMessageBox.warning(self, "Input Error", "Please select a valid status.")
            return

        try:
            query = """
            SELECT attendance_id FROM meetingattendance
            WHERE user_id = %s AND meeting_id = %s
            """
            self.cur.execute(query, (user_id, meeting_id))
            existing_record = self.cur.fetchone()

            if existing_record:
                attendance_id = existing_record[0]
                query = """
                UPDATE meetingattendance
                SET status = %s, created_by = %s
                WHERE attendance_id = %s
                """
                self.cur.execute(query, (status, created_by, attendance_id))
            else:
                query = """
                INSERT INTO meetingattendance (user_id, meeting_id, status, created_by)
                VALUES (%s, %s, %s, %s)
                """
                self.cur.execute(query, (user_id, meeting_id, status, created_by))
            
            self.conn.commit()
            self.loadMeetingAttendanceRecords()  # Reload the attendance records
            QMessageBox.information(self, 'Success', 'Attendance record updated successfully' if existing_record else 'Attendance marked successfully')
        except psycopg2.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def populateMeetingFields(self, item):
        attendance_id = item.data(Qt.UserRole)  # Retrieve the attendance_id directly from the item's user data
        if attendance_id:
                try:
                    query = """
                    SELECT ma.user_id, ma.meeting_id, ma.status
                    FROM meetingattendance ma
                    WHERE ma.attendance_id = %s
                    """
                    self.cur.execute(query, (attendance_id,))
                    record = self.cur.fetchone()
                    if record:
                        user_id, meeting_id, status = record
                        index = self.studentComboBox.findData(user_id)
                        if index >= 0:
                            self.studentComboBox.setCurrentIndex(index)
                        index = self.meetingComboBox.findData(meeting_id)
                        if index >= 0:
                            self.meetingComboBox.setCurrentIndex(index)
                        index = self.statusComboBox.findText(status, Qt.MatchFixedString)
                        if index >= 0:
                            self.statusComboBox.setCurrentIndex(index)
                    else:
                        QMessageBox.warning(self, 'Not Found', 'Attendance record not found.')
                        
                except psycopg2.Error as e:
                    QMessageBox.critical(self, 'Error', f'An error occurred: {e}')    

    # Methods for deleting attendance records (deleteSelectedMeetingAttendance, deleteAllMeetingAttendance, deleteSelectedStudentMeetingAttendance) should be similarly adjusted for meeting attendance.

    def deleteSelectedMeetingAttendance(self):
        selected_items = self.recordsList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Selection Error', 'Please select a meeting attendance record to delete.')
            return

        for item in selected_items:
            attendance_id = item.data(Qt.UserRole)  # Retrieve the attendance_id directly from the item's user data
            if attendance_id is None:
                QMessageBox.warning(self, 'Selection Error', 'Failed to retrieve attendance ID.')
                continue

            try:
                query = "DELETE FROM meetingattendance WHERE attendance_id = %s"
                self.cur.execute(query, (attendance_id,))
                self.conn.commit()
                # Remove the item from the QListWidget
                self.recordsList.takeItem(self.recordsList.row(item))
            except psycopg2.Error as e:
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
                self.conn.rollback()

        # Reload the attendance records to reflect the changes
        self.loadMeetingAttendanceRecords()

    

    def deleteSelectedStudentMeetingAttendance(self):
        user_id = self.studentComboBox.currentData()
        if not user_id:
            QMessageBox.warning(self, "Selection Error", "Please select a student.")
            return

        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete all meeting attendance records for the selected student?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM meetingattendance WHERE user_id = %s"
                self.cur.execute(query, (user_id,))
                self.conn.commit()
                self.loadMeetingAttendanceRecords()  # Reload the attendance records to reflect the changes
                QMessageBox.information(self, 'Success', 'All meeting attendance records for the selected student have been deleted.')
            except psycopg2.Error as e:
                self.conn.rollback()
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
            
    def deleteAllMeetingAttendance(self):
        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete all meeting attendance records?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM meetingattendance"
                self.cur.execute(query)
                self.conn.commit()
                # Clear all items from the QListWidget
                self.recordsList.clear()
            except psycopg2.Error as e:
                self.conn.rollback()
                QMessageBox.critical(self, 'Error', f'An error occurred: {e}')   
                
    def parseAttendanceId(self, record_text):
        # Extract the attendance_id from the record_text
        try:
            # Assuming the attendance_id is stored as user data in the QListWidgetItem
            return int(record_text)
        except (ValueError):
            QMessageBox.critical(self, 'Error', 'Failed to parse attendance ID.')
            return None     
        
        
        
        
        
        
        
        
        
        
        
###########################################################################################################
    def add_todolist_tab(self):
        self.tabWidget.setCurrentIndex(7)

    def add_message_tab(self):
        self.chattedUser = 0
        self.tabWidget.setCurrentIndex(8)
        self.messageCombobox = self.findChild(QComboBox, 'messageCombobox')
        self.listView_t.clicked.connect(self.read_message)

        
        self.load_chat_persons()
        self.populateMessageCombobox()

        self.messageCombobox.setCurrentIndex(0)
        self.messageCombobox.activated.connect(lambda index: self.chatUser(self.messageCombobox.itemData(index)))

    def read_message(self):
        self.model = QStandardItemModel()
        self.list_view_3_t.setModel(self.model)

        selected_indexes = self.listView_t.selectedIndexes()
        for index in selected_indexes:
            item = self.model2.itemFromIndex(index)
            item.setBackground(QColor("white"))
    
    def chatUser(self, user):
        if not user:
            user = 0
        self.chattedUser =  user
        self.cur.execute(f'''
SELECT name, surname, email FROM users WHERE user_id = {user}
''')
       
        data = self.cur.fetchone()
        if data:
            self.message_username.setText(f'{data[0]} {data[1]}')
            self.message_usermail.setText(f'{data[2]}')
        else:
            self.message_username.clear()
            self.message_usermail.clear()
        
        print(user)
        self.loadMessages(user)
        self.cur.execute(f'''UPDATE message SET message_read = true WHERE receiver_id = {self.user.id} and sender_id = {user}''')

    def send_message(self):
        message_text = self.LineEdit_3_t.text()

        try:
            self.cur.execute(f'''
INSERT INTO message (
content, sender_id, receiver_id
) VALUES ('{message_text}', {self.user.id}, {self.chattedUser})
''')
            self.LineEdit_3_t.clear()
            self.loadMessages(self.chattedUser)
        except (Exception, psycopg2.DatabaseError) as error:
            QMessageBox.warning(self, "Message Send Error", str(error))
        
        


    def loadMessages(self, user):
        if not user:
            user = 0
        self.cur.execute(f'''SELECT users.name, message.content, message.message_read, message.created_time, message.sender_id FROM
message full JOIN users ON  users.user_id = message.sender_id
WHERE sender_id = {self.user.id} and receiver_id = {user} or sender_id = {user} and receiver_id = {self.user.id}
ORDER BY created_time ASC''')
        
        messages = self.cur.fetchall()
        

        self.model = QStandardItemModel()
        self.list_view_3_t.setModel(self.model)
        self.list_view_3_t.setItemDelegate(BorderDelegate())

        if messages:
            for name, content, message_read, created_time, sender_id in messages:
                display_text = f'''
    Sender: {name}
    Content: {content}
    Time: {created_time}
    '''
                item = QStandardItem(display_text)
                if sender_id == self.user.id:
                    item.setTextAlignment(Qt.AlignRight)
                self.model.appendRow(item)
        
        # self.list_view_3_t.setModel(self.model)




    def populateMessageCombobox(self):
        self.messageCombobox.clear()
        self.messageCombobox.addItem("Search User for Chat", 0)
        self.cur.execute('''
SELECT user_id, name, surname, email FROM users
''')
        users = self.cur.fetchall()
        for user_id, name, surname, email in users:
            display_text = f"{name} - {email}"
            self.messageCombobox.addItem(display_text, user_id)

    def load_chat_persons(self):
        self.model2 = QStandardItemModel()
        self.listView_t.setModel(self.model2)
        self.cur.execute(f'''
SELECT DISTINCT users.user_id, users.email, users.name
FROM users
JOIN (
    SELECT DISTINCT sender_id AS chat_partner_id
    FROM message
    WHERE receiver_id = {self.user.id}
    UNION
    SELECT DISTINCT receiver_id AS chat_partner_id
    FROM message
    WHERE sender_id = {self.user.id}
) AS chat_partners
ON users.user_id = chat_partners.chat_partner_id; 
''')
        chat_persons = self.cur.fetchall()
        for user_id, email, name in chat_persons:
            self.cur.execute(f'''SELECT users.name, message.content, message.message_read, message.created_time, message.sender_id FROM
message full JOIN users ON  users.user_id = message.sender_id
WHERE sender_id = {user_id} and receiver_id = {self.user.id} and message_read = false''')
            messages = self.cur.fetchall()
            display_text = f"{name} - {email}"
            item = QStandardItem(display_text)
            if messages:
                item.setBackground(QColor('green'))
            item.setData(user_id, Qt.UserRole)
            self.model2.appendRow(item)

        self.listView_t.clicked.connect(self.on_list_item_clicked)

    def on_list_item_clicked(self, index):
        # Retrieve the selected user_id
        selected_index = index.row()
        selected_user_id = self.model2.item(selected_index).data(Qt.UserRole)
        self.chatUser(selected_user_id)    
        
    def add_announce_tab(self):
        self.tabWidget.setCurrentIndex(6)
        self.edittedAnnouncement = None
        self.populateAnnouncementCombobox()
        self.announcementCombobox = self.findChild(QComboBox, 'announcementCombobox')
        self.load_announcement()
        self.date_input = self.findChild(QLineEdit, 'announcementDate')
        self.date_input.mousePressEvent = self.showCalendarAnnouncement
        self.addButton.clicked.connect(self.add_announcement)
        self.editButton.clicked.connect(self.edit_announcement)
        self.deleteButton.clicked.connect(self.delete_announcement)

        self.announcementCombobox.setCurrentIndex(0)
        self.announcementCombobox.activated.connect(lambda index: self.selectAnnouncement(self.announcementCombobox.itemData(index)))


    def showCalendarAnnouncement(self, event):
        calendar_pos = self.date_input.mapToGlobal(self.date_input.rect().bottomLeft())
        self.calendar.move(calendar_pos)
        self.calendar.show()

    def load_announcement(self):
        self.model = QStandardItemModel()
        self.announcementListView.setModel(self.model)

        self.cur.execute('''
SELECT message, deadline, created_by, title, users.email 
FROM announcement JOIN users ON created_by = users.user_id
''')
        announcements = self.cur.fetchall()
        for message, deadline, created_by, title, author in announcements:
            display_text = f'''
Author: {author}
Title: {title}
Message: {message}
'''
            item = QStandardItem(display_text)
            self.model.appendRow(item)

    def selectAnnouncement(self, id):
        if not id:
            id = 0
        self.edittedAnnouncement = id
        text = self.announcementCombobox.currentText()
        if text != 'Select Announcement for Edit':
            self.announcementTitle.setText(text)
        

        self.cur.execute(f'''
SELECT message, deadline FROM announcement
WHERE announcement_id = {id} 
''')
        self.textEdit.clear()
        data = self.cur.fetchone()
        if data:
            context = data[0]
            self.textEdit.append(context)
            self.date_input.setText(str(data[1]))


    def add_announcement(self):
        text = self.textEdit.toPlainText()
        title = self.announcementTitle.text()
        date = self.date_input.text().strip()

        try:

            self.cur.execute(f'''
    INSERT INTO announcement (
    message, deadline, created_by, title
    ) VALUES (
    '{text}', '{date}', {self.user.id}, '{title}'
    );''')
            QMessageBox.warning(self, 'Success', 'Announcement Added Successfully')
            self.load_announcement()
            self.populateAnnouncementCombobox()
            self.textEdit.clear()
            self.announcementTitle.clear()
        except psycopg2.Error as e:
            QMessageBox.critical(self, 'Insert Error', f'Error: {e}')

    def edit_announcement(self):
        text = self.textEdit.toPlainText()
        title = self.announcementTitle.text()
        date = self.date_input.text().strip()

        if self.edittedAnnouncement:
            if self.edittedAnnouncement != 0:
                print(self.edittedAnnouncement)
                try:
                    self.cur.execute(f'''
            UPDATE announcement 
            SET message = '{text}', deadline = '{date}', title = '{title}'
            WHERE announcement_id = {self.edittedAnnouncement};''')
                    QMessageBox.warning(self, 'Success', 'Announcement Updated Successfully')
                    self.load_announcement()
                    self.populateAnnouncementCombobox()
                    self.textEdit.clear()
                    self.announcementTitle.clear()
                except psycopg2.Error as e:
                    QMessageBox.critical(self, 'Edit Error', f'Error: {e}')

    def delete_announcement(self):
        if self.edittedAnnouncement and self.edittedAnnouncement != 0:
            reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete announcement?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.cur.execute(f'''
DELETE FROM announcement WHERE announcement_id = {self.edittedAnnouncement}            
''')
                    QMessageBox.warning(self, 'Success', 'Announcement Deleted Successfully')
                    self.load_announcement()
                    self.populateAnnouncementCombobox()
                    self.textEdit.clear()
                    self.announcementTitle.clear()
                except psycopg2.Error as e:
                    QMessageBox.critical(self, 'Edit Error', f'Error: {e}')
        else:
            QMessageBox.warning(self, 'Error', 'There is no selected announcement')




        
        

    def populateAnnouncementCombobox(self):
        self.announcementCombobox.clear()
        self.announcementCombobox.addItem('Select Announcement for Edit', 0)
#         
        self.cur.execute('''
SELECT title, announcement_id FROM announcement
''')
        announcement_titles = self.cur.fetchall()
        for title, announcement_id in announcement_titles:
            text = f'''{title}'''
            self.announcementCombobox.addItem(text, announcement_id)

    def logout(self):
        self.close()
        self.show_login()
    
    def show_login(self):
        self.login.emit(True)

    def updateTeacherDetails(self):
        self.user.name = self.tb23.text()
        self.user.surname = self.tb24.text()
        self.user.phone = self.tb26.text()

        command = '''
UPDATE users
SET name = %s, surname = %s, phone = %s
WHERE users.email = %s;
'''

        try:
            cur = self.conn.cursor()
            cur.execute(command, (self.user.name, self.user.surname, self.user.phone, self.user.email))
            cur.close()
            self.conn.commit()
            QMessageBox.information(self, "Update Information", "User updated successfully")
        except (Exception, psycopg2.DatabaseError) as error:
            QMessageBox.warning(self, "Update Error", str(error))
