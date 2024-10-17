import csv
import os
import glob

def create_d2l_from_csv(input_file, output_file):
    with open(input_file, 'r', newline='') as input_handle, \
         open(output_file, 'w', newline='') as output_handle:
        
        csv_reader = csv.reader(input_handle)
        csv_writer = csv.writer(output_handle)

        # Skip the header row in the input file
        next(csv_reader)

        # Initialize a question counter to generate unique IDs
        question_counter = 1

        for row in csv_reader:
            # Check if the row has all required columns
            if len(row) < 9:
                print("Skipping invalid row:", row)
                continue

            # Extract fields from the input CSV and trim any excess spaces
            question_type, question_text, answer_options_str, correct_answer, points, image, hint, feedback, difficulty = [
                field.strip() for field in row[:9]
            ]
            answer_options = [option.strip() for option in answer_options_str.split('|')]

            # Generate a unique ID for the question
            question_id = f"Q{question_counter:03d}"
            question_counter += 1

            # Write the NewQuestion row
            csv_writer.writerow(["NewQuestion", "MC", "", ""])

            # Write the question components in separate rows
            csv_writer.writerow(["ID", question_id, "", ""])
            csv_writer.writerow(["Title", question_text, "", ""])
            csv_writer.writerow(["QuestionText", question_text, "", ""])
            csv_writer.writerow(["Points", points, "", ""])
            csv_writer.writerow(["Difficulty", difficulty, "", ""])
            csv_writer.writerow(["Image", image, "", ""])

            # Write each answer option in a separate row
            for option in answer_options:
                weight = "100" if option == correct_answer else "0"
                csv_writer.writerow(["Option", weight, option])

            # Write the hint and feedback
            csv_writer.writerow(["Hint", hint, "", ""])
            csv_writer.writerow(["Feedback", feedback, "", ""])

            # Add an empty row to separate each question
            csv_writer.writerow(["", "", "", ""])

    print(f"D2L-compatible CSV file created successfully at: {output_file}")

def main():
    # Specify the input and output directories
    input_dir = "html_src"
    output_dir = "html_des"

    # Check if the output directory exists, create it if not
    os.makedirs(output_dir, exist_ok=True)

    # Get all CSV files in the input directory
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

    # Process each CSV file
    for file in csv_files:
        filename = os.path.splitext(os.path.basename(file))[0]
        output_file = os.path.join(output_dir, f"{filename}_d2l.csv")
        create_d2l_from_csv(file, output_file)

if __name__ == "__main__":
    main()