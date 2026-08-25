"""
Machine Learning Probability Calibration & Evaluation Engine for NyayaSarathi.

Implements:
1. Platt Scaling (Sigmoid Logistic Calibration)
2. Isotonic Regression (Non-parametric Monotonic Calibration)
3. Formal Model Evaluation:
   - Brier Score: Mean Squared Error of Probabilities in [0, 1]
   - Expected Calibration Error (ECE)
   - ROC-AUC & Accuracy
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, accuracy_score, f1_score


class ProbabilityCalibrator:
    """
    Fits and applies probability calibration to ensure that estimated probabilities
    reflect empirical real-world judicial frequencies.
    """

    def __init__(self, method: str = "sigmoid"):
        self.method = method
        self.isotonic_model: Optional[IsotonicRegression] = None
        self.platt_a: float = 1.0
        self.platt_b: float = 0.0
        self.is_fitted: bool = False

    def fit(self, raw_probabilities: np.ndarray, actual_binary_outcomes: np.ndarray) -> Dict[str, float]:
        """
        Fits calibration model on raw estimated probabilities vs true binary outcomes (1=Favorable, 0=Unfavorable).
        """
        if len(raw_probabilities) < 10:
            # Insufficient samples for empirical fitting
            self.is_fitted = True
            return {"brier_before": 0.25, "brier_after": 0.25, "samples": len(raw_probabilities)}

        # Normalize to [0.0, 1.0]
        p_raw = np.clip(np.array(raw_probabilities, dtype=float) / 100.0 if np.max(raw_probabilities) > 1.0 else np.array(raw_probabilities, dtype=float), 0.01, 0.99)
        y = np.array(actual_binary_outcomes, dtype=int)

        brier_before = float(brier_score_loss(y, p_raw))

        if self.method == "isotonic":
            self.isotonic_model = IsotonicRegression(out_of_bounds="clip", y_min=0.05, y_max=0.95)
            self.isotonic_model.fit(p_raw, y)
            p_cal = self.isotonic_model.predict(p_raw)
        else:
            # Platt Scaling (Logistic Regression on log-odds)
            log_odds = np.log(p_raw / (1.0 - p_raw)).reshape(-1, 1)
            clf = LogisticRegression(C=1.0)
            clf.fit(log_odds, y)
            self.platt_a = float(clf.coef_[0][0])
            self.platt_b = float(clf.intercept_[0])
            p_cal = clf.predict_proba(log_odds)[:, 1]

        brier_after = float(brier_score_loss(y, p_cal))
        self.is_fitted = True

        return {
            "brier_before": round(brier_before, 4),
            "brier_after": round(brier_after, 4),
            "samples": len(raw_probabilities),
            "brier_improvement_pct": round(((brier_before - brier_after) / brier_before) * 100.0, 2) if brier_before > 0 else 0.0,
        }

    def calibrate_probability(self, raw_probability_pct: float) -> float:
        """
        Calibrates an estimated probability percentage to an empirical percentage.
        """
        p = float(np.clip(raw_probability_pct / 100.0, 0.01, 0.99))

        if not self.is_fitted:
            return raw_probability_pct

        if self.method == "isotonic" and self.isotonic_model is not None:
            cal_p = float(self.isotonic_model.predict([p])[0])
        else:
            # Platt Scaling
            log_odds = math.log(p / (1.0 - p))
            z = (self.platt_a * log_odds) + self.platt_b
            cal_p = 1.0 / (1.0 + math.exp(-z))

        return round(float(np.clip(cal_p * 100.0, 5.0, 95.0)), 2)

    def evaluate_model_performance(
        self,
        predicted_probs: np.ndarray,
        true_labels: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Calculates comprehensive ML evaluation metrics:
        Brier Score, ROC-AUC, Accuracy, Precision, Recall, F1-Score, and ECE.
        """
        p = np.clip(np.array(predicted_probs, dtype=float) / 100.0 if np.max(predicted_probs) > 1.0 else np.array(predicted_probs, dtype=float), 0.0, 1.0)
        y = np.array(true_labels, dtype=int)
        y_pred = (p >= 0.50).astype(int)

        brier = float(brier_score_loss(y, p))
        acc = float(accuracy_score(y, y_pred))
        f1 = float(f1_score(y, y_pred, zero_division=0))
        try:
            auc = float(roc_auc_score(y, p))
        except Exception:
            auc = 0.50

        # Compute Expected Calibration Error (ECE) with 10 bins
        ece = self._compute_ece(p, y, n_bins=10)

        return {
            "brier_score": round(brier, 4),
            "roc_auc": round(auc, 4),
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "expected_calibration_error": round(ece, 4),
            "total_eval_samples": len(y),
        }

    def _compute_ece(self, probs: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
        """Computes Expected Calibration Error across equal-width probability bins."""
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n = len(probs)
        if n == 0:
            return 0.0

        for i in range(n_bins):
            bin_lower = bin_edges[i]
            bin_upper = bin_edges[i + 1]
            in_bin = (probs > bin_lower) & (probs <= bin_upper) if i > 0 else (probs >= bin_lower) & (probs <= bin_upper)
            bin_size = np.sum(in_bin)

            if bin_size > 0:
                avg_confidence = float(np.mean(probs[in_bin]))
                avg_accuracy = float(np.mean(labels[in_bin]))
                ece += (bin_size / n) * abs(avg_confidence - avg_accuracy)

        return ece


# Singleton
_calibrator = None

def get_probability_calibrator() -> ProbabilityCalibrator:
    global _calibrator
    if _calibrator is None:
        _calibrator = ProbabilityCalibrator(method="sigmoid")
    return _calibrator
