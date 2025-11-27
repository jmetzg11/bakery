package main

import (
	"log"
	"net/http"
)

func (app *application) tester(w http.ResponseWriter, r *http.Request) {
	log.Println("tester was hit")
	app.render(w, http.StatusOK, "home.html", nil)
}

func (app *application) home(w http.ResponseWriter, r *http.Request) {
	app.render(w, http.StatusOK, "home.html", nil)
}
