package store

import (
	"errors"
	"sort"
	"time"
)

// IntervalTree indexes events by their start and end times to support fast overlap queries.
type IntervalTree struct {
	root *node
}

type node struct {
	center int64
	events []Event
	left   *node
	right  *node
}

// NewIntervalTree constructs an empty interval tree.
func NewIntervalTree() *IntervalTree {
	return &IntervalTree{}
}

// Insert adds an event to the tree. The event is normalized before insertion.
func (t *IntervalTree) Insert(e Event) {
	e.Normalize()
	midpoint := midpoint(e.Start, e.End)
	t.root = insertNode(t.root, midpoint, e)
}

// Delete removes an event by ID and interval bounds. It returns an error when the event cannot be found.
func (t *IntervalTree) Delete(id string, start, end time.Time) error {
	start, end = normalizeBounds(start, end)
	var removed bool
	t.root, removed = deleteNode(t.root, id, start, end)
	if !removed {
		return errors.New("event not found")
	}
	return nil
}

// QueryOverlap returns events that overlap the given interval.
func (t *IntervalTree) QueryOverlap(start, end time.Time) []Event {
	start, end = normalizeBounds(start, end)
	var results []Event
	queryOverlap(t.root, start, end, &results)
	return results
}

// QueryContaining returns events that fully contain the supplied interval.
func (t *IntervalTree) QueryContaining(start, end time.Time) []Event {
	start, end = normalizeBounds(start, end)
	var results []Event
	queryContains(t.root, start, end, &results)
	return results
}

func insertNode(n *node, center int64, e Event) *node {
	if n == nil {
		return &node{center: center, events: []Event{e}}
	}

	if e.End.UnixNano() < n.center {
		n.left = insertNode(n.left, center, e)
	} else if e.Start.UnixNano() > n.center {
		n.right = insertNode(n.right, center, e)
	} else {
		n.events = append(n.events, e)
		// Keep events sorted by start time for stable iteration and deterministic tests.
		sort.SliceStable(n.events, func(i, j int) bool {
			if n.events[i].Start.Equal(n.events[j].Start) {
				return n.events[i].ID < n.events[j].ID
			}
			return n.events[i].Start.Before(n.events[j].Start)
		})
	}
	return n
}

func deleteNode(n *node, id string, start, end time.Time) (*node, bool) {
	if n == nil {
		return nil, false
	}

	startNs, endNs := start.UnixNano(), end.UnixNano()
	if endNs < n.center {
		updated, removed := deleteNode(n.left, id, start, end)
		n.left = updated
		return n, removed
	}
	if startNs > n.center {
		updated, removed := deleteNode(n.right, id, start, end)
		n.right = updated
		return n, removed
	}

	// Remove from current node if present.
	for i, ev := range n.events {
		if ev.ID == id && ev.Start.Equal(start) && ev.End.Equal(end) {
			n.events = append(n.events[:i], n.events[i+1:]...)
			return n, true
		}
	}

	// If not found in current node, search children where the interval could also live.
	if startNs <= n.center {
		if n.left != nil {
			if updated, removed := deleteNode(n.left, id, start, end); removed {
				n.left = updated
				return n, true
			}
		}
	}
	if endNs >= n.center {
		if n.right != nil {
			if updated, removed := deleteNode(n.right, id, start, end); removed {
				n.right = updated
				return n, true
			}
		}
	}

	return n, false
}

func queryOverlap(n *node, start, end time.Time, results *[]Event) {
	if n == nil {
		return
	}

	startNs, endNs := start.UnixNano(), end.UnixNano()
	if startNs <= n.center {
		queryOverlap(n.left, start, end, results)
	}

	for _, ev := range n.events {
		if intervalsOverlap(start, end, ev.Start, ev.End) {
			*results = append(*results, ev)
		}
	}

	if endNs >= n.center {
		queryOverlap(n.right, start, end, results)
	}
}

func queryContains(n *node, start, end time.Time, results *[]Event) {
	if n == nil {
		return
	}

	startNs, endNs := start.UnixNano(), end.UnixNano()
	if startNs <= n.center {
		queryContains(n.left, start, end, results)
	}

	for _, ev := range n.events {
		if containsInterval(ev.Start, ev.End, start, end) {
			*results = append(*results, ev)
		}
	}

	if endNs >= n.center {
		queryContains(n.right, start, end, results)
	}
}

func intervalsOverlap(aStart, aEnd, bStart, bEnd time.Time) bool {
	return !aEnd.Before(bStart) && !bEnd.Before(aStart)
}

func containsInterval(outerStart, outerEnd, innerStart, innerEnd time.Time) bool {
	return (outerStart.Before(innerStart) || outerStart.Equal(innerStart)) && (outerEnd.After(innerEnd) || outerEnd.Equal(innerEnd))
}

func midpoint(start, end time.Time) int64 {
	return (start.UnixNano() + end.UnixNano()) / 2
}

func normalizeBounds(start, end time.Time) (time.Time, time.Time) {
	if start.After(end) {
		return end, start
	}
	return start, end
}
