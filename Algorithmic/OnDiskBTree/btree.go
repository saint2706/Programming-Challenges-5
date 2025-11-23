package main

import (
	"bytes"
	"encoding/binary"
	"os"
)

// Constants for B-Tree
const (
	PageSize = 4096
	Order    = 6 // Max children. Degree = Order/2 = 3. Keys = Order-1 = 5.
)

type Page struct {
	ID       int64
	IsLeaf   bool
	NumItems int32
	Keys     [Order - 1]int64
	Values   [Order - 1]int64
	Children [Order]int64
}

// BTree manages the on-disk structure.
type BTree struct {
	file *os.File
	root int64 // Root Page ID
}

// NewBTree creates or opens a BTree file.
func NewBTree(filename string) (*BTree, error) {
	f, err := os.OpenFile(filename, os.O_RDWR|os.O_CREATE, 0666)
	if err != nil {
		return nil, err
	}

	info, _ := f.Stat()
	if info.Size() == 0 {
		// Init root
		root := Page{ID: 0, IsLeaf: true, NumItems: 0}
		writePage(f, &root)
		return &BTree{file: f, root: 0}, nil
	}

	// Assume root is always at 0
	return &BTree{file: f, root: 0}, nil
}

func (bt *BTree) Close() error {
	return bt.file.Close()
}

func (bt *BTree) Insert(key, value int64) error {
	root, err := readPage(bt.file, bt.root)
	if err != nil {
		return err
	}

	if root.NumItems == Order-1 {
		// Root is full, split it

		// Move old root content to new page
		oldRootID := bt.allocatePageID()
		root.ID = oldRootID
		writePage(bt.file, root) // Write old root data to new location

		// Setup Page 0 as new root
		newRoot := Page{ID: 0, IsLeaf: false, NumItems: 0}
		newRoot.Children[0] = oldRootID

		// Load the child (old root) back as a clean object for splitting logic if needed,
		// or just use the updated root object.
		// splitChild expects the parent pointer and index of child to split.
		// child is passed by value? No, let's pass *Page or value.
		// My splitChild signature: splitChild(parent *Page, index int32, child Page)

		bt.splitChild(&newRoot, 0, *root)
		bt.insertNonFull(&newRoot, key, value)

		// Ensure new root is written (it might be updated in insertNonFull/splitChild)
		// but insertNonFull writes modified nodes.
		// splitChild writes parent.
	} else {
		bt.insertNonFull(root, key, value)
	}
	return nil
}

func (bt *BTree) insertNonFull(node *Page, key, value int64) error {
	i := int(node.NumItems) - 1
	if node.IsLeaf {
		// Insert into sorted leaf
		for i >= 0 && key < node.Keys[i] {
			node.Keys[i+1] = node.Keys[i]
			node.Values[i+1] = node.Values[i]
			i--
		}
		node.Keys[i+1] = key
		node.Values[i+1] = value
		node.NumItems++
		writePage(bt.file, node)
	} else {
		// Find child
		for i >= 0 && key < node.Keys[i] {
			i--
		}
		i++
		childID := node.Children[i]
		child, _ := readPage(bt.file, childID)

		if child.NumItems == Order-1 {
			bt.splitChild(node, int32(i), *child)
			if key > node.Keys[i] {
				i++
			}
			childID = node.Children[i]
			child, _ = readPage(bt.file, childID)
		}
		bt.insertNonFull(child, key, value)
	}
	return nil
}

func (bt *BTree) splitChild(parent *Page, index int32, child Page) {
	// Split child into child and newChild
	mid := Order / 2 // 3

	newChild := Page{ID: bt.allocatePageID(), IsLeaf: child.IsLeaf, NumItems: int32(mid - 1)}

	// Copy top half keys/values to newChild
	for j := 0; j < mid-1; j++ {
		newChild.Keys[j] = child.Keys[j+mid]
		newChild.Values[j] = child.Values[j+mid]
	}

	// Copy children if not leaf
	if !child.IsLeaf {
		for j := 0; j < mid; j++ {
			newChild.Children[j] = child.Children[j+mid]
		}
	}

	child.NumItems = int32(mid - 1) // reduced size
	midKey := child.Keys[mid-1]
	midVal := child.Values[mid-1]

	// Shift parent children
	for j := int(parent.NumItems); j >= int(index)+1; j-- {
		parent.Children[j+1] = parent.Children[j]
	}
	parent.Children[index+1] = newChild.ID

	// Shift parent keys
	for j := int(parent.NumItems) - 1; j >= int(index); j-- {
		parent.Keys[j+1] = parent.Keys[j]
		parent.Values[j+1] = parent.Values[j]
	}
	parent.Keys[index] = midKey
	parent.Values[index] = midVal
	parent.NumItems++

	writePage(bt.file, &child)
	writePage(bt.file, &newChild)
	writePage(bt.file, parent)
}

func (bt *BTree) Search(key int64) (int64, bool) {
	return bt.searchRecursive(bt.root, key)
}

func (bt *BTree) searchRecursive(pageID int64, key int64) (int64, bool) {
	node, err := readPage(bt.file, pageID)
	if err != nil {
		return 0, false
	}

	i := 0
	for i < int(node.NumItems) && key > node.Keys[i] {
		i++
	}
	if i < int(node.NumItems) && key == node.Keys[i] {
		return node.Values[i], true
	}
	if node.IsLeaf {
		return 0, false
	}
	return bt.searchRecursive(node.Children[i], key)
}

// Helpers

func (bt *BTree) allocatePageID() int64 {
	info, _ := bt.file.Stat()
	size := info.Size()
	return size / PageSize
}

func writePage(f *os.File, p *Page) error {
	buf := new(bytes.Buffer)
	binary.Write(buf, binary.LittleEndian, p.ID)
	binary.Write(buf, binary.LittleEndian, p.IsLeaf)
	binary.Write(buf, binary.LittleEndian, p.NumItems)
	binary.Write(buf, binary.LittleEndian, p.Keys)
	binary.Write(buf, binary.LittleEndian, p.Values)
	binary.Write(buf, binary.LittleEndian, p.Children)

	// Pad to PageSize
	padding := PageSize - buf.Len()
	if padding > 0 {
		buf.Write(make([]byte, padding))
	}

	_, err := f.WriteAt(buf.Bytes(), p.ID*PageSize)
	return err
}

func readPage(f *os.File, id int64) (*Page, error) {
	b := make([]byte, PageSize)
	_, err := f.ReadAt(b, id*PageSize)
	if err != nil {
		return nil, err
	}

	buf := bytes.NewReader(b)
	var p Page
	binary.Read(buf, binary.LittleEndian, &p.ID)
	binary.Read(buf, binary.LittleEndian, &p.IsLeaf)
	binary.Read(buf, binary.LittleEndian, &p.NumItems)
	binary.Read(buf, binary.LittleEndian, &p.Keys)
	binary.Read(buf, binary.LittleEndian, &p.Values)
	binary.Read(buf, binary.LittleEndian, &p.Children)
	return &p, nil
}
