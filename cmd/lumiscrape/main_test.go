package main

import (
	"testing"
)

func TestVersion(t *testing.T) {
	if version == "" {
		t.Fatal("expected version to be non-empty")
	}
}

func TestPrintUsage(_ *testing.T) {
	printUsage()
}
