package store

import "time"

// Event represents a temporal interval with an identifier and optional metadata.
type Event struct {
	ID    string            `json:"id" csv:"id"`
	Start time.Time         `json:"start" csv:"start"`
	End   time.Time         `json:"end" csv:"end"`
	Data  map[string]string `json:"data,omitempty" csv:"-"`
}

// Duration returns the length of the event's interval.
func (e Event) Duration() time.Duration {
	return e.End.Sub(e.Start)
}

// Normalize ensures the start time is not after the end time.
// It swaps the values when needed so the interval remains valid.
func (e *Event) Normalize() {
	if e.Start.After(e.End) {
		e.Start, e.End = e.End, e.Start
	}
}
