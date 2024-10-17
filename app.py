from flask import Flask, render_template, request, redirect, send_file
import csv
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to process CSV and create D2L-compatible output
def create_d2l_from_csv(input_file, output_file):
    with open(input_file, 'r') as input_handle, open(output_file, 'w', newline='') as output_handle:
        csv_reader = csv.reader(input_handle)
        csv_writer = csv.writer(output_handle)
        next(csv_reader)  # Skip the header row

        question_counter = 1
        for row in csv_reader:
            if len(row) < 9:
                continue

            # Extract fields
            question_type = row[0].strip()
            question_text = row[1].strip()
            answer_options = row[2].strip().split('|')
            correct_answer = row[3].strip()
            points = row[4].strip()
            image = row[5].strip()
            hint = row[6].strip()
            feedback = row[7].strip()
            difficulty = row[8].strip()

            question_id = f"Q{str(question_counter).zfill(3)}"
            question_counter += 1

            # Writing rows to the new D2L format
            csv_writer.writerow(["NewQuestion", "MC", "", ""])
            csv_writer.writerow(["ID", question_id, "", ""])
            csv_writer.writerow(["Title", question_text, "", ""])
            csv_writer.writerow(["QuestionText", question_text, "", ""])
            csv_writer.writerow(["Points", points, "", ""])
            csv_writer.writerow(["Difficulty", difficulty, "", ""])
            csv_writer.writerow(["Image", image, "", ""])

            # Write answer options
            for option in answer_options:
                weight = "100" if option == correct_answer else "0"
                csv_writer.writerow(["Option", weight, option])

            # Write hint and feedback
            csv_writer.writerow(["Hint", hint, "", ""])
            csv_writer.writerow(["Feedback", feedback, "", ""])
            csv_writer.writerow([])  # Empty row to separate questions

# Route for file upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle CSV upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect('/')
    
    file = request.files['file']
    if file.filename == '':
        return redirect('/')
    
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(OUTPUT_FOLDER, f"{os.path.splitext(file.filename)[0]}_d2l.csv")
    
    # Save the uploaded file
    file.save(input_path)
    
    # Process the CSV and create the output
    create_d2l_from_csv(input_path, output_path)
    
    # Redirect to download the generated file
    return redirect(f'/download/{os.path.basename(output_path)}')

# Route to download the generated CSV
@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
