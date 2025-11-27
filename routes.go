package main

import (
	"io/fs"
	"net/http"
)

func (app *application) routes(prod bool) http.Handler {
	mux := http.NewServeMux()

	staticFS, _ := fs.Sub(Files, "ui/static")
	mux.Handle("GET /static/", http.StripPrefix("/static", http.FileServer(http.FS(staticFS))))

	if !prod {
		mux.HandleFunc("GET /tester", app.tester)
	}

	mux.HandleFunc("GET /{$}", app.home)
	mux.HandleFunc("POST /make_report", app.makeReport)
	mux.HandleFunc("GET /reports", app.showReports)
	return rateLimit(mux)

}
