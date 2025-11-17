package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
)

// ClientConfig holds the client configuration
type ClientConfig struct {
	ServerURL string `json:"server_url"`
	Timeout   int    `json:"timeout"`   // in seconds
	Workers   int    `json:"workers"`
}

// DefaultConfig returns the default configuration
func DefaultConfig() ClientConfig {
	return ClientConfig{
		ServerURL: "http://localhost:8000",
		Timeout:   600, // 10 minutes
		Workers:   1,
	}
}

// LoadConfig loads configuration from config.json in the executable directory
func LoadConfig() ClientConfig {
	// Get executable directory
	exePath, err := os.Executable()
	if err != nil {
		log.Printf("Warning: Could not get executable path: %v", err)
		log.Println("Using default configuration")
		return DefaultConfig()
	}

	exeDir := filepath.Dir(exePath)
	configPath := filepath.Join(exeDir, "config.json")
	examplePath := filepath.Join(exeDir, "config.example.json")

	// Check if config.json exists
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		log.Printf("Config file not found: %s", configPath)

		// Create config.example.json if it doesn't exist
		if _, err := os.Stat(examplePath); os.IsNotExist(err) {
			log.Println("Creating config.example.json...")
			if err := createExampleConfig(examplePath); err != nil {
				log.Printf("Warning: Failed to create example config: %v", err)
			} else {
				log.Printf("Created example config: %s", examplePath)
			}
		}

		log.Println("Using default configuration")
		return DefaultConfig()
	}

	// Load config.json
	log.Printf("Loading configuration from: %s", configPath)
	config, err := loadConfigFile(configPath)
	if err != nil {
		log.Printf("Warning: Failed to load config: %v", err)
		log.Println("Using default configuration")
		return DefaultConfig()
	}

	// Validate configuration
	if err := validateConfig(&config); err != nil {
		log.Printf("Warning: Invalid configuration: %v", err)
		log.Println("Using default configuration")
		return DefaultConfig()
	}

	log.Println("Configuration loaded successfully")
	return config
}

// loadConfigFile reads and parses a config file
func loadConfigFile(path string) (ClientConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return ClientConfig{}, fmt.Errorf("failed to read file: %w", err)
	}

	var config ClientConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return ClientConfig{}, fmt.Errorf("failed to parse JSON: %w", err)
	}

	return config, nil
}

// validateConfig validates configuration values
func validateConfig(config *ClientConfig) error {
	// Validate server URL
	if config.ServerURL == "" {
		return fmt.Errorf("server_url cannot be empty")
	}

	// Validate timeout
	if config.Timeout <= 0 {
		log.Printf("Warning: Invalid timeout %d, using default (600s)", config.Timeout)
		config.Timeout = 600
	}

	// Validate workers
	if config.Workers < 1 {
		log.Printf("Warning: Invalid workers %d, using default (1)", config.Workers)
		config.Workers = 1
	} else if config.Workers > 10 {
		log.Printf("Warning: Workers count %d seems high, consider reducing", config.Workers)
	}

	return nil
}

// createExampleConfig creates a config.example.json file
func createExampleConfig(path string) error {
	example := map[string]interface{}{
		"_comment": "MayaSpeechify Client Configuration",
		"_usage":   "Copy this file to config.json and adjust values as needed",
		"server_url": "http://localhost:8000",
		"_server_url_note": "Server endpoint URL (can be overridden with -server flag)",
		"timeout": 600,
		"_timeout_note": "HTTP request timeout in seconds (can be overridden with -timeout flag)",
		"workers": 1,
		"_workers_note": "Default number of parallel workers (can be overridden with -workers flag)",
		"_examples": []string{
			"Local server: http://localhost:8000",
			"Remote server: http://192.168.1.100:8000",
			"RunPod proxy: https://xxxxx-7777.proxy.runpod.net",
		},
	}

	data, err := json.MarshalIndent(example, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal example config: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}

// SaveConfig saves configuration to config.json
func SaveConfig(config ClientConfig, path string) error {
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}

	return nil
}
