package main

import (
	"github.com/k0kubun/go-ansi"
	"github.com/schollz/progressbar/v3"
)

// ProgressBar interface for abstraction
type ProgressBar interface {
	Add(num int) error
	Finish() error
}

// createProgressBar creates a new progress bar with the preferred green style
func createProgressBar(total int, verbose bool) ProgressBar {
	if verbose {
		// In verbose mode, return a no-op progress bar to avoid interference with logs
		return &noOpProgressBar{}
	}

	bar := progressbar.NewOptions(total,
		progressbar.OptionSetWriter(ansi.NewAnsiStdout()),
		progressbar.OptionEnableColorCodes(true),
		progressbar.OptionSetWidth(40),
		progressbar.OptionShowCount(),
		progressbar.OptionSetDescription("[cyan]Processing files[reset]"),
		progressbar.OptionSetTheme(progressbar.Theme{
			Saucer:        "[green]█[reset]",
			SaucerHead:    "[green]█[reset]",
			SaucerPadding: "░",
			BarStart:      "│",
			BarEnd:        "│",
		}),
		progressbar.OptionOnCompletion(func() {
			// Print newline after completion
			ansi.NewAnsiStdout().Write([]byte("\n"))
		}),
	)

	return bar
}

// noOpProgressBar is a no-op implementation for verbose mode
type noOpProgressBar struct{}

func (n *noOpProgressBar) Add(num int) error {
	return nil
}

func (n *noOpProgressBar) Finish() error {
	return nil
}
