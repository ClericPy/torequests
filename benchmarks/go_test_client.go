package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

type result struct {
	string
	bool
}

const URL = "http://127.0.0.1:8080/"

func fetch(url string, ch chan string) string {
	r, _ := http.Get(url)
	defer r.Body.Close()
	body, _ := ioutil.ReadAll(r.Body)
	return string(body)
}

func main() {
	oks := 0
	resultChannel := make(chan string)
	start := time.Now()
	for index := 0; index < 2000; index++ {
		go func(u string) {
			resultChannel <- fetch(u, resultChannel)
		}(URL)
	}
	for i := 0; i < 2000; i++ {
		result := <-resultChannel
		if result == "ok" {
			oks++
		}
	}
	t := time.Since(start).Seconds()
	qps := 2000.0 / t
	fmt.Printf("%d / 2000, %.2f %%, cost %.2f seconds, %.2f qps.", oks, float64(oks)*100/float64(2000.0), t, qps)
}
