"""
Time Projection Module (Astronacci).

Uses Fibonacci time sequences and planetary cycles to project
potential reversal windows.

Features:
- Fibonacci time from significant low
- Planetary aspects (using ephem library)
- Lunar phase analysis
"""

from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from pulse.core.sapta.models import ModuleScore
from pulse.core.sapta.modules.base import BaseModule


class TimeProjectionModule(BaseModule):
    """
    Astronacci-style time projection analysis.

    Uses:
    1. Fibonacci time windows (21, 34, 55, 89, 144 days)
    2. Planetary aspects (if ephem available)
    3. Lunar phases

    Max Score: 15
    """

    name = "time_projection"
    max_score = 15.0

    # Fibonacci time windows (trading days)
    FIB_WINDOWS = [21, 34, 55, 89, 144]
    FIB_TOLERANCE = 3  # days tolerance

    def analyze(
        self,
        df: pd.DataFrame,
        include_planetary: bool = True,
        include_lunar: bool = True,
    ) -> ModuleScore:
        """
        Analyze time projections.

        Args:
            df: OHLCV DataFrame with DatetimeIndex
            include_planetary: Include planetary aspect analysis
            include_lunar: Include lunar phase analysis
        """
        if len(df) < 50:
            return self._create_score(0, False, "Insufficient data", [])

        score = 0.0
        signals = []
        features = {}
        projected_window = None

        current_date = df.index[-1]
        if isinstance(current_date, pd.Timestamp):
            current_date = current_date.to_pydatetime().date()

        # === 1. Fibonacci Time Analysis ===
        fib_score, fib_signals, fib_window, fib_features = self._analyze_fib_time(df)
        score += fib_score
        signals.extend(fib_signals)
        features.update(fib_features)
        projected_window = fib_window

        # === 2. Planetary Aspects (if available) ===
        if include_planetary:
            try:
                planet_score, planet_signals, planet_features = self._analyze_planetary(
                    current_date
                )
                score += planet_score
                signals.extend(planet_signals)
                features.update(planet_features)
            except Exception as e:
                features["planetary_error"] = str(e)

        # === 3. Lunar Phase ===
        if include_lunar:
            try:
                lunar_score, lunar_signals, lunar_features = self._analyze_lunar(current_date)
                score += lunar_score
                signals.extend(lunar_signals)
                features.update(lunar_features)
            except Exception as e:
                features["lunar_error"] = str(e)

        # Store projected window
        features["projected_window"] = projected_window

        # Determine status and details
        status = score >= 6  # Lowered threshold for status

        # Build informative details
        if features.get("in_fib_window"):
            details = f"In Fib window: Day {features.get('days_since_significant_low')} from low"
        elif projected_window:
            days_to = features.get("days_to_next_window", 0)
            details = f"Next window: {projected_window} ({days_to} days)"
        else:
            details = f"Day {features.get('days_since_significant_low', 0)} from low"

        result = self._create_score(score, status, details, signals, features)
        return result

    def _analyze_fib_time(
        self,
        df: pd.DataFrame,
    ) -> tuple[float, list[str], str | None, dict[str, Any]]:
        """
        Analyze Fibonacci time from significant low.

        Returns:
            Tuple of (score, signals, projected_window, features)
        """
        score = 0.0
        signals = []
        features = {}
        projected_window = None

        # Find significant low in history
        lookback = min(200, len(df))
        historical = df.tail(lookback)

        # Find the lowest point
        low_idx = historical["low"].idxmin()
        low_date = low_idx
        if isinstance(low_date, pd.Timestamp):
            low_date = low_date.to_pydatetime().date()

        current_date = df.index[-1]
        if isinstance(current_date, pd.Timestamp):
            current_date = current_date.to_pydatetime().date()

        # Calculate trading days since low (approximate)
        days_since_low = (current_date - low_date).days
        features["days_since_significant_low"] = int(days_since_low)
        features["significant_low_date"] = str(low_date)

        # Check if we're in a Fibonacci window
        in_window = False
        nearest_fib = None

        for fib_day in self.FIB_WINDOWS:
            distance = abs(days_since_low - fib_day)
            if distance <= self.FIB_TOLERANCE:
                score += 8
                signals.append(f"Day {days_since_low} from low (Fib {fib_day} window)")
                in_window = True
                nearest_fib = fib_day
                break

        features["in_fib_window"] = float(in_window)
        features["nearest_fib"] = nearest_fib

        # Project next window
        for fib_day in self.FIB_WINDOWS:
            if fib_day > days_since_low:
                days_to_window = fib_day - days_since_low
                window_start = current_date + timedelta(days=days_to_window - self.FIB_TOLERANCE)
                window_end = current_date + timedelta(days=days_to_window + self.FIB_TOLERANCE)

                projected_window = (
                    f"{window_start.strftime('%d %b')} - {window_end.strftime('%d %b %Y')}"
                )
                features["days_to_next_window"] = int(days_to_window)
                features["next_fib_day"] = fib_day

                if days_to_window <= 10:
                    score += 4
                    signals.append(f"Next Fib window in {days_to_window} days (Fib {fib_day})")
                elif days_to_window <= 20:
                    score += 2
                    signals.append(f"Approaching Fib {fib_day} window")
                break

        return score, signals, projected_window, features

    def _analyze_planetary(
        self,
        current_date: date,
    ) -> tuple[float, list[str], dict[str, Any]]:
        """
        Analyze planetary aspects using ephem library.

        Key aspects:
        - Conjunction (0°): Powerful, new beginnings
        - Sextile (60°): Harmonious opportunity
        - Square (90°): Tension, volatility
        - Trine (120°): Very harmonious
        - Opposition (180°): Tension, potential reversal
        """
        score = 0.0
        signals = []
        features = {}

        try:
            import ephem

            # Set observer date
            obs_date = ephem.Date(current_date)

            # Get planetary positions
            sun = ephem.Sun(obs_date)
            moon = ephem.Moon(obs_date)
            mercury = ephem.Mercury(obs_date)
            venus = ephem.Venus(obs_date)
            mars = ephem.Mars(obs_date)
            jupiter = ephem.Jupiter(obs_date)
            saturn = ephem.Saturn(obs_date)

            planets = {
                "sun": float(sun.hlong) * 180 / np.pi,
                "moon": float(moon.hlong) * 180 / np.pi,
                "mercury": float(mercury.hlong) * 180 / np.pi,
                "venus": float(venus.hlong) * 180 / np.pi,
                "mars": float(mars.hlong) * 180 / np.pi,
                "jupiter": float(jupiter.hlong) * 180 / np.pi,
                "saturn": float(saturn.hlong) * 180 / np.pi,
            }

            features["planetary_positions"] = planets

            # Check key aspects
            aspects_found = []

            # Jupiter-Saturn (major economic cycle)
            jup_sat_angle = abs(planets["jupiter"] - planets["saturn"]) % 360
            if jup_sat_angle > 180:
                jup_sat_angle = 360 - jup_sat_angle

            features["jupiter_saturn_angle"] = float(jup_sat_angle)

            if jup_sat_angle < 10:  # Conjunction
                score += 3
                aspects_found.append("Jupiter-Saturn conjunction (major cycle)")
            elif 85 < jup_sat_angle < 95:  # Square
                score += 1
                aspects_found.append("Jupiter-Saturn square (tension)")
            elif 175 < jup_sat_angle < 185:  # Opposition
                score += 2
                aspects_found.append("Jupiter-Saturn opposition (turning point)")

            # Venus aspects (market sentiment)
            ven_jup_angle = abs(planets["venus"] - planets["jupiter"]) % 360
            if ven_jup_angle > 180:
                ven_jup_angle = 360 - ven_jup_angle

            if 115 < ven_jup_angle < 125:  # Trine
                score += 2
                aspects_found.append("Venus-Jupiter trine (positive sentiment)")

            # Mercury retrograde check (simplified)
            # In reality would need to track apparent motion
            features["mercury_longitude"] = float(planets["mercury"])

            if aspects_found:
                signals.extend(aspects_found)
            else:
                signals.append("No major planetary aspects")

            return score, signals, features

        except ImportError:
            features["planetary_available"] = False
            return 0, ["Planetary analysis unavailable (install ephem)"], features

    def _analyze_lunar(
        self,
        current_date: date,
    ) -> tuple[float, list[str], dict[str, Any]]:
        """
        Analyze lunar phase.

        Market tendencies:
        - New Moon: Potential bottoms, new beginnings
        - Full Moon: Peak emotion, potential tops
        - First Quarter: Building momentum
        - Last Quarter: Declining momentum
        """
        score = 0.0
        signals = []
        features = {}

        try:
            import ephem

            # Get lunar phase
            obs_date = ephem.Date(current_date)

            # Calculate moon phase (0 = new, 0.5 = full)
            moon = ephem.Moon(obs_date)
            sun = ephem.Sun(obs_date)

            # Calculate elongation (angle between moon and sun)
            elongation = float(moon.hlong - sun.hlong)
            if elongation < 0:
                elongation += 2 * np.pi

            # Convert to phase (0-1)
            phase = elongation / (2 * np.pi)
            features["lunar_phase"] = float(phase)

            # Determine phase name
            if phase < 0.05 or phase > 0.95:
                phase_name = "new_moon"
                score += 2
                signals.append("New Moon (potential reversal point)")
            elif 0.2 < phase < 0.3:
                phase_name = "first_quarter"
                score += 1
                signals.append("First Quarter (momentum building)")
            elif 0.45 < phase < 0.55:
                phase_name = "full_moon"
                score += 2
                signals.append("Full Moon (high emotion, potential peak)")
            elif 0.7 < phase < 0.8:
                phase_name = "last_quarter"
                score += 1
                signals.append("Last Quarter (momentum declining)")
            else:
                phase_name = "intermediate"

            features["lunar_phase_name"] = phase_name

            # Always add lunar phase info
            if phase_name == "intermediate":
                signals.append(f"Lunar: Waxing phase ({phase:.0%})")

            # Calculate next new moon
            next_new = ephem.next_new_moon(obs_date)
            next_new_date = ephem.Date(next_new).datetime().date()
            days_to_new = (next_new_date - current_date).days
            features["days_to_new_moon"] = int(days_to_new)

            if days_to_new <= 3:
                score += 1
                signals.append(f"New Moon in {days_to_new} days")

            return score, signals, features

        except ImportError:
            features["lunar_available"] = False
            return 0, ["Lunar analysis unavailable (install ephem)"], features
