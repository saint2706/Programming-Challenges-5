"""Time-series forecasting toolkit combining ARIMA, Prophet, and an LSTM forecaster.

This module demonstrates classic and neural approaches on a sample univariate
series (monthly airline passengers). It provides standalone functions for each
model family and a CLI demonstration that prints forecasts for the next N
periods.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module
from importlib.util import find_spec
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


@dataclass
class ForecastResult:
    """Container for forecasted values and model description."""

    model: str
    predictions: pd.Series

    def pretty_print(self) -> None:
        header = f"{self.model} forecast"
        print(f"\n{header}\n{'-' * len(header)}")
        for timestamp, value in self.predictions.items():
            print(f"{timestamp.date()}: {value:.2f}")


def load_sample_passenger_series() -> pd.Series:
    """Return the monthly AirPassengers series as a pandas Series.

    The values are embedded to avoid network or dataset download requirements.
    """

    passengers: List[int] = [
        112,
        118,
        132,
        129,
        121,
        135,
        148,
        148,
        136,
        119,
        104,
        118,
        115,
        126,
        141,
        135,
        125,
        149,
        170,
        170,
        158,
        133,
        114,
        140,
        145,
        150,
        178,
        163,
        172,
        178,
        199,
        199,
        184,
        162,
        146,
        166,
        171,
        180,
        193,
        181,
        183,
        218,
        230,
        242,
        209,
        191,
        172,
        194,
        196,
        196,
        236,
        235,
        229,
        243,
        264,
        272,
        237,
        211,
        180,
        201,
        204,
        188,
        235,
        227,
        234,
        264,
        302,
        293,
        259,
        229,
        203,
        229,
        242,
        233,
        267,
        269,
        270,
        315,
        364,
        347,
        312,
        274,
        237,
        278,
        284,
        277,
        317,
        313,
        318,
        374,
        413,
        405,
        355,
        306,
        271,
        306,
        315,
        301,
        356,
        348,
        355,
        422,
        465,
        467,
        404,
        347,
        305,
        336,
        340,
        318,
        362,
        348,
        363,
        435,
        491,
        505,
        404,
        359,
        310,
        337,
        360,
        342,
        406,
        396,
        420,
        472,
        548,
        559,
        463,
        407,
        362,
        405,
        417,
        391,
        419,
        461,
        472,
        535,
        622,
        606,
        508,
        461,
        390,
        432,
    ]
    dates = pd.date_range(start="1949-01-01", periods=len(passengers), freq="MS")
    return pd.Series(passengers, index=dates, name="air_passengers")


def forecast_arima(
    series: pd.Series, steps: int = 12, order: tuple[int, int, int] = (2, 1, 2)
) -> ForecastResult:
    """Fit a simple ARIMA model and forecast forward."""

    from statsmodels.tsa.arima.model import ARIMA

    model = ARIMA(series, order=order)
    fitted = model.fit()
    forecast = fitted.forecast(steps=steps)
    forecast.index = pd.date_range(
        start=series.index[-1] + pd.offsets.MonthBegin(1), periods=steps, freq="MS"
    )
    return ForecastResult("ARIMA", forecast)


def _import_first_available(module_names: Iterable[str]):
    for name in module_names:
        if find_spec(name):
            return import_module(name)
    raise ImportError(f"None of the modules {module_names} are installed.")


def forecast_prophet(series: pd.Series, steps: int = 12) -> ForecastResult:
    """Fit a Prophet model if available and return the forecast."""

    prophet_module = _import_first_available(["prophet", "fbprophet"])
    Prophet = prophet_module.Prophet
    df = series.reset_index().rename(columns={"index": "ds", 0: "y", series.name: "y"})

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=steps, freq="MS")
    forecast_df = model.predict(future)
    forecast_df = forecast_df.set_index("ds").iloc[-steps:]
    return ForecastResult("Prophet", forecast_df["yhat"])


class LSTMForecaster:
    """A minimal LSTM forecaster implemented with PyTorch."""

    def __init__(
        self,
        lookback: int = 12,
        hidden_size: int = 32,
        lr: float = 1e-2,
        epochs: int = 250,
    ):
        self.lookback = lookback
        self.hidden_size = hidden_size
        self.lr = lr
        self.epochs = epochs
        self.model: Optional[object] = None
        self.mean: float = 0.0
        self.std: float = 1.0

    def _build_model(self):
        from torch import nn

        class _Net(nn.Module):
            def __init__(self, lookback: int, hidden: int):
                super().__init__()
                self.lstm = nn.LSTM(input_size=1, hidden_size=hidden, batch_first=True)
                self.fc = nn.Linear(hidden, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                out = out[:, -1, :]
                return self.fc(out)

        return _Net(self.lookback, self.hidden_size)

    def fit(self, series: pd.Series) -> None:
        import torch
        from torch import nn, optim
        from torch.utils.data import DataLoader, TensorDataset

        values = series.values.astype(np.float32)
        self.mean = float(values.mean())
        self.std = float(values.std())
        normalized = (values - self.mean) / (self.std + 1e-8)

        sequences, labels = [], []
        for i in range(len(normalized) - self.lookback):
            sequences.append(normalized[i : i + self.lookback])
            labels.append(normalized[i + self.lookback])

        x_tensor = torch.tensor(np.array(sequences)).unsqueeze(-1)
        y_tensor = torch.tensor(np.array(labels)).unsqueeze(-1)
        loader = DataLoader(
            TensorDataset(x_tensor, y_tensor), batch_size=16, shuffle=True
        )

        self.model = self._build_model()
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.lr)

        for _ in range(self.epochs):
            for xb, yb in loader:
                optimizer.zero_grad()
                preds = self.model(xb)
                loss = criterion(preds, yb)
                loss.backward()
                optimizer.step()

    def predict(self, last_values: np.ndarray, steps: int) -> np.ndarray:
        import torch

        if self.model is None:
            raise RuntimeError("Model is not trained. Call fit() first.")

        history = (last_values - self.mean) / (self.std + 1e-8)
        preds: List[float] = []
        for _ in range(steps):
            input_seq = (
                torch.tensor(history[-self.lookback :])
                .float()
                .view(1, self.lookback, 1)
            )
            with torch.no_grad():
                pred_norm = self.model(input_seq).item()
            preds.append(pred_norm * (self.std + 1e-8) + self.mean)
            history = np.append(history, pred_norm)
        return np.array(preds)


def forecast_lstm(
    series: pd.Series, steps: int = 12, lookback: int = 12
) -> ForecastResult:
    """Fit the LSTM forecaster and project forward."""

    _import_first_available(["torch"])  # Ensure PyTorch is available.
    forecaster = LSTMForecaster(lookback=lookback)
    forecaster.fit(series)
    preds = forecaster.predict(series.values.astype(np.float32), steps)
    forecast_index = pd.date_range(
        start=series.index[-1] + pd.offsets.MonthBegin(1), periods=steps, freq="MS"
    )
    return ForecastResult("LSTM", pd.Series(preds, index=forecast_index))


def run_demo(forecast_horizon: int = 12) -> None:
    series = load_sample_passenger_series()
    methods = [
        ("ARIMA", lambda: forecast_arima(series, steps=forecast_horizon)),
        ("Prophet", lambda: forecast_prophet(series, steps=forecast_horizon)),
        ("LSTM", lambda: forecast_lstm(series, steps=forecast_horizon)),
    ]

    print("Loaded sample series with", len(series), "observations.")
    for name, method in methods:
        try:
            result = method()
            result.pretty_print()
        except ImportError as exc:
            print(f"\n{name} forecast\n{'-' * (len(name) + 9)}")
            print(f"Skipped because dependency is missing: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demo time-series forecasting toolkit."
    )
    parser.add_argument(
        "-n",
        "--steps",
        type=int,
        default=12,
        help="Number of future periods to forecast.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_demo(forecast_horizon=args.steps)


if __name__ == "__main__":
    main()
