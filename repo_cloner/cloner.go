package main

import (
	"bufio"
	"fmt"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
)

const (
	repoListFile = "repos.txt"
	cloneDir     = "cloned_repos"
	maxWorkers   = 20
)

func normalizeURL(raw string) string {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return ""
	}
	if strings.HasPrefix(raw, "https://") || strings.HasPrefix(raw, "git@") {
		return raw
	}
	if strings.HasPrefix(raw, "github.com") {
		return "https://" + raw
	}
	if !strings.Contains(raw, "/") {
		return ""
	}
	return "https://github.com/" + raw
}

func extractOrgRepo(repoURL string) (string, string) {
	u, err := url.Parse(repoURL)
	if err != nil {
		return "", ""
	}
	parts := strings.Split(strings.Trim(u.Path, "/"), "/")
	if len(parts) < 2 {
		return "", ""
	}
	org := parts[0]
	repo := strings.TrimSuffix(parts[1], ".git")
	return org, repo
}

func cloneRepo(url string, wg *sync.WaitGroup, sem chan struct{}) {
	defer wg.Done()
	sem <- struct{}{}
	defer func() { <-sem }()

	org, repo := extractOrgRepo(url)
	if org == "" || repo == "" {
		fmt.Printf("[ERROR] Couldn't parse org/repo from %s\n", url)
		return
	}

	targetPath := filepath.Join(cloneDir, org, repo)

	if _, err := os.Stat(targetPath); err == nil {
		fmt.Printf("[SKIPPED] %s/%s already exists.\n", org, repo)
		return
	}

	if err := os.MkdirAll(filepath.Dir(targetPath), 0755); err != nil {
		fmt.Printf("[ERROR] Couldn't create directory for %s: %v\n", targetPath, err)
		return
	}

	cmd := exec.Command("git", "clone", url, targetPath)
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("[ERROR] Failed to clone %s: %s\n", url, string(out))
		return
	}
	fmt.Printf("[CLONED] %s\n", url)
}

func readURLs(file string) ([]string, error) {
	f, err := os.Open(file)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	urlMap := make(map[string]struct{})
	scanner := bufio.NewScanner(f)

	for scanner.Scan() {
		line := normalizeURL(scanner.Text())
		if line != "" {
			urlMap[line] = struct{}{}
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	urls := make([]string, 0, len(urlMap))
	for url := range urlMap {
		urls = append(urls, url)
	}
	return urls, nil
}

func main() {
	if err := os.MkdirAll(cloneDir, 0755); err != nil {
		fmt.Println("Failed to create clone directory:", err)
		return
	}

	urls, err := readURLs(repoListFile)
	if err != nil {
		fmt.Println("Error reading repo list:", err)
		return
	}

	var wg sync.WaitGroup
	sem := make(chan struct{}, maxWorkers)

	for _, url := range urls {
		wg.Add(1)
		go cloneRepo(url, &wg, sem)
	}

	wg.Wait()
}
