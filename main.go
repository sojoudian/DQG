package main

import (
	"encoding/csv"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"
)

const (
	port         = ":8002"
	outputFolder = "outputs"
)

var (
	questions         = []Question{}
	questionIDCounter = 1
	mu                sync.Mutex // To ensure safe concurrent access
)

// Question struct to store question data
type Question struct {
	ID            int
	QuestionText  string
	Points        float64
	Difficulty    string
	Option1       string
	Option2       string
	Option3       string
	Option4       string
	CorrectAnswer int
}

func main() {
	// Create the output folder if it doesn't exist
	err := os.MkdirAll(outputFolder, os.ModePerm)
	if err != nil {
		log.Fatalf("Error creating output folder: %v", err)
	}

	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/submit", submitHandler)
	http.HandleFunc("/download/", downloadHandler)

	fmt.Printf("Serving on port %s\n", port)
	err = http.ListenAndServe(port, nil)
	if err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	tmpl, err := template.ParseFiles("index.html")
	if err != nil {
		http.Error(w, "Error loading index.html", http.StatusInternalServerError)
		return
	}

	// Pass the current question ID to the template
	data := struct {
		QuestionID int
	}{
		QuestionID: questionIDCounter,
	}

	tmpl.Execute(w, data)
}

func submitHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	mu.Lock()
	defer mu.Unlock()

	// Parse form data
	err := r.ParseForm()
	if err != nil {
		http.Error(w, "Error parsing form", http.StatusBadRequest)
		return
	}

	points, err := strconv.ParseFloat(r.FormValue("points"), 64)
	if err != nil || points < 0.5 || points > 3 {
		http.Error(w, "Points must be between 0.5 and 3", http.StatusBadRequest)
		return
	}

	// Create a new question
	question := Question{
		ID:            questionIDCounter,
		QuestionText:  r.FormValue("question_text"),
		Points:        points,
		Difficulty:    r.FormValue("difficulty"),
		Option1:       r.FormValue("option1"),
		Option2:       r.FormValue("option2"),
		Option3:       r.FormValue("option3"),
		Option4:       r.FormValue("option4"),
		CorrectAnswer: parseCorrectAnswer(r.FormValue("correct_answer")),
	}

	// Increment question ID counter and store the question
	questionIDCounter++
	questions = append(questions, question)

	// Handle the action (next or generate)
	action := r.FormValue("action")
	if action == "next" {
		// Continue adding more questions
		http.Redirect(w, r, "/", http.StatusSeeOther)
	} else if action == "generate" {
		// Generate a unique filename with the current date and time
		timestamp := time.Now().Format("2006_Jan_02_03PM_04")
		outputFile := filepath.Join(outputFolder, fmt.Sprintf("%s.csv", timestamp))

		// Generate the CSV and reset questions and questionIDCounter
		err := createCSV(outputFile)
		if err != nil {
			http.Error(w, "Error generating CSV", http.StatusInternalServerError)
			return
		}

		// Clear questions and reset question ID counter
		questions = []Question{}
		questionIDCounter = 1

		// Redirect to download page
		http.Redirect(w, r, "/download/"+filepath.Base(outputFile), http.StatusSeeOther)
	}
}

func downloadHandler(w http.ResponseWriter, r *http.Request) {
	filename := filepath.Base(r.URL.Path)
	filePath := filepath.Join(outputFolder, filename)

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.Error(w, "File not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Header().Set("Content-Type", "text/csv")
	http.ServeFile(w, r, filePath)
}

// createCSV generates the D2L-compatible CSV
func createCSV(outputFile string) error {
	file, err := os.Create(outputFile)
	if err != nil {
		return fmt.Errorf("error creating file: %w", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	for _, question := range questions {
		writer.Write([]string{"NewQuestion", "MC", "", ""})
		writer.Write([]string{"ID", strconv.Itoa(question.ID), "", ""})
		writer.Write([]string{"Title", question.QuestionText, "", ""})
		writer.Write([]string{"QuestionText", question.QuestionText, "", ""})
		writer.Write([]string{"Points", fmt.Sprintf("%.1f", question.Points), "", ""})
		writer.Write([]string{"Difficulty", question.Difficulty, "", ""})

		options := []string{question.Option1, question.Option2, question.Option3, question.Option4}
		for i, option := range options {
			weight := "0"
			if i == question.CorrectAnswer-1 {
				weight = "100"
			}
			writer.Write([]string{"Option", weight, option})
		}

		writer.Write([]string{}) // Add an empty row to separate questions
	}

	fmt.Printf("CSV file created at: %s\n", outputFile)
	return nil
}

func parseCorrectAnswer(answer string) int {
	correctAnswer, _ := strconv.Atoi(answer)
	return correctAnswer
}
