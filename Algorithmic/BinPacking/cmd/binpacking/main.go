package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	"binpacking"
)

func parseFloatList(input string) ([]float64, error) {
	if strings.TrimSpace(input) == "" {
		return nil, fmt.Errorf("no items supplied")
	}
	parts := strings.FieldsFunc(input, func(r rune) bool {
		return r == ',' || r == ';' || r == ' ' || r == '\n' || r == '\t'
	})
	values := make([]float64, 0, len(parts))
	for _, p := range parts {
		if p == "" {
			continue
		}
		v, err := strconv.ParseFloat(p, 64)
		if err != nil {
			return nil, err
		}
		values = append(values, v)
	}
	return values, nil
}

func parseRectList(input string) ([]binpacking.Rect, error) {
	if strings.TrimSpace(input) == "" {
		return nil, fmt.Errorf("no rectangles supplied")
	}
	specs := strings.FieldsFunc(input, func(r rune) bool { return r == ';' || r == ' ' || r == '\n' || r == '\t' })
	rects := make([]binpacking.Rect, 0, len(specs))
	for _, spec := range specs {
		if spec == "" {
			continue
		}
		wh := strings.Split(spec, "x")
		if len(wh) != 2 {
			return nil, fmt.Errorf("rectangle must be widthxheight: %s", spec)
		}
		w, err := strconv.ParseFloat(wh[0], 64)
		if err != nil {
			return nil, err
		}
		h, err := strconv.ParseFloat(wh[1], 64)
		if err != nil {
			return nil, err
		}
		rects = append(rects, binpacking.Rect{Width: w, Height: h})
	}
	return rects, nil
}

func printBins(bins binpacking.Bins) {
	fmt.Printf("bins used: %d\n", len(bins))
	for i, b := range bins {
		fmt.Printf("bin %d (remaining %.2f): %v\n", i+1, b.Remaining, b.Items)
	}
	fmt.Printf("utilization: %.2f%%\n", binpacking.Bins(bins).Utilization()*100)
}

func run1D(capacity float64, heuristic string, items string) error {
	list, err := parseFloatList(items)
	if err != nil {
		return err
	}
	var bins binpacking.Bins
	switch heuristic {
	case "first":
		bins, err = binpacking.FirstFit(capacity, list)
	case "best":
		bins, err = binpacking.BestFit(capacity, list)
	case "ffd":
		bins, err = binpacking.FirstFitDecreasing(capacity, list)
	default:
		return fmt.Errorf("unknown heuristic %s", heuristic)
	}
	if err != nil {
		return err
	}
	printBins(bins)
	return nil
}

func run2D(width, height float64, rectSpec string) error {
	rects, err := parseRectList(rectSpec)
	if err != nil {
		return err
	}
	bins, err := binpacking.ShelfFirstFit(width, height, rects)
	if err != nil {
		return err
	}
	fmt.Printf("bins used: %d\n", len(bins))
	for i, b := range bins {
		fmt.Printf("bin %d shelves:\n", i+1)
		for j, s := range b.Shelves {
			fmt.Printf("  shelf %d (h=%.2f rem=%.2f): ", j+1, s.Height, s.Remaining)
			writer := csv.NewWriter(os.Stdout)
			records := make([][]string, 1)
			shelfParts := make([]string, 0, len(s.Items))
			for _, r := range s.Items {
				shelfParts = append(shelfParts, fmt.Sprintf("%.1fx%.1f", r.Width, r.Height))
			}
			records[0] = []string{strings.Join(shelfParts, " ")}
			writer.WriteAll(records)
		}
	}
	fmt.Printf("area utilization: %.2f%%\n", binpacking.ShelfUsage(bins)*100)
	return nil
}

func main() {
	heuristic := flag.String("heuristic", "first", "1D heuristic: first, best, ffd")
	capacity := flag.Float64("capacity", 0, "bin capacity for 1D")
	items := flag.String("items", "", "comma/space separated item sizes for 1D")
	mode2D := flag.Bool("twoD", false, "enable 2D rectangle packing")
	binWidth := flag.Float64("width", 0, "bin width for 2D")
	binHeight := flag.Float64("height", 0, "bin height for 2D")
	rects := flag.String("rects", "", "rectangles as WxH;WxH for 2D")
	flag.Parse()

	if *mode2D {
		if *binWidth <= 0 || *binHeight <= 0 {
			log.Fatal("2D mode requires positive width and height")
		}
		if err := run2D(*binWidth, *binHeight, *rects); err != nil {
			log.Fatal(err)
		}
		return
	}

	if *capacity <= 0 {
		log.Fatal("1D mode requires positive capacity")
	}
	if err := run1D(*capacity, *heuristic, *items); err != nil {
		log.Fatal(err)
	}
}
