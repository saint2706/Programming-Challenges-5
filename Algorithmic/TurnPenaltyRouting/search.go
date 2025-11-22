package turnpenaltyrouting

import (
	"container/heap"
	"fmt"
)

// Heuristic estimates the cost from a node to the goal.
type Heuristic func(node string) float64

// RouteResult encapsulates the best path found by the search.
type RouteResult struct {
	Cost  float64
	Path  []Edge
	Steps int
}

type state struct {
	node       string
	incomingID string
}

type queueItem struct {
	state state
	gCost float64
	fCost float64
	index int
}

type priorityQueue []*queueItem

func (pq priorityQueue) Len() int           { return len(pq) }
func (pq priorityQueue) Less(i, j int) bool { return pq[i].fCost < pq[j].fCost }
func (pq priorityQueue) Swap(i, j int) {
	pq[i], pq[j] = pq[j], pq[i]
	pq[i].index = i
	pq[j].index = j
}

func (pq *priorityQueue) Push(x interface{}) {
	item := x.(*queueItem)
	item.index = len(*pq)
	*pq = append(*pq, item)
}

func (pq *priorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	*pq = old[0 : n-1]
	return item
}

// ShortestPath computes the cheapest path considering turn penalties using a Dijkstra/A* hybrid.
func ShortestPath(g *Graph, penalties *TurnPenalties, start, goal string, h Heuristic) (RouteResult, error) {
	if g == nil {
		return RouteResult{}, fmt.Errorf("graph cannot be nil")
	}
	if _, ok := g.Nodes[start]; !ok {
		return RouteResult{}, fmt.Errorf("unknown start node: %s", start)
	}
	if _, ok := g.Nodes[goal]; !ok {
		return RouteResult{}, fmt.Errorf("unknown goal node: %s", goal)
	}
	if h == nil {
		h = func(string) float64 { return 0 }
	}

	dist := map[state]float64{}
	prevState := map[state]state{}
	prevEdge := map[state]Edge{}

	startState := state{node: start, incomingID: ""}
	startItem := &queueItem{state: startState, gCost: 0, fCost: h(start)}
	dist[startState] = 0

	pq := priorityQueue{startItem}
	heap.Init(&pq)
	visited := map[state]bool{}

	for pq.Len() > 0 {
		item := heap.Pop(&pq).(*queueItem)
		if visited[item.state] {
			continue
		}
		visited[item.state] = true

		if item.state.node == goal {
			path := reconstructPath(prevState, prevEdge, item.state)
			return RouteResult{Cost: item.gCost, Path: path, Steps: len(visited)}, nil
		}

		for _, edge := range g.Outgoing[item.state.node] {
			if penalties != nil && item.state.incomingID != "" && penalties.IsForbidden(item.state.incomingID, edge.ID) {
				continue
			}
			turnCost := 0.0
			if item.state.incomingID != "" {
				turnCost = penalties.Penalty(item.state.incomingID, edge.ID)
			}
			nextState := state{node: edge.To, incomingID: edge.ID}
			tentative := item.gCost + edge.Cost + turnCost
			if old, ok := dist[nextState]; ok && tentative >= old {
				continue
			}
			dist[nextState] = tentative
			nextItem := &queueItem{state: nextState, gCost: tentative, fCost: tentative + h(edge.To)}
			prevState[nextState] = item.state
			prevEdge[nextState] = edge
			heap.Push(&pq, nextItem)
		}
	}
	return RouteResult{}, fmt.Errorf("no path from %s to %s", start, goal)
}

func reconstructPath(prevState map[state]state, prevEdge map[state]Edge, end state) []Edge {
	var edges []Edge
	cur := end
	for {
		pState, ok := prevState[cur]
		if !ok {
			break
		}
		edge, exists := prevEdge[cur]
		if !exists {
			break
		}
		edges = append(edges, edge)
		cur = pState
	}
	// reverse
	for i, j := 0, len(edges)-1; i < j; i, j = i+1, j-1 {
		edges[i], edges[j] = edges[j], edges[i]
	}
	return edges
}
