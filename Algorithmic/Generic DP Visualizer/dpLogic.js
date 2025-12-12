const cloneTable = (table) => table.map((row) => row.slice());

export function createEmptyTable(rows, cols, fillValue = null) {
  return Array.from({ length: rows }, () => Array.from({ length: cols }, () => fillValue));
}

export function parseDependencies(recurrence) {
  const deps = new Set();
  const twoDRegex = /dp\[(i[+-]?\d*|\d+)\]\[(j[+-]?\d*|\d+)\]/g;
  const oneDRegex = /dp\[(i[+-]?\d*|\d+)\](?!\[)/g;

  let match;
  while ((match = twoDRegex.exec(recurrence)) !== null) {
    const [_, iPart, jPart] = match;
    deps.add(JSON.stringify({ axis: '2d', iPart, jPart }));
  }
  while ((match = oneDRegex.exec(recurrence)) !== null) {
    const [_, iPart] = match;
    deps.add(JSON.stringify({ axis: '1d', iPart }));
  }

  return Array.from(deps).map((entry) => JSON.parse(entry));
}

const toIndex = (base, token) => {
  if (token.startsWith('i') || token.startsWith('j')) {
    const offset = token.slice(1);
    return base + (offset ? Number(offset) : 0);
  }
  return Number(token);
};

export function dependenciesForCell(i, j, recurrence, rows, cols) {
  return parseDependencies(recurrence)
    .map((dep) => {
      if (dep.axis === '1d') {
        const targetRow = 0;
        const targetCol = toIndex(i, dep.iPart);
        return { row: targetRow, col: targetCol };
      }
      const targetRow = toIndex(i, dep.iPart);
      const targetCol = toIndex(j, dep.jPart);
      return { row: targetRow, col: targetCol };
    })
    .filter(({ row, col }) => row >= 0 && col >= 0 && row < rows && col < cols);
}

export function evaluateRecurrence(recurrence, i, j, table, context = {}) {
  const safeTable = cloneTable(table).map((row) => row.map((cell) => (cell == null ? 0 : cell)));
  const evaluator = new Function('i', 'j', 'dp', 'ctx', `return ${recurrence};`);
  return evaluator(i, j, safeTable, context);
}

export function buildSteps(rows, cols, recurrence, initializer = () => null, context = {}) {
  const table = createEmptyTable(rows, cols);
  const steps = [];

  for (let i = 0; i < rows; i += 1) {
    for (let j = 0; j < cols; j += 1) {
      const baseValue = initializer(i, j, table, context);
      if (baseValue !== null && baseValue !== undefined) {
        table[i][j] = baseValue;
        steps.push({
          row: i,
          col: j,
          value: baseValue,
          dependencies: [],
          type: 'init',
        });
        continue;
      }
      const dependencies = dependenciesForCell(i, j, recurrence, rows, cols);
      const value = evaluateRecurrence(recurrence, i, j, table, context);
      table[i][j] = value;
      steps.push({ row: i, col: j, value, dependencies, type: 'update' });
    }
  }

  return { table, steps };
}

export function applyStep(table, step) {
  const next = cloneTable(table);
  next[step.row][step.col] = step.value;
  return next;
}

export function exportSnapshot(table, steps, currentStepIndex) {
  return JSON.stringify(
    {
      appliedSteps: currentStepIndex,
      table,
      history: steps.slice(0, currentStepIndex),
    },
    null,
    2
  );
}

export function buildHistoryFromSteps(rows, cols, steps) {
  const history = [createEmptyTable(rows, cols)];
  steps.forEach((step) => {
    const latest = applyStep(history[history.length - 1], step);
    history.push(latest);
  });
  return history;
}
