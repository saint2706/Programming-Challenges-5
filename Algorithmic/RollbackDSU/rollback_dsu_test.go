package rollbackdsu

import "testing"

func TestUnionAndSnapshotRollback(t *testing.T) {
	dsu := NewRollbackDSU(5)
	dsu.Union(0, 1)
	dsu.Union(2, 3)
	snap := dsu.Snapshot()

	if !dsu.Union(1, 2) {
		t.Fatalf("expected union to merge distinct components")
	}

	if !dsu.Connected(0, 3) {
		t.Fatalf("components should be connected after union across snapshots")
	}

	if size := dsu.Size(0); size != 4 {
		t.Fatalf("expected merged size 4, got %d", size)
	}

	if err := dsu.Rollback(snap); err != nil {
		t.Fatalf("rollback failed: %v", err)
	}

	if dsu.Connected(0, 3) {
		t.Fatalf("rollback should disconnect previously merged components")
	}

	if size := dsu.Size(0); size != 2 {
		t.Fatalf("expected size 2 for component {0,1}, got %d", size)
	}
	if size := dsu.Size(2); size != 2 {
		t.Fatalf("expected size 2 for component {2,3}, got %d", size)
	}
}

func TestMultipleSnapshots(t *testing.T) {
	dsu := NewRollbackDSU(6)
	s0 := dsu.Snapshot()

	dsu.Union(0, 1)
	s1 := dsu.Snapshot()
	dsu.Union(1, 2)
	dsu.Union(3, 4)
	s2 := dsu.Snapshot()

	dsu.Union(0, 4)

	if size := dsu.Size(0); size != 5 {
		t.Fatalf("expected size 5 after connecting clusters, got %d", size)
	}

	if err := dsu.Rollback(s2); err != nil {
		t.Fatalf("rollback to s2 failed: %v", err)
	}

	if dsu.Connected(0, 4) {
		t.Fatalf("rollback to s2 should undo last union")
	}
	if size := dsu.Size(0); size != 3 {
		t.Fatalf("expected size 3 after rollback to s2, got %d", size)
	}

	if err := dsu.Rollback(s1); err != nil {
		t.Fatalf("rollback to s1 failed: %v", err)
	}

	if size := dsu.Size(0); size != 2 {
		t.Fatalf("expected size 2 after rollback to s1, got %d", size)
	}
	if dsu.Connected(0, 2) {
		t.Fatalf("rollback to s1 should separate nodes 0 and 2")
	}

	if err := dsu.Rollback(s0); err != nil {
		t.Fatalf("rollback to s0 failed: %v", err)
	}
	for i := 0; i < 5; i++ {
		if dsu.Size(i) != 1 {
			t.Fatalf("expected all nodes size 1 after full rollback, node %d has size %d", i, dsu.Size(i))
		}
	}
}

func TestInvalidRollbackAndRedundantUnions(t *testing.T) {
	dsu := NewRollbackDSU(3)
	dsu.Union(0, 1)

	if dsu.Union(0, 1) {
		t.Fatalf("redundant union should return false")
	}

	if err := dsu.Rollback(5); err == nil {
		t.Fatalf("expected error on invalid snapshot index")
	}

	snap := dsu.Snapshot()
	dsu.Union(1, 2)

	if err := dsu.Rollback(snap); err != nil {
		t.Fatalf("unexpected rollback error: %v", err)
	}
	if dsu.Connected(0, 2) {
		t.Fatalf("rollback should disconnect 0 and 2")
	}
}
