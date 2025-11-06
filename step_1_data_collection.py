import cv2
import os
import time

# --- Settings ---
# Get the absolute path of the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, 'dataset')
NUM_IMAGES_TO_COLLECT = 30
# -----------------

def collect_data():
    """
    Captures and saves face images for a new student.
    The user will be prompted to enter a Roll Number, which will be used
    as the directory name to store the images.
    """
    
    roll_no = input("Enter Student Roll Number: ")
    if not roll_no:
        print("Roll Number cannot be empty.")
        return

    student_dir = os.path.join(DATASET_PATH, roll_no)
    
    if not os.path.exists(student_dir):
        os.makedirs(student_dir)
        print(f"Directory created: {student_dir}")
    else:
        print(f"Directory {student_dir} already exists. Images may be overwritten.")

    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # Load OpenCV's pre-trained face detector
    # This is simpler than dlib for just finding the face region
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    print(f"Collecting images for RollNo: {roll_no}. Please look at the camera.")
    
    while count < NUM_IMAGES_TO_COLLECT:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        if len(faces) > 0:
            # Assuming only one face for data collection
            (x, y, w, h) = faces[0]
            
            # Draw rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Save the captured face
            face_img = frame[y:y+h, x:x+w]
            img_path = os.path.join(student_dir, f"{count + 1}.jpg")
            cv2.imwrite(img_path, face_img)
            
            count += 1
            
            # Display collecting status
            status_text = f"Collected: {count}/{NUM_IMAGES_TO_COLLECT}"
            print(status_text)
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Display the frame
        cv2.imshow("Data Collection - Press 'q' to quit", frame)
        
        # Give a small delay to allow user to move their head slightly
        time.sleep(0.2) 

        # Quit if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Data collection stopped early by user.")
            break

    print(f"Data collection complete for RollNo: {roll_no}. {count} images saved.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if not os.path.exists(DATASET_PATH):
        os.makedirs(DATASET_PATH)
    collect_data()