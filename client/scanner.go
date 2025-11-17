package main

import (
	"log"
	"os"
	"path/filepath"
	"strings"
)

// discoverFiles scans the given directory for .txt files
func discoverFiles(rootPath string, recursive bool) ([]string, error) {
	var files []string

	if recursive {
		// Recursive scan using filepath.Walk
		err := filepath.Walk(rootPath, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				log.Printf("Warning: error accessing path %s: %v", path, err)
				return nil // Continue walking despite errors
			}

			// Skip directories
			if info.IsDir() {
				return nil
			}

			// Check for .txt extension (case-insensitive)
			if strings.ToLower(filepath.Ext(path)) == ".txt" {
				files = append(files, path)
			}

			return nil
		})

		if err != nil {
			return nil, err
		}
	} else {
		// Non-recursive scan - only root directory
		entries, err := os.ReadDir(rootPath)
		if err != nil {
			return nil, err
		}

		for _, entry := range entries {
			// Skip directories
			if entry.IsDir() {
				continue
			}

			// Check for .txt extension (case-insensitive)
			if strings.ToLower(filepath.Ext(entry.Name())) == ".txt" {
				fullPath := filepath.Join(rootPath, entry.Name())
				files = append(files, fullPath)
			}
		}
	}

	return files, nil
}

// fileExists checks if a file exists at the given path
func fileExists(path string) bool {
	info, err := os.Stat(path)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}
