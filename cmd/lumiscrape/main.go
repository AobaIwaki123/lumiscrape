// Package main is the entry point for the lumiscrape CLI and server.
package main

import (
	"flag"
	"fmt"
	"os"
)

var version = "1.0.0"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(0)
	}

	command := os.Args[1]
	switch command {
	case "version", "--version", "-v":
		fmt.Printf("lumiscrape %s\n", version)
	case "serve":
		serveCmd := flag.NewFlagSet("serve", flag.ExitOnError)
		port := serveCmd.String("port", "8080", "HTTP server port")
		host := serveCmd.String("host", "0.0.0.0", "HTTP server host")
		_ = serveCmd.Parse(os.Args[2:])
		fmt.Printf("Starting lumiscrape server on %s:%s (scaffolding stage)...\n", *host, *port)
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n\n", command)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Printf(`lumiscrape - Thin, robust, and LLM-assisted web scraping platform (%s)

Usage:
  lumiscrape <command> [options]

Available Commands:
  serve       Start the HTTP management web server and scheduler
  version     Display version information
  help        Show help for lumiscrape
`, version)
}
