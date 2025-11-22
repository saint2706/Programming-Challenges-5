package binpacking

import "errors"

// Rect represents a rectangle to pack.
type Rect struct {
	Width  float64
	Height float64
}

// Bin2D represents a bin for rectangles using shelf packing.
type Bin2D struct {
	Width   float64
	Height  float64
	Shelves []shelf
}

type shelf struct {
	Height    float64
	Remaining float64
	Items     []Rect
}

// NewBin2D creates an empty shelf-based bin.
func NewBin2D(width, height float64) Bin2D {
	return Bin2D{Width: width, Height: height}
}

// Add attempts to place a rectangle using a simple first-fit shelf strategy.
func (b *Bin2D) Add(r Rect) bool {
	if r.Width < 0 || r.Height < 0 {
		return false
	}
	if r.Width > b.Width+1e-9 || r.Height > b.Height+1e-9 {
		return false
	}
	for i := range b.Shelves {
		if r.Height <= b.Shelves[i].Height+1e-9 && r.Width <= b.Shelves[i].Remaining+1e-9 {
			b.Shelves[i].Items = append(b.Shelves[i].Items, r)
			b.Shelves[i].Remaining -= r.Width
			return true
		}
	}
	usedHeight := 0.0
	for _, s := range b.Shelves {
		usedHeight += s.Height
	}
	if usedHeight+r.Height > b.Height+1e-9 {
		return false
	}
	newShelf := shelf{
		Height:    r.Height,
		Remaining: b.Width - r.Width,
		Items:     []Rect{r},
	}
	b.Shelves = append(b.Shelves, newShelf)
	return true
}

// ShelfFirstFit packs rectangles with a first-fit shelf heuristic.
func ShelfFirstFit(binWidth, binHeight float64, rects []Rect) ([]Bin2D, error) {
	if binWidth <= 0 || binHeight <= 0 {
		return nil, errors.New("bin dimensions must be positive")
	}
	var bins []Bin2D
	for _, r := range rects {
		if r.Width < 0 || r.Height < 0 {
			return nil, errors.New("rectangle sizes must be non-negative")
		}
		placed := false
		for i := range bins {
			if bins[i].Add(r) {
				placed = true
				break
			}
		}
		if !placed {
			bin := NewBin2D(binWidth, binHeight)
			if !bin.Add(r) {
				return nil, errors.New("rectangle cannot fit into empty bin")
			}
			bins = append(bins, bin)
		}
	}
	return bins, nil
}

// ShelfUsage computes the fraction of area used.
func ShelfUsage(bins []Bin2D) float64 {
	if len(bins) == 0 {
		return 0
	}
	used := 0.0
	total := 0.0
	for _, b := range bins {
		total += b.Width * b.Height
		for _, s := range b.Shelves {
			for _, r := range s.Items {
				used += r.Width * r.Height
			}
		}
	}
	if total == 0 {
		return 0
	}
	return used / total
}
