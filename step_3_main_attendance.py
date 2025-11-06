import cv2
import face_recognition
import pandas as pd
import numpy as np
import pickle
import json
import os
from datetime import datetime

# --- File Paths ---
# Get the absolute path of the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENTS_FILE = os.path.join(SCRIPT_DIR, 'students.csv')
TIMETABLE_FILE = os.path.join(SCRIPT_DIR, 'timetable.json')
ENCODINGS_FILE = os.path.join(SCRIPT_DIR, 'face_encodings.pkl')
ATTENDANCE_FILE = os.path.join(SCRIPT_DIR, 'attendance.xlsx')
# --------------------

# --- Global Variables ---
today_log = set() # To keep track of (roll_no, subject) already marked today
students_df = None
timetable = None
known_face_encodings = []
known_face_names = []
# --------------------

def load_data():
    """Loads all necessary data from files into global variables."""
    global students_df, timetable, known_face_encodings, known_face_names
    
    # Load Student Info
    try:
        print(f"Attempting to load: {STUDENTS_FILE}") # Added debug print
        # Read 'RollNo' explicitly as a string type
        students_df = pd.read_csv(STUDENTS_FILE, dtype={'RollNo': str})
        students_df.set_index('RollNo', inplace=True)
        print("Student data loaded.")
    except FileNotFoundError:
        print(f"Error: {STUDENTS_FILE} not found.")
        return False

    # Load Timetable
    try:
        print(f"Attempting to load: {TIMETABLE_FILE}") # Added debug print
        with open(TIMETABLE_FILE, 'r') as f:
            timetable = json.load(f)
        print("Timetable loaded.")
    except FileNotFoundError:
        print(f"Error: {TIMETABLE_FILE} not found.")
        return False
        
    # Load Face Encodings
    try:
        print(f"Attempting to load: {ENCODINGS_FILE}") # Added debug print
        with open(ENCODINGS_FILE, 'rb') as f:
            data = pickle.load(f)
            known_face_encodings = data['encodings']
            known_face_names = data['names']
        print("Face encodings loaded.")
    except FileNotFoundError:
        print(f"Error: {ENCODINGS_FILE} not found. Please run 'step_2_model_training.py' first.")
        return False
        
    return True

def check_current_class():
    """Checks the timetable to see if a class is currently scheduled."""
    now = datetime.now()
    current_day = now.strftime('%A') # e.g., "Monday"
    current_time = now.time()
    
    if current_day not in timetable:
        return None, "No classes scheduled for today."

    for slot in timetable[current_day]:
        try:
            start_time = datetime.strptime(slot['start'], '%H:%M').time()
            end_time = datetime.strptime(slot['end'], '%H:%M').time()
            
            if start_time <= current_time <= end_time:
                return slot['subject'], f"Class: {slot['subject']} (Attendance ON)"
        except ValueError:
            print(f"Warning: Invalid time format in timetable for {current_day} - {slot}")
            
    return None, "No Class Scheduled (Attendance OFF)"

def mark_attendance(roll_no, name, subject):
    """
    Marks a student as 'Present' in the Excel sheet.
    Uses 'today_log' to prevent duplicate entries for the same student/subject.
    """
    global today_log
    
    log_entry = (roll_no, subject)
    
    if log_entry in today_log:
        return # Already marked today for this subject

    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H:%M:%S')
    day_str = now.strftime('%A')
    
    new_entry = pd.DataFrame([{
        'RollNo': roll_no,
        'Name': name,
        'Date': date_str,
        'Time': time_str,
        'Day': day_str,
        'Subject': subject,
        'Status': 'Present'
    }])
    
    print(f"Marking PRESENT: {roll_no} - {name} for {subject}")

    try:
        if not os.path.exists(ATTENDANCE_FILE):
            # Create new file if it doesn't exist
            new_entry.to_excel(ATTENDANCE_FILE, index=False)
        else:
            # Append to existing file
            with pd.ExcelWriter(ATTENDANCE_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                # Read existing data to find the last row
                try:
                    existing_df = pd.read_excel(ATTENDANCE_FILE)
                    startrow = len(existing_df)
                except Exception:
                    startrow = 0
                
                # Append new data without header
                new_entry.to_excel(writer, index=False, header=False, startrow=startrow + 1)

        # Add to today's log to prevent re-marking
        today_log.add(log_entry)
        
    except Exception as e:
        print(f"Error writing to Excel file: {e}")


def run_attendance_system():
    """Main function to run the webcam feed and face recognition."""
    
    if not load_data():
        print("Exiting due to data loading failure.")
        return

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Starting webcam... Press 'q' to quit.")
    
    # Variables for processing optimization
    process_this_frame = True

    while True:
        # Check current class status
        current_subject, status_message = check_current_class()
        
        # Grab a single frame of video
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Only process every other frame to save time
        if process_this_frame:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert BGR to RGB (which face_recognition uses)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find all face locations and encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"

                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    roll_no = known_face_names[best_match_index]
                    
                    try:
                        # Get student name from the loaded dataframe
                        student_name = students_df.loc[roll_no]['Name']
                        name = f"{roll_no} - {student_name}"
                        
                        # If a class is active, mark attendance
                        if current_subject:
                            mark_attendance(roll_no, student_name, current_subject)
                            
                    except KeyError:
                        name = f"{roll_no} - (Name not found)"
                    except Exception as e:
                        print(f"Error looking up student name: {e}")

                face_names.append(name)

        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Set box color
            color = (0, 0, 255) # Red for Unknown
            if name != "Unknown":
                color = (0, 255, 0) # Green for Known
                if not current_subject:
                    color = (0, 165, 255) # Orange if known but no class

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        # Display the current class status on the frame
        status_color = (0, 0, 255) # Red for "Off"
        if current_subject:
            status_color = (0, 255, 0) # Green for "On"
            
        cv2.putText(frame, status_message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)

        # Display the resulting image
        cv2.imshow('Smart Attendance System', frame)

        # Hit 'q' on the keyboard to quit!
        # Increased wait time from 1ms to 5ms for better keypress registration
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_attendance_system()