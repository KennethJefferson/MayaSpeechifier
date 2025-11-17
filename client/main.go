package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
)

// Config holds the application configuration
type Config struct {
	Workers   int
	ScanPath  string
	Recursive bool
	Verbose   bool
	ServerURL string
}

func main() {
	// Define command-line flags
	var config Config

	flag.IntVar(&config.Workers, "workers", 1, "Number of parallel workers (default: 1)")
	flag.StringVar(&config.ScanPath, "scan", "", "Root directory to scan for .txt files (required)")
	flag.BoolVar(&config.Recursive, "recursive", false, "Search subdirectories recursively")
	flag.BoolVar(&config.Verbose, "verbose", false, "Enable detailed logging")
	flag.StringVar(&config.ServerURL, "server", "http://localhost:8000", "Maya1 API server URL")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "MayaSpeechify - Text-to-Speech Client\n\n")
		fmt.Fprintf(os.Stderr, "Usage:\n")
		fmt.Fprintf(os.Stderr, "  MayaSpeechify -scan \"<path>\" [options]\n\n")
		fmt.Fprintf(os.Stderr, "Options:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nExamples:\n")
		fmt.Fprintf(os.Stderr, "  MayaSpeechify -scan \"K:\\Downloads\\books\"\n")
		fmt.Fprintf(os.Stderr, "  MayaSpeechify -workers 2 -scan \"K:\\Downloads\\books\" -recursive -verbose\n")
	}

	flag.Parse()

	// Validate required flags
	if config.ScanPath == "" {
		fmt.Fprintf(os.Stderr, "Error: -scan flag is required\n\n")
		flag.Usage()
		os.Exit(1)
	}

	// Validate scan path exists
	if _, err := os.Stat(config.ScanPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: scan path does not exist: %s\n", config.ScanPath)
		os.Exit(1)
	}

	// Validate workers count
	if config.Workers < 1 {
		fmt.Fprintf(os.Stderr, "Error: workers must be at least 1\n")
		os.Exit(1)
	}

	// Initialize logger
	if !config.Verbose {
		log.SetOutput(os.Stderr)
		log.SetFlags(0)
	} else {
		log.SetOutput(os.Stderr)
		log.SetFlags(log.Ldate | log.Ltime | log.Lshortfile)
	}

	// Print configuration
	if config.Verbose {
		log.Printf("Configuration:")
		log.Printf("  Workers: %d", config.Workers)
		log.Printf("  Scan Path: %s", config.ScanPath)
		log.Printf("  Recursive: %v", config.Recursive)
		log.Printf("  Server URL: %s", config.ServerURL)
		log.Println()
	}

	// Run the application
	if err := run(config); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func run(config Config) error {
	// Step 1: Discover text files
	log.Println("Scanning for .txt files...")
	files, err := discoverFiles(config.ScanPath, config.Recursive)
	if err != nil {
		return fmt.Errorf("failed to scan files: %w", err)
	}

	if len(files) == 0 {
		log.Println("No .txt files found")
		return nil
	}

	if config.Verbose {
		log.Printf("Found %d text file(s)\n", len(files))
	} else {
		fmt.Printf("Found %d text file(s)\n", len(files))
	}

	// Step 2: Process files with worker pool
	results, err := processFiles(files, config)
	if err != nil {
		return fmt.Errorf("failed to process files: %w", err)
	}

	// Step 3: Print summary
	printSummary(results, config.Verbose)

	return nil
}

// printSummary prints processing results summary
func printSummary(results []ProcessResult, verbose bool) {
	successful := 0
	failed := 0

	for _, result := range results {
		if result.Error == nil {
			successful++
		} else {
			failed++
		}
	}

	fmt.Println()
	fmt.Println("=== Summary ===")
	fmt.Printf("Total files: %d\n", len(results))
	fmt.Printf("Successful: %d\n", successful)
	fmt.Printf("Failed: %d\n", failed)

	if failed > 0 && verbose {
		fmt.Println("\nFailed files:")
		for _, result := range results {
			if result.Error != nil {
				fmt.Printf("  - %s: %v\n", filepath.Base(result.FilePath), result.Error)
			}
		}
	}
}

// getOutputPath generates the output MP3 path for a given input file
func getOutputPath(inputPath string) string {
	ext := filepath.Ext(inputPath)
	return strings.TrimSuffix(inputPath, ext) + ".mp3"
}
