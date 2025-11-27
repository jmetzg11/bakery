package main

import (
	"flag"
	"log"
	"net/http"
	"text/template"
	"time"

	"github.com/joho/godotenv"
	"google.golang.org/api/sheets/v4"
)

type application struct {
	templateCache  map[string]*template.Template
	sheetsServices *sheets.Service
	sheetId        string
}

func main() {
	prod := flag.Bool("prod", false, "User Production")
	flag.Parse()

	if !*prod {
		_ = godotenv.Load()
	}

	app := &application{
		templateCache:  newTemplateCache(),
		sheetsServices: mustSheetsService(),
		sheetId:        mustGetenv("SPREADSHEET_ID"),
	}

	srv := &http.Server{
		Addr:         ":3000",
		Handler:      app.routes(*prod),
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	log.Print("Server starting on :3000")
	log.Fatal(srv.ListenAndServe())
}
