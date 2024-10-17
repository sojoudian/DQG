import csv

def convert_to_d2l_format(input_csv, output_csv):
    with open(input_csv, mode='r', newline='', encoding='utf-8') as infile, open(output_csv, mode='w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Write the D2L header or any initial metadata rows if required
        writer.writerow(["NewQuestion,WR,,,"])  # Example initial metadata

        # Iterate over each row and process accordingly
        question_data = []
        for row in reader:
            if "NewQuestion" in row[0]:
                # Start new question block
                if question_data:
                    writer.writerows(question_data)
                    writer.writerow([])  # Add empty row between questions
                question_data = [row]  # Reset for the next question
            else:
                question_data.append(row)

        # Write the last question block
        if question_data:
            writer.writerows(question_data)

    print(f"Conversion completed! File saved as: {output_csv}")

# Usage
input_csv = 'input_questions.csv'  
output_csv = 'd2l_brightspace_questions.csv'
convert_to_d2l_format(input_csv, output_csv)