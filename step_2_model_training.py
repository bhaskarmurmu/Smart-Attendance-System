import face_recognition
import os
import pickle

# --- Settings ---
# Get the absolute path of the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, 'dataset')
ENCODINGS_FILE = os.path.join(SCRIPT_DIR, 'face_encodings.pkl')
# -----------------

def train_model():
    """
    Scans the dataset directory, encodes all faces, and saves
    the encodings to a pickle file for later use.
    """
    print("Starting model training...")
    known_face_encodings = []
    known_face_names = [] # This will store Roll Numbers

    # Loop through each person in the dataset
    for roll_no in os.listdir(DATASET_PATH):
        student_dir = os.path.join(DATASET_PATH, roll_no)
        
        # Skip if it's not a directory
        if not os.path.isdir(student_dir):
            continue
            
        print(f"Processing student: {roll_no}")
        
        # Loop through each image for the current person
        for img_name in os.listdir(student_dir):
            img_path = os.path.join(student_dir, img_name)
            
            try:
                # Load the image
                image = face_recognition.load_image_file(img_path)
                
                # Find face encodings. We assume one face per image.
                # face_encodings() returns a list, we take the first one [0].
                encoding = face_recognition.face_encodings(image)[0]
                
                # Add the encoding and the corresponding name (RollNo)
                known_face_encodings.append(encoding)
                known_face_names.append(roll_no)
                
            except Exception as e:
                print(f"Warning: Could not process image {img_path}. Skipping. Error: {e}")

    print(f"Training complete. Found {len(known_face_encodings)} faces.")

    # Save the encodings to a file
    data = {"encodings": known_face_encodings, "names": known_face_names}
    with open(ENCODINGS_FILE, 'wb') as f:
        pickle.dump(data, f)
        
    print(f"Face encodings saved to {ENCODINGS_FILE}")

if __name__ == "__main__":
    train_model()