import http.server
import socketserver
import urllib.parse
import os
import csv
import shutil

PORT = 8000
OUTPUT_FOLDER = 'outputs'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Function to generate D2L-compatible CSV from form data
def create_d2l_from_form(data, output_file):
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as output_handle:
            csv_writer = csv.writer(output_handle)

            question_id = data.get('id')
            question_text = data.get('question_text')
            points = data.get('points')
            difficulty = data.get('difficulty')
            options = [
                data.get('option1'),
                data.get('option2'),
                data.get('option3'),
                data.get('option4')
            ]
            correct_answer_index = int(data.get('correct_answer')) - 1  # Convert to 0-based index

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


# HTML template for the form
html_form = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Create D2L-Compatible CSV</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        form { max-width: 600px; margin: auto; }
        label { display: block; margin-top: 10px; }
        input[type="text"], input[type="number"] { width: 100%; padding: 8px; box-sizing: border-box; }
        button { margin-top: 20px; padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>Create D2L-Compatible CSV</h1>
    <form action="/submit" method="POST">
        <label for="id">Question ID:</label>
        <input type="text" id="id" name="id" required>

        <label for="question_text">Question Text:</label>
        <input type="text" id="question_text" name="question_text" required>

        <label for="points">Points:</label>
        <input type="number" id="points" name="points" required>

        <label for="difficulty">Difficulty (1-5):</label>
        <input type="number" id="difficulty" name="difficulty" min="1" max="5" required>

        <label for="option1">Option 1:</label>
        <input type="text" id="option1" name="option1" required>

        <label for="option2">Option 2:</label>
        <input type="text" id="option2" name="option2" required>

        <label for="option3">Option 3:</label>
        <input type="text" id="option3" name="option3" required>

        <label for="option4">Option 4:</label>
        <input type="text" id="option4" name="option4" required>

        <label for="correct_answer">Correct Answer:</label>
        <input type="text" id="correct_answer" name="correct_answer" required>

        <button type="submit">Submit</button>
    </form>
</body>
</html>
'''

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/':
            # Serve the form HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_form.encode('utf-8'))
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
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/submit':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))

            # Convert the parsed form data to a dictionary
            processed_data = {k: v[0] for k, v in form_data.items()}

            # Validate required fields
            required_fields = ['id', 'question_text', 'points', 'difficulty', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
            if not all(field in processed_data and processed_data[field].strip() for field in required_fields):
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>400 Bad Request</h1><p>All fields are required.</p>')
                return

            # Create output file path
            filename = f"{processed_data['id'].strip()}_d2l.csv"
            output_file = os.path.join(OUTPUT_FOLDER, filename)

            try:
                # Generate CSV file
                create_d2l_from_form(processed_data, output_file)

                # Redirect to download the generated CSV file
                self.send_response(303)  # HTTP 303 See Other
                self.send_header('Location', f'/download/{urllib.parse.quote(filename)}')
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
