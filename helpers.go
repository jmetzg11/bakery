package main

import (
	"bytes"
	"context"
	"embed"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"text/template"

	"golang.org/x/oauth2/google"
	"golang.org/x/time/rate"
	"google.golang.org/api/option"
	"google.golang.org/api/sheets/v4"
)

//go:embed ui/html ui/static
var Files embed.FS

func newTemplateCache() map[string]*template.Template {
	cache := map[string]*template.Template{}

	funcMap := template.FuncMap{
		"formatMoney": func(f float64) string {
			// Format the integer part with commas
			intPart := int(f)
			cents := int((f - float64(intPart)) * 100)

			// Convert integer to string with commas
			intStr := fmt.Sprintf("%d", intPart)
			var result []byte
			numDigits := len(intStr)

			for i, digit := range intStr {
				if i > 0 && (numDigits-i)%3 == 0 {
					result = append(result, ',')
				}
				result = append(result, byte(digit))
			}

			// Add cents
			return fmt.Sprintf("€%s.%02d", string(result), cents)
		},
	}

	pages, err := fs.Glob(Files, "ui/html/pages/*.html")
	if err != nil {
		log.Fatalf("failed to create template cache: %v", err)
	}

	for _, page := range pages {
		name := filepath.Base(page)

		patterns := []string{
			"ui/html/base.html",
			page,
		}

		ts, err := template.New(name).Funcs(funcMap).ParseFS(Files, patterns...)
		if err != nil {
			log.Fatalf("failed to create template")
		}
		cache[name] = ts
	}
	return cache
}

func mustSheetsService() *sheets.Service {
	ctx := context.Background()

	credJSON := os.Getenv("GOOGLE_CREDENTIALS_JSON")
	if credJSON == "" {
		log.Fatal("GOOGLE_CREDENTIALS_JSON environment variable not set")
	}

	creds, err := google.CredentialsFromJSON(
		ctx,
		[]byte(credJSON),
		sheets.SpreadsheetsScope, // cleaner than the full URL
	)
	if err != nil {
		log.Fatalf("Unable to parse Google credentials: %v", err)
	}

	svc, err := sheets.NewService(ctx, option.WithCredentials(creds))
	if err != nil {
		log.Fatalf("Unable to create Google Sheets service: %v", err)
	}

	return svc
}

func mustGetenv(key string) string {
	val := os.Getenv(key)
	if val == "" {
		log.Fatalf("required environment variable %s is not set", key)
	}
	return val
}

func (app *application) render(w http.ResponseWriter, status int, page string, data any) {
	ts, ok := app.templateCache[page]
	if !ok {
		err := fmt.Errorf("the template %s does not exist", page)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	buf := new(bytes.Buffer)
	err := ts.ExecuteTemplate(buf, "base", data)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(status)
	buf.WriteTo(w)
}

func isStaticAsset(path string) bool {
	staticPrefixes := []string{"/static/"}
	for _, prefix := range staticPrefixes {
		if len(path) >= len(prefix) && path[:len(prefix)] == prefix {
			return true
		}
	}
	return false
}

var limiter = rate.NewLimiter(4, 10)

func rateLimit(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip rate limiting for static assets
		if isStaticAsset(r.URL.Path) {
			next.ServeHTTP(w, r)
			return
		}

		if !limiter.Allow() {
			http.Error(w, "Too many requests", http.StatusTooManyRequests)
			return
		}
		next.ServeHTTP(w, r)
	})
}
