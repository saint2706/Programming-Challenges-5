import { describe, expect, it } from 'vitest';
import {
  applyStep,
  buildHistoryFromSteps,
  buildSteps,
  createEmptyTable,
  exportSnapshot,
} from '../dpLogic.js';

describe('table creation and steps', () => {
  it('initializes base cells and computes recurrence-driven updates', () => {
    const initializer = (i, j, _table, _ctx, base) =>
      i === 0 || j === 0 ? base : null;
    const recurrence = 'dp[i-1][j] + dp[i][j-1] + 1';
    const { steps } = buildSteps(3, 3, recurrence, (i, j, table, ctx) =>
      initializer(i, j, table, ctx, 0)
    );

    expect(steps[0]).toMatchObject({ row: 0, col: 0, value: 0, type: 'init' });
    const updateStep = steps.find((s) => s.row === 1 && s.col === 1);
    expect(updateStep.value).toBe(1); // dp[0][1] + dp[1][0] + 1 = 0 + 0 + 1
    expect(updateStep.dependencies).toEqual([
      { row: 0, col: 1 },
      { row: 1, col: 0 },
    ]);
  });
});

describe('history building and snapshot exporting', () => {
  it('replays steps into table history and exports structured snapshot', () => {
    const table = createEmptyTable(2, 2);
    const steps = [
      { row: 0, col: 0, value: 0, dependencies: [], type: 'init' },
      {
        row: 0,
        col: 1,
        value: 1,
        dependencies: [{ row: 0, col: 0 }],
        type: 'update',
      },
    ];

    const history = buildHistoryFromSteps(2, 2, steps);
    expect(history).toHaveLength(3);
    expect(history[2][0][1]).toBe(1);

    const exported = JSON.parse(exportSnapshot(history[2], steps, 2));
    expect(exported.appliedSteps).toBe(2);
    expect(exported.table[0][1]).toBe(1);
    expect(exported.history).toHaveLength(2);
  });
});
