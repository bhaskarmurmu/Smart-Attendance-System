import pandas as pd
import json
from datetime import datetime
import os

# --- File Paths ---
# Get the absolute path of the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_FILE = os.path.join(SCRIPT_DIR, 'students.csv')
TIMETABLE_FILE = os.path.join(SCRIPT_DIR, 'timetable.json')
ATTENDANCE_FILE = os.path.join(SCRIPT_DIR, 'attendance.xlsx')
# --------------------

def generate_absentee_report():
    """
    Checks all students against today's schedule. If a student
    was not marked 'Present' for a scheduled class, marks them 'Absent'.
    """
    
    print("Generating absentee report...")
    
    try:
        # Load all data
        print(f"Attempting to load: {STUDENTS_FILE}") # Added debug print
        # Read 'RollNo' explicitly as a string type
        all_students_df = pd.read_csv(STUDENTS_FILE, dtype={'RollNo': str})
        
        print(f"Attempting to load: {TIMETABLE_FILE}") # Added debug print
        with open(TIMETABLE_FILE, 'r') as f:
            timetable = json.load(f)
            
        # Check if attendance file exists. If not, create an empty one.
        print(f"Checking for: {ATTENDANCE_FILE}") # Added debug print
        if os.path.exists(ATTENDANCE_FILE):
             # Ensure RollNo is read as string to match students.csv
            attendance_df = pd.read_excel(ATTENDANCE_FILE, dtype={'RollNo': str})
        else:
            print("Attendance file not found. Creating a new one.")
            attendance_df = pd.DataFrame(columns=['RollNo', 'Name', 'Date', 'Time', 'Day', 'Subject', 'Status'])
            attendance_df.to_excel(ATTENDANCE_FILE, index=False)
            
        # No longer needed, as dtype is set at read
        # all_students_df['RollNo'] = all_students_df['RollNo'].astype(str)
        
    except FileNotFoundError as e:
        print(f"Error: Could not find file {e.filename}. Cannot generate report.")
        return
    except Exception as e:
        print(f"An error occurred loading files: {e}")
        return

    now = datetime.now()
    today_str = now.strftime('%A')
    date_str = now.strftime('%Y-%m-%d')
    
    if today_str not in timetable or not timetable[today_str]:
        print(f"No classes scheduled for today ({today_str}). No report generated.")
        return
        
    todays_classes = timetable[today_str]
    new_absent_entries = []

    # Iterate over every student
    for _, student in all_students_df.iterrows():
        roll_no = student['RollNo']
        name = student['Name']
        
        # Iterate over every class scheduled for today
        for class_slot in todays_classes:
            subject = class_slot['subject']
            
            # Check if this student was marked 'Present' for this subject today
            is_present = not attendance_df[
                (attendance_df['RollNo'] == roll_no) &
                (attendance_df['Subject'] == subject) &
                (attendance_df['Date'] == date_str) &
                (attendance_df['Status'] == 'Present')
            ].empty
            
            # Check if an 'Absent' entry *already* exists
            is_absent = not attendance_df[
                (attendance_df['RollNo'] == roll_no) &
                (attendance_df['Subject'] == subject) &
                (attendance_df['Date'] == date_str) &
                (attendance_df['Status'] == 'Absent')
            ].empty

            # If not present and not already marked absent, add an 'Absent' entry
            if not is_present and not is_absent:
                absent_entry = {
                    'RollNo': roll_no,
                    'Name': name,
                    'Date': date_str,
                    'Time': 'N/A',
                    'Day': today_str,
                    'Subject': subject,
                    'Status': 'Absent'
                }
                new_absent_entries.append(absent_entry)
                print(f"Marking ABSENT: {roll_no} - {name} for {subject}")

    # If there are new absent entries, append them to the Excel file
    if new_absent_entries:
        absent_df = pd.DataFrame(new_absent_entries)
        
        try:
            # Append new entries to the existing sheet
            with pd.ExcelWriter(ATTENDANCE_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                existing_df = pd.read_excel(ATTENDANCE_FILE)
                startrow = len(existing_df)
                absent_df.to_excel(writer, index=False, header=False, startrow=startrow + 1)
            
            print(f"Successfully added {len(new_absent_entries)} 'Absent' records to {ATTENDANCE_FILE}.")
        
        except Exception as e:
            print(f"Error writing 'Absent' records to Excel: {e}")
    else:
        print("No new 'Absent' records to add.")

if __name__ == "__main__":
    generate_absentee_report()