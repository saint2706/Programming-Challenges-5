# Dataset Explorer UI

A Streamlit application for quickly inspecting CSV datasets. Upload files directly or point to a CSV path to visualize summaries, distributions, correlations, and optional profiling reports.

## Features
- Upload CSVs or provide a filesystem path (useful for large local files).
- Preview raw data and generate summary statistics.
- Visualize numeric distributions and correlation heatmaps.
- Opt-in profiling via **pandas-profiling (ydata-profiling)** or **Sweetviz** with downloadable HTML reports.
- Sample datasets included for quick testing.

## Getting Started

1. **Install dependencies** (use a virtual environment if desired):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Streamlit app** from the repository root:
   ```bash
   streamlit run "Practical/Dataset Explorer UI/app.py"
   ```

3. **Load data** using either method:
   - Upload a CSV via the sidebar widget.
   - Provide a local CSV path (e.g., `Practical/Dataset Explorer UI/sample_data/iris_sample.csv`).

4. **Explore insights**:
   - View raw data and summary stats.
   - Toggle distribution plots and correlation heatmaps.
   - Enable profiling toggles to generate and download detailed HTML reports.

## Sample Data
- `sample_data/iris_sample.csv`: Small subset of the Iris flower measurements.
- `sample_data/sales_sample.csv`: Example transactional sales records with regions and pricing.

Feel free to swap in your own CSV files to explore additional datasets.
