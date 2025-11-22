package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"os"
)

type Config struct {
	Courses      []Course `json:"courses"`
	Rooms        []Room   `json:"rooms"`
	TimeSlots    []string `json:"time_slots"`
	UseAnnealing bool     `json:"use_annealing"`
}

func main() {
	configPath := flag.String("config", "", "Path to JSON configuration file")
	useAnnealing := flag.Bool("anneal", false, "Use simulated annealing fallback")
	flag.Parse()

	if *configPath == "" {
		fmt.Println("Usage: automatic-timetabler -config config.json [-anneal]")
		os.Exit(1)
	}

	config, err := loadConfig(*configPath)
	if err != nil {
		fmt.Printf("failed to read config: %v\n", err)
		os.Exit(1)
	}

	if len(config.TimeSlots) == 0 || len(config.Courses) == 0 || len(config.Rooms) == 0 {
		fmt.Println("config must include time_slots, courses, and rooms")
		os.Exit(1)
	}

	problem := NewProblem(config.Courses, config.Rooms, config.TimeSlots)
	solution, err := problem.Solve(*useAnnealing || config.UseAnnealing)
	if err != nil {
		fmt.Printf("no solution: %v\n", err)
		os.Exit(1)
	}

	output, err := json.MarshalIndent(solution, "", "  ")
	if err != nil {
		fmt.Printf("failed to encode solution: %v\n", err)
		os.Exit(1)
	}
	fmt.Println(string(output))
}

func loadConfig(path string) (Config, error) {
	var cfg Config
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return cfg, err
	}
	if err := json.Unmarshal(data, &cfg); err != nil {
		return cfg, err
	}
	return cfg, nil
}
