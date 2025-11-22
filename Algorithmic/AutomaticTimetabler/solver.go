package main

import (
	"errors"
	"math"
	"math/rand"
	"time"
)

type Course struct {
	Name      string   `json:"name"`
	Size      int      `json:"size"`
	Conflicts []string `json:"conflicts"`
}

type Room struct {
	Name     string `json:"name"`
	Capacity int    `json:"capacity"`
}

type Placement struct {
	Room string `json:"room"`
	Time string `json:"time"`
}

type Problem struct {
	Courses       map[string]Course
	Rooms         []Room
	TimeSlots     []string
	conflictGraph map[string]map[string]bool
	baseDomains   map[string][]Placement
	roomCapacity  map[string]int
}

func NewProblem(courses []Course, rooms []Room, timeSlots []string) *Problem {
	conflictGraph := make(map[string]map[string]bool)
	courseMap := make(map[string]Course)
	roomCapacity := make(map[string]int)

	for _, room := range rooms {
		roomCapacity[room.Name] = room.Capacity
	}

	for _, course := range courses {
		courseMap[course.Name] = course
		if _, ok := conflictGraph[course.Name]; !ok {
			conflictGraph[course.Name] = make(map[string]bool)
		}
		for _, c := range course.Conflicts {
			if _, ok := conflictGraph[c]; !ok {
				conflictGraph[c] = make(map[string]bool)
			}
			conflictGraph[course.Name][c] = true
			conflictGraph[c][course.Name] = true
		}
	}

	baseDomains := make(map[string][]Placement)
	for _, course := range courses {
		baseDomains[course.Name] = buildDomain(course, rooms, timeSlots)
	}

	return &Problem{
		Courses:       courseMap,
		Rooms:         rooms,
		TimeSlots:     timeSlots,
		conflictGraph: conflictGraph,
		baseDomains:   baseDomains,
		roomCapacity:  roomCapacity,
	}
}

func buildDomain(course Course, rooms []Room, timeSlots []string) []Placement {
	var domain []Placement
	for _, room := range rooms {
		if room.Capacity < course.Size {
			continue
		}
		for _, t := range timeSlots {
			domain = append(domain, Placement{Room: room.Name, Time: t})
		}
	}
	return domain
}

func (p *Problem) Solve(useAnnealing bool) (map[string]Placement, error) {
	assignment := make(map[string]Placement)
	domains := copyDomains(p.baseDomains)

	result, ok := p.backtrack(assignment, domains)
	if ok {
		return result, nil
	}

	if useAnnealing {
		if annealed, ok := p.simulatedAnnealing(5000, 1.0, 0.995); ok {
			if err := p.ValidateAssignment(annealed); err == nil {
				return annealed, nil
			}
		}
	}

	return nil, errors.New("no feasible timetable found")
}

func (p *Problem) backtrack(assignment map[string]Placement, domains map[string][]Placement) (map[string]Placement, bool) {
	if len(assignment) == len(p.Courses) {
		result := make(map[string]Placement, len(assignment))
		for k, v := range assignment {
			result[k] = v
		}
		return result, true
	}

	course := p.selectUnassigned(domains, assignment)
	if course == "" {
		return nil, false
	}

	for _, placement := range domains[course] {
		if !p.isConsistent(course, placement, assignment) {
			continue
		}
		assignment[course] = placement
		pruned := p.forwardCheck(course, placement, assignment, domains)
		if pruned != nil {
			if result, ok := p.backtrack(assignment, pruned); ok {
				return result, true
			}
		}
		delete(assignment, course)
	}

	return nil, false
}

func (p *Problem) selectUnassigned(domains map[string][]Placement, assignment map[string]Placement) string {
	var chosen string
	minDomain := math.MaxInt
	for course := range p.Courses {
		if _, assigned := assignment[course]; assigned {
			continue
		}
		size := len(domains[course])
		if size < minDomain {
			minDomain = size
			chosen = course
		}
	}
	return chosen
}

func (p *Problem) isConsistent(course string, placement Placement, assignment map[string]Placement) bool {
	if capLimit, ok := p.roomCapacity[placement.Room]; !ok || capLimit < p.Courses[course].Size {
		return false
	}

	for otherCourse, otherPlacement := range assignment {
		if placement.Time == otherPlacement.Time {
			if p.conflictGraph[course][otherCourse] {
				return false
			}
			if placement.Room == otherPlacement.Room {
				return false
			}
		}
		if placement.Room == otherPlacement.Room && placement.Time == otherPlacement.Time {
			return false
		}
	}
	return true
}

