"""CLI for importing two independent human-review label files."""

from __future__ import annotations

import argparse

from industrialops.evaluation.v07.human_calibration import (
    calculate_two_reviewer_agreement,
    load_review_labels,
    write_agreement_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate v0.7 two-reviewer agreement")
    parser.add_argument("--labels", required=True)
    parser.add_argument("--reviewer-a", required=True)
    parser.add_argument("--reviewer-b", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = calculate_two_reviewer_agreement(
        load_review_labels(args.labels), reviewer_a=args.reviewer_a, reviewer_b=args.reviewer_b
    )
    write_agreement_report(args.output, result.as_dict())
    print(result.as_dict())


if __name__ == "__main__":
    main()
