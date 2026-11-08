"""
Rubric loading, validation and scoring.

A rubric is a YAML file (see rubrics/) with weighted dimensions, each with
anchored score levels. This module validates the structure, computes weighted
scores, and applies "gate" dimensions (e.g. safety) that cap the overall score.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import yaml


@dataclass
class Dimension:
    key: str
    name: str
    weight: float
    description: str
    anchors: dict[int, str]
    gate: bool = False            # if True, a low score here caps the total
    gate_threshold: int | None = None
    gate_cap: float | None = None


@dataclass
class Rubric:
    name: str
    version: str
    scale_min: int
    scale_max: int
    dimensions: list[Dimension]
    task_type: str = ""
    instructions: str = ""
    metadata: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- scoring
    def weighted_score(self, scores: dict[str, int | float]) -> float:
        """Weighted mean of dimension scores on the rubric's scale, with gates applied."""
        total_w = sum(d.weight for d in self.dimensions)
        missing = [d.key for d in self.dimensions if d.key not in scores]
        if missing:
            raise ValueError(f"missing scores for dimensions: {missing}")
        out = sum(d.weight * float(scores[d.key]) for d in self.dimensions) / total_w
        for d in self.dimensions:
            if d.gate and d.gate_threshold is not None and scores[d.key] <= d.gate_threshold:
                out = min(out, d.gate_cap if d.gate_cap is not None else float(self.scale_min))
        return out

    def normalized_score(self, scores: dict[str, int | float]) -> float:
        """Weighted score rescaled to 0-1."""
        s = self.weighted_score(scores)
        return (s - self.scale_min) / (self.scale_max - self.scale_min)

    def validate_scores(self, scores: dict[str, int | float]) -> list[str]:
        """Return a list of problems (empty if the score record is valid)."""
        problems = []
        for d in self.dimensions:
            if d.key not in scores:
                problems.append(f"{d.key}: missing")
                continue
            v = scores[d.key]
            if not isinstance(v, (int, float)) or v != int(v):
                problems.append(f"{d.key}: score must be an integer, got {v!r}")
            elif not self.scale_min <= v <= self.scale_max:
                problems.append(f"{d.key}: {v} outside {self.scale_min}-{self.scale_max}")
        extra = set(scores) - {d.key for d in self.dimensions}
        if extra:
            problems.append(f"unknown dimensions: {sorted(extra)}")
        return problems

    # ---------------------------------------------------------------- export
    def to_markdown(self) -> str:
        lines = [f"# {self.name} (v{self.version})", "", f"*Task type:* {self.task_type}  ",
                 f"*Scale:* {self.scale_min}–{self.scale_max}", "", self.instructions.strip(), ""]
        for d in self.dimensions:
            gate = " · **GATE**" if d.gate else ""
            lines += [f"## {d.name} (weight {d.weight:g}){gate}", "", d.description.strip(), "",
                      "| Score | Anchor |", "|---|---|"]
            for k in sorted(d.anchors):
                lines.append(f"| {k} | {d.anchors[k].strip()} |")
            lines.append("")
        return "\n".join(lines)


# -------------------------------------------------------------------- loading

REQUIRED_TOP = {"name", "version", "scale", "dimensions"}


def load_rubric(path: str) -> Rubric:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    problems = validate_rubric_dict(raw)
    if problems:
        raise ValueError(f"invalid rubric {os.path.basename(path)}:\n  - " + "\n  - ".join(problems))
    dims = []
    for d in raw["dimensions"]:
        gate = d.get("gate", {}) or {}
        dims.append(Dimension(
            key=d["key"], name=d["name"], weight=float(d.get("weight", 1.0)), description=d.get("description", ""),
            anchors={int(k): str(v) for k, v in d["anchors"].items()},
            gate=bool(gate), gate_threshold=gate.get("threshold"), gate_cap=gate.get("cap"),
        ))
    return Rubric(name=raw["name"], version=str(raw["version"]), scale_min=int(raw["scale"]["min"]),
                  scale_max=int(raw["scale"]["max"]), dimensions=dims, task_type=raw.get("task_type", ""),
                  instructions=raw.get("instructions", ""), metadata=raw.get("metadata", {}) or {})


def validate_rubric_dict(raw: dict) -> list[str]:
    """Structural checks. Returns a list of human-readable problems."""
    problems = []
    if not isinstance(raw, dict):
        return ["rubric must be a mapping"]
    for k in REQUIRED_TOP - set(raw):
        problems.append(f"missing top-level key: {k}")
    if problems:
        return problems
    lo, hi = raw["scale"].get("min"), raw["scale"].get("max")
    if not (isinstance(lo, int) and isinstance(hi, int) and lo < hi):
        problems.append("scale.min and scale.max must be integers with min < max")
        return problems
    keys = set()
    for i, d in enumerate(raw["dimensions"]):
        tag = f"dimensions[{i}]"
        for k in ("key", "name", "anchors"):
            if k not in d:
                problems.append(f"{tag}: missing '{k}'")
        if "key" in d:
            if d["key"] in keys:
                problems.append(f"{tag}: duplicate key '{d['key']}'")
            keys.add(d["key"])
        if "weight" in d and (not isinstance(d["weight"], (int, float)) or d["weight"] <= 0):
            problems.append(f"{tag}: weight must be a positive number")
        anchors = d.get("anchors") or {}
        expected = set(range(lo, hi + 1))
        got = {int(k) for k in anchors} if all(str(k).lstrip("-").isdigit() for k in anchors) else set()
        if got != expected:
            problems.append(f"{tag}: anchors must cover every level {lo}-{hi}; got {sorted(got)}")
        gate = d.get("gate")
        if gate and ("threshold" not in gate):
            problems.append(f"{tag}: gate needs a 'threshold'")
    return problems


def rubric_to_json(rubric: Rubric) -> str:
    return json.dumps({
        "name": rubric.name, "version": rubric.version, "scale": [rubric.scale_min, rubric.scale_max],
        "dimensions": [{"key": d.key, "name": d.name, "weight": d.weight, "gate": d.gate} for d in rubric.dimensions],
    }, indent=2)
