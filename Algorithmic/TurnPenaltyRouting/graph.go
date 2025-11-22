package turnpenaltyrouting

import (
	"errors"
	"fmt"
)

// Edge represents a directed edge in the base graph.
type Edge struct {
	ID   string
	From string
	To   string
	Cost float64
}

// Graph stores nodes and adjacency information for routing.
type Graph struct {
	Nodes    map[string]struct{}
	Edges    []Edge
	Outgoing map[string][]Edge
	Incoming map[string][]Edge
}

// NewGraph constructs a Graph from a list of edges.
func NewGraph(edges []Edge) (*Graph, error) {
	g := &Graph{
		Nodes:    map[string]struct{}{},
		Edges:    make([]Edge, len(edges)),
		Outgoing: map[string][]Edge{},
		Incoming: map[string][]Edge{},
	}
	idSeen := make(map[string]struct{})
	for i, e := range edges {
		if e.ID == "" {
			return nil, errors.New("edge id cannot be empty")
		}
		if _, exists := idSeen[e.ID]; exists {
			return nil, fmt.Errorf("duplicate edge id: %s", e.ID)
		}
		idSeen[e.ID] = struct{}{}
		g.Edges[i] = e
		g.Nodes[e.From] = struct{}{}
		g.Nodes[e.To] = struct{}{}
		g.Outgoing[e.From] = append(g.Outgoing[e.From], e)
		g.Incoming[e.To] = append(g.Incoming[e.To], e)
	}
	return g, nil
}

// TurnPenalties holds extra costs for transitions between edges.
type TurnPenalties struct {
	penalties map[string]float64
	forbidden map[string]struct{}
}

// NewTurnPenalties creates an empty TurnPenalties structure.
func NewTurnPenalties() *TurnPenalties {
	return &TurnPenalties{
		penalties: make(map[string]float64),
		forbidden: make(map[string]struct{}),
	}
}

func turnKey(incoming, outgoing string) string {
	return incoming + "->" + outgoing
}

// SetPenalty sets the penalty for transitioning from incoming to outgoing.
func (t *TurnPenalties) SetPenalty(incoming, outgoing string, cost float64) {
	delete(t.forbidden, turnKey(incoming, outgoing))
	t.penalties[turnKey(incoming, outgoing)] = cost
}

// ForbidTurn marks a transition as forbidden.
func (t *TurnPenalties) ForbidTurn(incoming, outgoing string) {
	delete(t.penalties, turnKey(incoming, outgoing))
	t.forbidden[turnKey(incoming, outgoing)] = struct{}{}
}

// IsForbidden returns whether a transition is forbidden.
func (t *TurnPenalties) IsForbidden(incoming, outgoing string) bool {
	_, ok := t.forbidden[turnKey(incoming, outgoing)]
	return ok
}

// Penalty returns the penalty for a transition, or zero when unspecified.
func (t *TurnPenalties) Penalty(incoming, outgoing string) float64 {
	if t == nil {
		return 0
	}
	val, ok := t.penalties[turnKey(incoming, outgoing)]
	if !ok {
		return 0
	}
	return val
}
