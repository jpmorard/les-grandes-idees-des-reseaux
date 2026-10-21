"""Deterministic rare-event classification with a sealed final test split."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from statistics import fmean


@dataclass(frozen=True)
class Sample:
    sample_id: str
    feature: float
    incident: int


@dataclass(frozen=True)
class ScoreModel:
    normal_mean: float
    incident_mean: float
    scale: float

    def score(self, feature: float) -> float:
        midpoint = (self.normal_mean + self.incident_mean) / 2.0
        direction = 1.0 if self.incident_mean >= self.normal_mean else -1.0
        logit = direction * (feature - midpoint) / self.scale
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, logit))))


def generate_split(
    name: str,
    *,
    seed: int,
    size: int,
    incident_rate: float = 0.02,
) -> list[Sample]:
    """Create an identified synthetic split without customer or field data."""

    if not 0.0 < incident_rate < 0.5:
        raise ValueError("incident_rate must be between zero and one half")
    if size < 100:
        raise ValueError("size must be at least 100")
    rng = random.Random(seed)
    samples: list[Sample] = []
    for index in range(size):
        incident = int(rng.random() < incident_rate)
        mean = 2.4 if incident else 0.0
        feature = rng.gauss(mean, 1.0)
        samples.append(Sample(f"{name}-{index:05d}", feature, incident))
    if not any(sample.incident for sample in samples):
        raise RuntimeError(f"{name} contains no positive example")
    return samples


def fit_score_model(training: list[Sample]) -> ScoreModel:
    """Fit only class centroids; threshold selection is deliberately separate."""

    normal = [sample.feature for sample in training if not sample.incident]
    incidents = [sample.feature for sample in training if sample.incident]
    if not normal or not incidents:
        raise ValueError("both classes are required for training")
    normal_mean = fmean(normal)
    incident_mean = fmean(incidents)
    residuals = [
        sample.feature - (incident_mean if sample.incident else normal_mean)
        for sample in training
    ]
    scale = math.sqrt(fmean(residual * residual for residual in residuals))
    return ScoreModel(normal_mean, incident_mean, max(scale, 1e-9))


def confusion_counts(
    samples: list[Sample], model: ScoreModel, threshold: float
) -> dict[str, int]:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between zero and one")
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for sample in samples:
        predicted = int(model.score(sample.feature) >= threshold)
        if predicted and sample.incident:
            counts["tp"] += 1
        elif predicted:
            counts["fp"] += 1
        elif sample.incident:
            counts["fn"] += 1
        else:
            counts["tn"] += 1
    return counts


def classification_metrics(counts: dict[str, int]) -> dict[str, float]:
    tp, fp, tn, fn = (counts[key] for key in ("tp", "fp", "tn", "fn"))
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": (tp + tn) / total,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
    }


def weighted_error_cost(
    counts: dict[str, int], *, false_positive_cost: float, false_negative_cost: float
) -> float:
    return (
        false_positive_cost * counts["fp"]
        + false_negative_cost * counts["fn"]
    )


def select_threshold(
    validation: list[Sample],
    model: ScoreModel,
    *,
    candidates: tuple[float, ...] = tuple(index / 100 for index in range(5, 96, 5)),
    false_positive_cost: float = 1.0,
    false_negative_cost: float = 12.0,
) -> dict[str, float]:
    """Choose a threshold on validation data only."""

    rows: list[tuple[float, float, float]] = []
    for threshold in candidates:
        counts = confusion_counts(validation, model, threshold)
        cost = weighted_error_cost(
            counts,
            false_positive_cost=false_positive_cost,
            false_negative_cost=false_negative_cost,
        )
        rows.append((cost, -classification_metrics(counts)["recall"], threshold))
    cost, negative_recall, threshold = min(rows)
    return {
        "threshold": threshold,
        "validation_cost": cost,
        "validation_recall": -negative_recall,
        "false_positive_cost": false_positive_cost,
        "false_negative_cost": false_negative_cost,
    }


def _split_digest(samples: list[Sample]) -> str:
    payload = [asdict(sample) for sample in samples]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _evaluate(
    samples: list[Sample], model: ScoreModel, threshold: float
) -> dict[str, object]:
    counts = confusion_counts(samples, model, threshold)
    return {
        "threshold": threshold,
        "counts": counts,
        "metrics": classification_metrics(counts),
    }


def run_experiment() -> dict[str, object]:
    """Fit on train, select on validation, and open the final test once."""

    training = generate_split("train", seed=101, size=2_000)
    validation = generate_split("validation", seed=211, size=1_200)
    final_test = generate_split("test", seed=307, size=1_200)
    identifiers = [
        {sample.sample_id for sample in split}
        for split in (training, validation, final_test)
    ]
    if identifiers[0] & identifiers[1] or identifiers[0] & identifiers[2]:
        raise AssertionError("training overlaps another split")
    if identifiers[1] & identifiers[2]:
        raise AssertionError("validation overlaps the final test")

    model = fit_score_model(training)
    choice = select_threshold(validation, model)
    threshold = float(choice["threshold"])
    final_result = _evaluate(final_test, model, threshold)
    naive_result = _evaluate(final_test, model, 0.5)
    return {
        "experiment_id": "rare-network-incident-threshold-v1",
        "evidence_scope": {
            "kind": "deterministic_synthetic",
            "production_proof": False,
        },
        "split_contract": {
            "training_role": "fit_score_model",
            "validation_role": "select_threshold",
            "test_role": "single_final_evaluation",
            # Declared protocol, not an instrumented count of test accesses.
            "test_open_count": 1,
            "sizes": {
                "training": len(training),
                "validation": len(validation),
                "test": len(final_test),
            },
            "sha256": {
                "training": _split_digest(training),
                "validation": _split_digest(validation),
                "test": _split_digest(final_test),
            },
        },
        "model": asdict(model),
        "selection": choice,
        "final_test": final_result,
        "naive_threshold_reference": naive_result,
    }


if __name__ == "__main__":
    print(json.dumps(run_experiment(), indent=2, sort_keys=True))
