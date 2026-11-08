"""
Command-line interface.

    python -m llm_eval.cli report ANNOTATIONS.csv [--pairwise PAIRWISE.csv] [--out report.md]
    python -m llm_eval.cli validate-rubric rubrics/general_assistant_v1.yaml
    python -m llm_eval.cli rubric-md rubrics/general_assistant_v1.yaml > rubric.md
    python -m llm_eval.cli alpha ANNOTATIONS.csv [--dimension factual_accuracy] [--level ordinal]
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd

from .agreement import interpret_alpha, krippendorff_alpha
from .quality import to_wide
from .report import build_report
from .rubric import load_rubric


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="llm_eval")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("report", help="annotation quality report (Markdown)")
    r.add_argument("annotations")
    r.add_argument("--pairwise")
    r.add_argument("--out")
    r.add_argument("--title", default="Annotation quality report")

    v = sub.add_parser("validate-rubric", help="check a rubric YAML file")
    v.add_argument("rubric")

    m = sub.add_parser("rubric-md", help="render a rubric as Markdown")
    m.add_argument("rubric")

    a = sub.add_parser("alpha", help="Krippendorff's alpha for an annotations file")
    a.add_argument("annotations")
    a.add_argument("--dimension")
    a.add_argument("--level", default="ordinal", choices=["nominal", "ordinal", "interval"])

    args = ap.parse_args(argv)

    if args.cmd == "report":
        ann = pd.read_csv(args.annotations)
        pw = pd.read_csv(args.pairwise) if args.pairwise else None
        text = build_report(ann, pw, title=args.title)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"wrote {args.out}")
        else:
            print(text)
        return 0

    if args.cmd == "validate-rubric":
        try:
            rub = load_rubric(args.rubric)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        print(f"OK: {rub.name} v{rub.version} - {len(rub.dimensions)} dimensions, scale {rub.scale_min}-{rub.scale_max}, "
              f"gates: {[d.key for d in rub.dimensions if d.gate] or 'none'}")
        return 0

    if args.cmd == "rubric-md":
        print(load_rubric(args.rubric).to_markdown())
        return 0

    if args.cmd == "alpha":
        ann = pd.read_csv(args.annotations)
        wide = to_wide(ann, dimension=args.dimension)
        alpha = krippendorff_alpha(wide.T.to_numpy(), level=args.level)
        scope = args.dimension or "all dimensions"
        print(f"Krippendorff's alpha ({args.level}) for {scope}: {alpha:.3f}  -> {interpret_alpha(alpha)}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
