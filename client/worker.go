package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// ProcessResult represents the result of processing a single file
type ProcessResult struct {
	FilePath   string
	OutputPath string
	Duration   time.Duration
	Error      error
}

// SynthesizeRequest matches the server's API request format
type SynthesizeRequest struct {
	Text             string  `json:"text"`
	VoiceDescription *string `json:"voice_description,omitempty"`
}

// processFiles processes all files using a worker pool
func processFiles(files []string, config AppConfig) ([]ProcessResult, error) {
	numWorkers := config.Workers
	if numWorkers > len(files) {
		numWorkers = len(files)
	}

	// Create channels
	jobs := make(chan string, len(files))
	results := make(chan ProcessResult, len(files))

	// Create progress bar
	bar := createProgressBar(len(files), config.Verbose)

	// Start workers
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go worker(i+1, jobs, results, &wg, config, bar)
	}

	// Send jobs
	for _, file := range files {
		jobs <- file
	}
	close(jobs)

	// Wait for all workers to finish
	go func() {
		wg.Wait()
		close(results)
	}()

	// Collect results
	var allResults []ProcessResult
	for result := range results {
		allResults = append(allResults, result)
	}

	// Finish progress bar
	if bar != nil {
		bar.Finish()
	}

	return allResults, nil
}

// worker processes files from the jobs channel
func worker(id int, jobs <-chan string, results chan<- ProcessResult,
	wg *sync.WaitGroup, config AppConfig, bar ProgressBar) {
	defer wg.Done()

	client := &http.Client{
		Timeout: config.Timeout,
	}

	if config.Verbose {
		log.Printf("[Worker %d] Starting with timeout: %v", id, config.Timeout)
	}

	for filePath := range jobs {
		if config.Verbose {
			log.Printf("[Worker %d] Processing: %s", id, filepath.Base(filePath))
		}

		startTime := time.Now()
		result := ProcessResult{
			FilePath: filePath,
		}

		// Process the file
		outputPath, err := processSingleFile(filePath, client, config)
		result.OutputPath = outputPath
		result.Duration = time.Since(startTime)
		result.Error = err

		if err != nil {
			if config.Verbose {
				log.Printf("[Worker %d] Failed: %s - %v", id, filepath.Base(filePath), err)
			}
		} else {
			if config.Verbose {
				log.Printf("[Worker %d] Success: %s -> %s (%.2fs)",
					id, filepath.Base(filePath), filepath.Base(outputPath), result.Duration.Seconds())
			}
		}

		results <- result

		// Update progress bar
		if bar != nil {
			bar.Add(1)
		}
	}

	if config.Verbose {
		log.Printf("[Worker %d] Finished", id)
	}
}

// processSingleFile handles the processing of a single text file
func processSingleFile(filePath string, client *http.Client, config AppConfig) (string, error) {
	// Read file contents
	content, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %w", err)
	}

	// Prepare request
	reqBody := SynthesizeRequest{
		Text: string(content),
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	// Send request to server
	url := fmt.Sprintf("%s/synthesize", config.ServerURL)
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// Check response status
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("server returned status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	// Read response body (MP3 data)
	mp3Data, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	// Generate output path (same directory as input, .mp3 extension)
	outputPath := getOutputPath(filePath)

	// Write MP3 file
	err = os.WriteFile(outputPath, mp3Data, 0644)
	if err != nil {
		return "", fmt.Errorf("failed to write MP3 file: %w", err)
	}

	return outputPath, nil
}
