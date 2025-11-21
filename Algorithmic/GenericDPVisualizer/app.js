import {
  buildHistoryFromSteps,
  buildSteps,
  createEmptyTable,
  exportSnapshot,
} from './dpLogic.js';

const presetSelect = document.getElementById('preset');
const rowsInput = document.getElementById('rows');
const colsInput = document.getElementById('cols');
const baseInput = document.getElementById('base');
const recurrenceInput = document.getElementById('recurrence');
const tableContainer = document.getElementById('table');
const dependencyLabel = document.getElementById('dependency-label');
const stepLabel = document.getElementById('step-label');

const presets = {
  custom: {
    label: 'Custom (enter your own recurrence)',
    rows: 5,
    cols: 5,
    recurrence: 'dp[i-1][j] + dp[i][j-1]',
    base: 0,
    initializer: (i, j, _table, _ctx, base) => (i === 0 || j === 0 ? base : null),
    context: {},
  },
  knapsack: {
    label: '0/1 Knapsack (weights [1,3,4], values [1,4,5], capacity 6)',
    rows: 4,
    cols: 7,
    recurrence:
      'Math.max(dp[i-1][j], ctx.weights[i-1] <= j ? ctx.values[i-1] + dp[i-1][j-ctx.weights[i-1]] : dp[i-1][j])',
    base: 0,
    initializer: (i, j, _table, _ctx, base) => (i === 0 || j === 0 ? base : null),
    context: { weights: [1, 3, 4], values: [1, 4, 5] },
  },
  lis: {
    label: 'LIS (sequence [10, 9, 2, 5, 3, 7])',
    rows: 6,
    cols: 1,
    recurrence: '1 + ctx.prevLessMax(i, dp, ctx)',
    base: 1,
    initializer: (i, j, _table, _ctx, base) => (j === 0 && i === 0 ? base : null),
    context: {
      sequence: [10, 9, 2, 5, 3, 7],
      prevLessMax(i, dp, ctx) {
        let best = 0;
        for (let k = 0; k < i; k += 1) {
          if (ctx.sequence[k] < ctx.sequence[i]) {
            best = Math.max(best, dp[k][0]);
          }
        }
        return best;
      },
    },
  },
};

let steps = [];
let history = [];
let currentStepIndex = 0;
let playbackTimer = null;

const renderTable = (tableState, activeStep = null) => {
  tableContainer.innerHTML = '';
  tableContainer.style.gridTemplateRows = `repeat(${tableState.length}, auto)`;

  tableState.forEach((row, i) => {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'dp-row';
    row.forEach((cell, j) => {
      const cellDiv = document.createElement('div');
      cellDiv.className = 'cell';
      const isInit = steps.find(
        (step, idx) => idx < currentStepIndex && step.type === 'init' && step.row === i && step.col === j,
      );
      if (isInit) cellDiv.classList.add('init');

      if (activeStep && activeStep.row === i && activeStep.col === j) {
        cellDiv.classList.add('active');
      }
      if (activeStep && activeStep.dependencies.some((dep) => dep.row === i && dep.col === j)) {
        cellDiv.classList.add('dependency');
      }

      cellDiv.textContent = cell ?? '';
      rowDiv.appendChild(cellDiv);
    });
    tableContainer.appendChild(rowDiv);
  });
};

const updateLabels = (activeStep) => {
  if (!activeStep) {
    stepLabel.textContent = 'No steps loaded.';
    dependencyLabel.textContent = '';
    return;
  }
  stepLabel.textContent = `Step ${currentStepIndex}/${steps.length}: set dp[${activeStep.row}][${activeStep.col}] = ${activeStep.value}`;
  if (activeStep.dependencies.length === 0) {
    dependencyLabel.textContent = 'Initialization step (no dependencies).';
  } else {
    const deps = activeStep.dependencies.map((d) => `dp[${d.row}][${d.col}]`).join(', ');
    dependencyLabel.textContent = `Depends on: ${deps}`;
  }
};

const stopPlayback = () => {
  if (playbackTimer) {
    clearInterval(playbackTimer);
    playbackTimer = null;
  }
};

const goToStep = (index) => {
  currentStepIndex = Math.max(0, Math.min(index, steps.length));
  const activeStep = currentStepIndex === 0 ? null : steps[currentStepIndex - 1];
  renderTable(history[currentStepIndex], activeStep);
  updateLabels(activeStep);
};

const regenerate = () => {
  const rows = Number(rowsInput.value);
  const cols = Number(colsInput.value);
  const base = Number(baseInput.value);
  const recurrence = recurrenceInput.value.trim();
  if (!recurrence) return;

  const presetKey = presetSelect.value || 'custom';
  const preset = presets[presetKey];
  const initializer = (i, j, table, ctx) => preset.initializer(i, j, table, ctx, base);
  const { steps: builtSteps } = buildSteps(rows, cols, recurrence, initializer, preset.context);
  steps = builtSteps;
  history = buildHistoryFromSteps(rows, cols, steps);
  goToStep(0);
};

const play = () => {
  stopPlayback();
  playbackTimer = setInterval(() => {
    if (currentStepIndex >= steps.length) {
      stopPlayback();
      return;
    }
    goToStep(currentStepIndex + 1);
  }, 800);
};

const presetOptions = Object.entries(presets)
  .map(([key, value]) => `<option value="${key}">${value.label}</option>`)
  .join('');
presetSelect.innerHTML = presetOptions;
presetSelect.value = 'knapsack';

const loadPreset = (key) => {
  const preset = presets[key];
  rowsInput.value = preset.rows;
  colsInput.value = preset.cols;
  baseInput.value = preset.base;
  recurrenceInput.value = preset.recurrence;
  regenerate();
};

presetSelect.addEventListener('change', (e) => loadPreset(e.target.value));
document.getElementById('generate').addEventListener('click', regenerate);
document.getElementById('play').addEventListener('click', play);
document.getElementById('pause').addEventListener('click', stopPlayback);
document.getElementById('next').addEventListener('click', () => goToStep(currentStepIndex + 1));
document.getElementById('prev').addEventListener('click', () => goToStep(currentStepIndex - 1));
document.getElementById('reset').addEventListener('click', () => goToStep(0));
document.getElementById('snapshot').addEventListener('click', () => {
  const snapshot = exportSnapshot(history[currentStepIndex], steps, currentStepIndex);
  const blob = new Blob([snapshot], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'dp-snapshot.json';
  link.click();
  URL.revokeObjectURL(url);
});

// Initial render
loadPreset('knapsack');
