import http.server
import socketserver
import urllib.parse
import os
import csv
import shutil

PORT = 8002
OUTPUT_FOLDER = 'outputs'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# In-memory storage for questions and ID counter
questions = []
question_id_counter = 1  # Start with ID 1

# Function to generate D2L-compatible CSV from form data
def create_d2l_from_questions(output_file):
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as output_handle:
            csv_writer = csv.writer(output_handle)

            for question in questions:
                question_id = question['id']
                question_text = question['question_text']
                points = question['points']
                difficulty = question['difficulty']
                options = [
                    question['option1'],
                    question['option2'],
                    question['option3'],
                    question['option4']
                ]
                correct_answer_index = int(question['correct_answer']) - 1  # Convert to 0-based index

                # Writing the NewQuestion rows
                csv_writer.writerow(["NewQuestion", "MC", "", ""])
                csv_writer.writerow(["ID", question_id, "", ""])
                csv_writer.writerow(["Title", question_text, "", ""])
                csv_writer.writerow(["QuestionText", question_text, "", ""])
                csv_writer.writerow(["Points", points, "", ""])
                csv_writer.writerow(["Difficulty", difficulty, "", ""])

                # Write each answer option and assign the correct answer weight
                for index, option in enumerate(options):
                    weight = "100" if index == correct_answer_index else "0"
                    csv_writer.writerow(["Option", weight, option.strip()])

                # Add an empty row to separate questions
                csv_writer.writerow([])

        print(f"CSV file created at: {output_file}")
    except Exception as e:
        print(f"Error creating CSV file: {e}")
        raise

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            # Serve the external index.html
            try:
                with open('index.html', 'r') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read().encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "File Not Found: index.html")
        elif path.startswith('/download/'):
            # Handle file download
            filename = os.path.basename(path)
            file_path = os.path.join(OUTPUT_FOLDER, filename)

            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        self.send_response(200)
                        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                        self.send_header('Content-type', 'text/csv')
                        fs = os.fstat(f.fileno())
                        self.send_header("Content-Length", str(fs.st_size))
                        self.end_headers()
                        shutil.copyfileobj(f, self.wfile)
                except Exception as e:
                    print(f"Error serving file {file_path}: {e}")
                    self.send_error(500, 'Internal Server Error')
            else:
                print(f"File not found: {file_path}")
                self.send_error(404, 'File not found.')
        else:
            # Serve other static files if needed
            super().do_GET()

    def do_POST(self):
        global question_id_counter  # To modify the global question_id_counter

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            # Convert the parsed form data to a dictionary
            processed_data = {k: v[0] for k, v in form_data.items()}

            # Automatically assign the incremented question ID
            processed_data['id'] = str(question_id_counter)
            question_id_counter += 1  # Increment for the next question

            # Validate that the points are within the allowed range (0.5 to 3)
            points = float(processed_data['points'])
            if points < 0.5 or points > 3:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>400 Bad Request</h1><p>Points must be between 0.5 and 3.</p>')
                return

            # Store the question in memory
            questions.append(processed_data)

            action = processed_data.get('action')
            if action == 'next':
                # Continue adding more questions
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
            elif action == 'generate':
                # Create output file path
                output_file = os.path.join(OUTPUT_FOLDER, 'd2l_questions.csv')

                # Generate CSV file from all stored questions
                try:
                    create_d2l_from_questions(output_file)
                    questions.clear()  # Clear questions after CSV is generated

                    # Redirect to download the generated CSV file
                    self.send_response(303)  # HTTP 303 See Other
                    self.send_header('Location', f'/download/{os.path.basename(output_file)}')
                    self.end_headers()
                except Exception as e:
                    print(f"Error processing form data: {e}")
                    self.send_response(500)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h1>500 Internal Server Error</h1><p>There was an error processing your request.</p>')
        else:
            # Handle other POST requests if needed
            self.send_error(404, 'File not found.')

    def log_message(self, format, *args):
        # Override to log to console with client address
        print("%s - - [%s] %s" %
              (self.client_address[0],
               self.log_date_time_string(),
               format%args))

# Set up the HTTP server
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Serving on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server.")
        httpd.server_close()
