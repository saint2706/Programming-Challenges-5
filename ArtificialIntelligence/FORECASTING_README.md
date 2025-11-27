# Time-Series Forecasting Toolkit

This toolkit (`ArtificialIntelligence/forecasting_toolkit.py`) demonstrates three
popular forecasting approaches on the classic monthly airline passenger series:

- **ARIMA** via `statsmodels`
- **Prophet** (if `prophet` or `fbprophet` is installed)
- **LSTM** implemented with `torch`

## Dependencies

Install the Python libraries you want to try. ARIMA and Prophet are optional if
you only want to run the others.

```bash
pip install pandas numpy statsmodels prophet torch
```

## Running the demo

Execute the script to train each available model on the embedded passenger data
and print the next 12 monthly forecasts. Adjust `-n` to change the horizon.

```bash
python ArtificialIntelligence/forecasting_toolkit.py -n 12
```

If a dependency is missing, the script will skip that model and note which
package to install.
