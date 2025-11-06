Smart Attendance System using OpenCV & Face Recognition
This guide provides all the steps and code required to build your project.

Project Structure
Before you start, create a main project folder. All these files should go inside it. You will also need to create a folder named dataset .

SmartAttendance/
- dataset/                  <-- Create this empty folder
- students.csv              <-- Admin manages this
- timetable.json            <-- Admin manages this
- face_encodings.pkl        <-- This will be generated
- attendance.xlsx           <-- This will be generated
  
1. step_1_data_collection.py
2. step_2_model_training.py
3. step_3_main_attendance.py
4. step_4_generate_report.py


Step 0: Install Dependencies
You need several Python libraries. Install them using pip:

pip install opencv-python-headless
pip install face-recognition
pip install pandas
pip install openpyxl
pip install numpy

Note: face-recognition depends on dlib . This can sometimes be difficult to install on Windows. If you have trouble,
a common solution is to first install cmake and then dlib before installing face- recognition : 

pip install cmake
pip install dlib
pip install face-recognition

Step 1: Admin Setup (Features #1 & #3)

Your first feature request was "admin control". We will handle this by having the admin edit two simple files.
1. students.csv : This file maps student Roll Numbers to their Names. The Roll Number must be unique and will be used to name the image folders.
      - Create students.csv (I've provided a sample file).
      - Add your students here. The RollNo must not have spaces.
2. timetable.json : This file sets the schedule.
      - Create timetable.json (I've provided a sample file).
      - The format is: DayOfWeek: [List of classes] .
      - Time is in 24-hour format ( HH:MM ).
      - You can add as many classes as you want for each day.

Step 2: Data Collection (Gathering Faces)

Now you need to collect face images for each student you added to students.csv .
1.	Run the step_1_data_collection.py script: python step_1_data_collection.py
2.	The script will ask for a Roll Number. Enter a RollNo from your students.csv (e.g., 101 ).
3.	A webcam window will open. Center your face. The script will automatically detect your face, draw a box, and save 30 pictures to a new folder: dataset/101/ .
4.	Once it has 30 pictures, it will quit.
5.	Repeat this process for every student.

Step 3: Model Training

With your dataset of faces, you need to "train" the system. This script will scan all the images, create a unique face "encoding" (a set of numbers) for each student, and save these encodings to a single file.
1.	Run the step_2_model_training.py script: python step_2_model_training.py
2.	This script will:
      - Look inside the dataset/ folder.
      - Process each student's image folder.
      - Create the face encodings.
      - Save all the encodings into a file named face_encodings.pkl .
You only need to re-run this script when you add a new student (or update a student's pictures).

Step 4: Run the Main Attendance System (Feature #2)

This is the main part. This script will run the webcam, check the time, and mark attendance.
1.	Run the step_3_main_attendance.py script: python step_3_main_attendance.py
2.	Here is what it does (your "Working" logic):
      - It starts the webcam.
      - It continuously checks the current time against timetable.json .
      - If no class is scheduled, it will show "No Class Scheduled" on the screen.
      - If a class IS scheduled, it will change the status to "Class: [Subject] (Attendance ON)".
      - During this "ON" time, it will actively try to recognize faces.
      - When it recognizes a student (e.g., "101 - Alice Smith"), it will:
            - Mark them 'Present' for that subject.
            - Instantly save the entry to attendance.xlsx .
            - It will only mark each student once per subject to avoid 1000s of entries.
      - It will draw a green box and their name on the screen. "Unknown" faces get a red box.
3.	Press 'q' to quit the program.
 
Step 5: Generate the Final Report (Absent Logic)

The main script only marks who is 'Present'. At the end of the day (or after all classes are over), you need to run one more script to mark the 'Absent' students.
1.	Run the step_4_generate_report.py script: python step_4_generate_report.py
2.	This script will:
      - Read students.csv (all students).
      - Read timetable.json (all classes for today).
      - Read attendance.xlsx (all 'Present' marks).
      - It will find which students were not marked 'Present' for a class they had scheduled.
      - It will add a new 'Absent' row for each of them (with 'Time' as 'N/A').
      - It will update attendance.xlsx with the complete report.
This two-script (Present/Absent) approach is much more reliable than trying to mark "Absent" in real- time.
