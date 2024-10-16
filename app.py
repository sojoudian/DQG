import csv

def parse_txt_to_questions(txt_file):
    with open(txt_file, 'r') as file:
        lines = file.readlines()

    questions = []
    current_question = ""
    current_options = []
    correct_answer = ""
    question_id = 1

    for line in lines:
        line = line.strip()

        # Check if it's an option
        if line.startswith("•"):
            option_text = line.split(") ")[1]  # Extract the option text after letter
            current_options.append(option_text)
        # Check if it's the correct answer
        elif line.startswith("Correct Answer:"):
            correct_answer = line.split(") ")[1]  # Extract correct answer text
        # Check if it's a new question
        elif line and not line.startswith("Correct Answer") and not line.startswith("•"):
            if current_question:  # If a question was already processed, add it
                questions.append((f"PYTHON-{question_id}", current_question, current_options, correct_answer))
                question_id += 1
            current_question = line
            current_options = []
        elif not line:  # Empty line, signifies the end of a question block
            continue

    # Add the last question if any
    if current_question:
        questions.append((f"PYTHON-{question_id}", current_question, current_options, correct_answer))

    return questions

def generate_csv_from_questions(questions, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        for question_id, question_text, options, correct_answer in questions:
            writer.writerow(["NewQuestion", "MC", "", ""])
            writer.writerow(["ID", question_id, "", ""])
            writer.writerow(["Title", question_text, "", ""])
            writer.writerow(["QuestionText", question_text, "", ""])
            writer.writerow(["Points", "1", "", ""])
            writer.writerow(["Difficulty", "2", "", ""])
            writer.writerow(["Image", "", "", ""])

            # Write the options and mark the correct answer with 100
            for option in options:
                score = "100" if option == correct_answer else "0"
                writer.writerow(["Option", score, option, "", ""])

            writer.writerow(["", "", "", ""])  # Empty row to separate questions

# Example usage
txt_file = 'w2.txt'
output_csv = 'd2l_w2.csv'

questions = parse_txt_to_questions(txt_file)
generate_csv_from_questions(questions, output_csv)

print(f"CSV file '{output_csv}' has been generated with correct answer scoring.")