package main

import (
	"fmt"
	"net/http"
)

type indexHandler struct {
	content string
}

func (ih *indexHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, ih.content)
}

func main() {
	http.Handle("/", &indexHandler{content: "ok"})
	http.ListenAndServe(":8080", nil)
}