func (p *Problem) forwardCheck(course string, placement Placement, assignment map[string]Placement, domains map[string][]Placement) map[string][]Placement {
	newDomains := copyDomains(domains)
	newDomains[course] = []Placement{placement}

	for other, vals := range domains {
		if other == course {
			continue
		}
		if _, assigned := assignment[other]; assigned {
			continue
		}
		filtered := make([]Placement, 0, len(vals))
		for _, v := range vals {
			if v.Room == placement.Room && v.Time == placement.Time {
				continue
			}
			if p.conflictGraph[course][other] && v.Time == placement.Time {
				continue
			}
			if capLimit := p.roomCapacity[v.Room]; capLimit < p.Courses[other].Size {
				continue
			}
			filtered = append(filtered, v)
		}
		if len(filtered) == 0 {
			return nil
		}
		newDomains[other] = filtered
	}
	return newDomains
}

func copyDomains(domains map[string][]Placement) map[string][]Placement {
	dup := make(map[string][]Placement, len(domains))
	for k, v := range domains {
		nv := make([]Placement, len(v))
		copy(nv, v)
		dup[k] = nv
	}
	return dup
}

func (p *Problem) simulatedAnnealing(maxIterations int, temperature float64, cooling float64) (map[string]Placement, bool) {
	rand.Seed(time.Now().UnixNano())
	assignment := p.randomAssignment()
	if assignment == nil {
		return nil, false
	}
	currentCost := p.cost(assignment)

	for i := 0; i < maxIterations && currentCost > 0; i++ {
		candidate := copyAssignment(assignment)
		courseNames := p.courseNames()
		course := courseNames[rand.Intn(len(courseNames))]
		domain := p.baseDomains[course]
		candidate[course] = domain[rand.Intn(len(domain))]

		nextCost := p.cost(candidate)
		if acceptMove(currentCost, nextCost, temperature) {
			assignment = candidate
			currentCost = nextCost
		}
		temperature *= cooling
		if temperature < 1e-5 {
			temperature = 1e-5
		}
	}
	return assignment, currentCost == 0
}

func (p *Problem) randomAssignment() map[string]Placement {
	assignment := make(map[string]Placement, len(p.Courses))
	for course := range p.Courses {
		domain := p.baseDomains[course]
		if len(domain) == 0 {
			return nil
		}
		assignment[course] = domain[rand.Intn(len(domain))]
	}
	return assignment
}

func (p *Problem) courseNames() []string {
	names := make([]string, 0, len(p.Courses))
	for name := range p.Courses {
		names = append(names, name)
	}
	return names
}

func (p *Problem) cost(assignment map[string]Placement) int {
	if assignment == nil {
		return math.MaxInt
	}
	cost := 0
	roomUsage := make(map[string]map[string]int)

	for course, place := range assignment {
		if p.roomCapacity[place.Room] < p.Courses[course].Size {
			cost++
		}
		if _, ok := roomUsage[place.Time]; !ok {
			roomUsage[place.Time] = make(map[string]int)
		}
		roomUsage[place.Time][place.Room]++
	}

	for t, rooms := range roomUsage {
		for _, count := range rooms {
			if count > 1 {
				cost += count - 1
			}
		}
		for c1, p1 := range assignment {
			if p1.Time != t {
				continue
			}
			for c2, p2 := range assignment {
				if c1 >= c2 {
					continue
				}
				if p2.Time != t {
					continue
				}
				if p1.Room == p2.Room {
					cost++
				}
				if p.conflictGraph[c1][c2] {
					cost++
				}
			}
		}
	}
	return cost
}

func acceptMove(current, next int, temperature float64) bool {
	if next <= current {
		return true
	}
	delta := float64(next - current)
	probability := math.Exp(-delta / temperature)
	return rand.Float64() < probability
}

func copyAssignment(assign map[string]Placement) map[string]Placement {
	dup := make(map[string]Placement, len(assign))
	for k, v := range assign {
		dup[k] = v
	}
	return dup
}

func (p *Problem) ValidateAssignment(assign map[string]Placement) error {
	if len(assign) != len(p.Courses) {
		return errors.New("assignment does not cover all courses")
	}

	roomTimeUsage := make(map[string]map[string]bool)
	for course, placement := range assign {
		courseInfo, ok := p.Courses[course]
		if !ok {
			return errors.New("unknown course in assignment")
		}
		if capLimit, ok := p.roomCapacity[placement.Room]; !ok || capLimit < courseInfo.Size {
			return errors.New("room capacity violated")
		}
		if _, ok := roomTimeUsage[placement.Time]; !ok {
			roomTimeUsage[placement.Time] = make(map[string]bool)
		}
		if roomTimeUsage[placement.Time][placement.Room] {
			return errors.New("room double booked")
		}
		roomTimeUsage[placement.Time][placement.Room] = true

		for otherCourse, otherPlacement := range assign {
			if course == otherCourse {
				continue
			}
			if placement.Time == otherPlacement.Time {
				if p.conflictGraph[course][otherCourse] {
					return errors.New("conflicting courses share time")
				}
				if placement.Room == otherPlacement.Room {
					return errors.New("room collision")
				}
			}
		}
	}
	return nil
}
