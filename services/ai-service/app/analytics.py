"""Pure analytics functions (pandas + numpy + sklearn).

These functions NEVER touch the network or the database — they only
transform DataFrames / dicts. That keeps them easy to unit-test and
guarantees we never fabricate measurements: when data is thin we say
so explicitly (``is_estimate=True`` + human-readable messages).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.config import (
    ANOMALY_MIN_POINTS,
    ANOMALY_Z_THRESHOLD,
    FORECAST_MIN_DAYS,
)

# Cost factors used by estimate_costs().
COST_RATES = {
    "electricity": 8.0,   # Rs 8 per kWh
    "water": 0.06,        # Rs 0.06 per litre
    "waste": 2.0,         # Rs 2 per kg disposal
}
COST_UNITS = {
    "electricity": "kWh",
    "water": "L",
    "waste": "kg",
}


def _to_df(readings) -> pd.DataFrame:
    """Normalise readings into a DataFrame with a numeric ``value`` column."""
    if isinstance(readings, pd.DataFrame):
        df = readings.copy()
    elif isinstance(readings, list):
        df = pd.DataFrame(readings) if readings else pd.DataFrame()
    else:
        return pd.DataFrame()
    if df.empty:
        return df
    # Tolerate alternative field names from the resource service.
    if "value" not in df.columns:
        for alt in ("consumption", "amount", "quantity"):
            if alt in df.columns:
                df["value"] = df[alt]
                break
    df["value"] = pd.to_numeric(df.get("value"), errors="coerce")
    df = df.dropna(subset=["value"])
    if "recorded_at" in df.columns:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce")
    return df


def _severity(z: float) -> str:
    az = abs(float(z))
    if az >= 4.0:
        return "critical"
    if az >= 3.0:
        return "high"
    return "medium"


# ------------------------------------------------------------------ #
# Anomaly detection (z-score)
# ------------------------------------------------------------------ #
def detect_anomalies(
    readings,
    threshold: float = ANOMALY_Z_THRESHOLD,
    min_points: int = ANOMALY_MIN_POINTS,
) -> dict:
    """Flag readings whose z-score exceeds ``threshold`` (|z| > 2.5 default).

    Returns ``{"anomalies": [...], "message": ..., "mean": ..., "std": ...}``.
    With fewer than ``min_points`` rows we return an empty list plus a
    beginner-friendly insufficient-data message instead of guessing.
    """
    df = _to_df(readings)
    if df.empty or len(df) < min_points:
        return {
            "anomalies": [],
            "message": (
                "insufficient data for anomaly detection "
                f"(need at least {min_points} readings, got {len(df)})."
            ),
            "mean": None,
            "std": None,
        }

    values = df["value"].to_numpy(dtype=float)
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    if std == 0 or not np.isfinite(std):
        return {
            "anomalies": [],
            "message": "insufficient variation for anomaly detection "
                       "(all readings are identical).",
            "mean": mean,
            "std": 0.0,
        }

    lo, hi = mean - threshold * std, mean + threshold * std
    anomalies = []
    for _, row in df.iterrows():
        z = (float(row["value"]) - mean) / std
        if abs(z) > threshold:
            recorded = row.get("recorded_at")
            if isinstance(recorded, (pd.Timestamp, datetime)):
                recorded_str = pd.Timestamp(recorded).isoformat()
            else:
                recorded_str = recorded if recorded is not None else None
            anomalies.append(
                {
                    "reading_id": str(
                        row.get("reading_id", row.get("_id", row.get("id", "")))
                    ),
                    "building_id": row.get("building_id"),
                    "resource_type": row.get("resource_type"),
                    "value": float(row["value"]),
                    "expected_range": [round(lo, 3), round(hi, 3)],
                    "z_score": round(float(z), 3),
                    "recorded_at": recorded_str,
                    "severity": _severity(z),
                }
            )
    anomalies.sort(key=lambda a: abs(a["z_score"]), reverse=True)
    return {
        "anomalies": anomalies,
        "message": None if anomalies else "no anomalies detected.",
        "mean": round(mean, 3),
        "std": round(std, 3),
    }


# ------------------------------------------------------------------ #
# Forecasting (daily totals + LinearRegression)
# ------------------------------------------------------------------ #
def forecast_usage(readings, days: int = 7) -> dict:
    """Aggregate daily totals and extrapolate with LinearRegression.

    With fewer than 7 distinct days of history we return a naive
    average-based fallback flagged ``is_estimate=True`` — we never
    present guesses as real measurements.
    """
    df = _to_df(readings)
    if df.empty or "recorded_at" not in df.columns:
        return {
            "history": [],
            "forecast": [],
            "method": "none",
            "is_estimate": True,
            "disclaimer": "insufficient data for forecasting "
                          "(no dated readings available). Showing no forecast.",
            "message": "insufficient data for forecasting "
                       "(no dated readings available).",
        }

    df = df.dropna(subset=["recorded_at"]).copy()
    if df.empty:
        return {
            "history": [],
            "forecast": [],
            "method": "none",
            "is_estimate": True,
            "disclaimer": "insufficient data for forecasting "
                          "(no dated readings available). Showing no forecast.",
            "message": "insufficient data for forecasting "
                       "(no dated readings available).",
        }

    df["date"] = df["recorded_at"].dt.date
    unit = ""
    if "unit" in df.columns:
        modes = df["unit"].dropna()
        unit = str(modes.mode().iloc[0]) if not modes.empty else ""

    daily = df.groupby("date", as_index=False)["value"].sum()
    daily = daily.sort_values("date")
    history = [
        {"date": d.isoformat(), "total": round(float(t), 3)}
        for d, t in zip(daily["date"], daily["value"])
    ]

    if len(daily) < FORECAST_MIN_DAYS:
        avg = float(daily["value"].mean()) if len(daily) else 0.0
        last = daily["date"].max() if len(daily) else datetime.utcnow().date()
        forecast = [
            {
                "date": (last + timedelta(days=i + 1)).isoformat(),
                "predicted_value": round(avg, 3),
                "unit": unit,
            }
            for i in range(max(int(days), 0))
        ]
        return {
            "history": history,
            "forecast": forecast,
            "method": "naive_average",
            "is_estimate": True,
            "disclaimer": (
                "Estimate only: fewer than "
                f"{FORECAST_MIN_DAYS} days of history, so the forecast "
                "repeats the daily average. Collect more data for a "
                "trend-based forecast."
            ),
            "message": (
                "insufficient data for trend forecast "
                f"(need at least {FORECAST_MIN_DAYS} days, got {len(daily)}). "
                "Returned naive average fallback."
            ),
        }

    X = np.arange(len(daily)).reshape(-1, 1)
    y = daily["value"].to_numpy(dtype=float)
    model = LinearRegression()
    model.fit(X, y)
    future_X = np.arange(len(daily), len(daily) + int(days)).reshape(-1, 1)
    preds = model.predict(future_X)
    preds = np.maximum(preds, 0.0)  # usage cannot be negative
    last = daily["date"].max()
    forecast = [
        {
            "date": (last + timedelta(days=i + 1)).isoformat(),
            "predicted_value": round(float(p), 3),
            "unit": unit,
        }
        for i, p in enumerate(preds)
    ]
    return {
        "history": history,
        "forecast": forecast,
        "method": "linear_regression",
        "is_estimate": False,
        "disclaimer": (
            "Statistical projection based on past daily totals; "
            "actual usage will vary."
        ),
    }


# ------------------------------------------------------------------ #
# Recommendations (rule-based)
# ------------------------------------------------------------------ #
def build_recommendations(totals, anomalies) -> list:
    """Turn totals + anomalies into actionable, beginner-friendly tips.

    ``totals`` maps resource_type -> total consumption. ``anomalies`` is
    the list produced by :func:`detect_anomalies`. Always returns a list
    (possibly a single generic tip) — never raises on empty input.
    """
    totals = totals or {}
    anomalies = anomalies or []
    recs = []

    elec = float(totals.get("electricity", 0) or 0)
    water = float(totals.get("water", 0) or 0)
    waste = float(totals.get("waste", 0) or 0)

    elec_anoms = [a for a in anomalies if (a or {}).get("resource_type") == "electricity"]
    water_anoms = [a for a in anomalies if (a or {}).get("resource_type") == "water"]
    waste_anoms = [a for a in anomalies if (a or {}).get("resource_type") == "waste"]

    if elec > 0:
        priority = "high" if (elec_anoms or elec > 1000) else "medium"
        recs.append(
            {
                "title": "LED retrofit & lighting audit",
                "description": (
                    f"Electricity usage totals {elec:g} kWh in the selected period"
                    + (f" with {len(elec_anoms)} spike(s)" if elec_anoms else "")
                    + ". Swap remaining fluorescents for LEDs, add occupancy "
                      "sensors in corridors, and set AC to 24-25C."
                ),
                "category": "electricity",
                "potential_saving_pct": 15,
                "priority": priority,
            }
        )
    if water > 0:
        priority = "high" if water_anoms else ("medium" if water > 5000 else "low")
        recs.append(
            {
                "title": "Leak check & low-flow fixtures",
                "description": (
                    f"Water usage totals {water:g} L"
                    + (f" with {len(water_anoms)} spike(s) — possible leak" if water_anoms else "")
                    + ". Inspect overhead tanks, taps and flush valves; "
                      "fit aerators and consider rainwater harvesting."
                ),
                "category": "water",
                "potential_saving_pct": 20 if water_anoms else 12,
                "priority": priority,
            }
        )
    if waste > 0:
        priority = "medium" if (waste_anoms or waste > 500) else "low"
        recs.append(
            {
                "title": "Waste segregation drive",
                "description": (
                    f"Waste totals {waste:g} kg in the selected period. "
                    "Place colour-coded bins, compost food waste, and run a "
                    "weekly hostel segregation audit."
                ),
                "category": "waste",
                "potential_saving_pct": 25,
                "priority": priority,
            }
        )
    if anomalies and len(anomalies) >= 3:
        recs.append(
            {
                "title": "Investigate repeated usage spikes",
                "description": (
                    f"{len(anomalies)} anomalous readings detected. Schedule a "
                    "facility walk-through on spike dates and check for faulty "
                    "meters, events, or equipment left running overnight."
                ),
                "category": "general",
                "potential_saving_pct": 10,
                "priority": "high",
            }
        )
    if not recs:
        recs.append(
            {
                "title": "Start metering consistently",
                "description": (
                    "Not enough data yet to personalise advice. Log daily "
                    "electricity, water and waste readings for at least a week "
                    "to unlock tailored recommendations."
                ),
                "category": "general",
                "potential_saving_pct": 5,
                "priority": "low",
            }
        )

    order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: order.get(r.get("priority", "low"), 2))
    return recs


# ------------------------------------------------------------------ #
# Cost estimation
# ------------------------------------------------------------------ #
def estimate_costs(totals) -> dict:
    """Estimate spend in INR from totals.

    Rates: electricity Rs 8/kWh, water Rs 0.06/L, waste Rs 2/kg disposal.
    Unknown resource types cost Rs 0 and are still listed for transparency.
    """
    totals = totals or {}
    breakdown = {}
    for rtype, total in totals.items():
        try:
            qty = float(total)
        except (TypeError, ValueError):
            qty = 0.0
        rate = COST_RATES.get(str(rtype).lower(), 0.0)
        breakdown[str(rtype)] = round(qty * rate, 2)
    total_cost = round(sum(breakdown.values()), 2)
    return {
        "breakdown": breakdown,
        "total": total_cost,
        "currency": "INR",
        "rates": dict(COST_RATES),
        "note": (
            "Estimates use standard campus rates "
            "(electricity Rs 8/kWh, water Rs 0.06/L, waste Rs 2/kg). "
            "Actual tariffs may vary."
        ),
    }
