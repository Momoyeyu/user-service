#!/usr/bin/env python
"""Helper functions for test.sh script."""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET


def generate_coveragerc() -> None:
    """Parse cfg.yml and generate .coveragerc, output threshold to stdout."""
    try:
        import yaml
    except ImportError as e:
        raise SystemExit(f"missing yaml parser (PyYAML). import yaml failed: {e}")

    root_dir = os.environ["ROOT_DIR"]
    output_dir = os.environ.get("OUTPUT_DIR", os.path.join(root_dir, "output"))
    config_path = os.environ.get("TEST_CONFIG_PATH", os.path.join(root_dir, "tests", "cfg.yml"))

    # Default config
    threshold = 80.0
    include_patterns = ["src/**/service.py", "src/middleware/**"]
    exclude_patterns = ["src/**/__init__.py"]

    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        cov_cfg = cfg.get("coverage") or {}

        def as_list(value: str | list[str] | None) -> list[str]:
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            return list(value)

        threshold = float(cov_cfg.get("threshold", 80))
        if cov_cfg.get("include"):
            include_patterns = as_list(cov_cfg.get("include"))
        if cov_cfg.get("exclude"):
            exclude_patterns = as_list(cov_cfg.get("exclude"))

    # Expand patterns to get actual file paths
    def expand(patterns: list[str]) -> set[str]:
        files: set[str] = set()
        for pattern in patterns:
            abs_pattern = os.path.join(root_dir, pattern)
            for path in glob.glob(abs_pattern, recursive=True):
                path = os.path.normpath(path)
                if os.path.isfile(path) and path.endswith(".py"):
                    rel_path = os.path.relpath(path, root_dir)
                    files.add(rel_path)
        return files

    include_files = expand(include_patterns)
    exclude_files = expand(exclude_patterns)
    selected_files = sorted(include_files - exclude_files)

    # Generate .coveragerc with explicit source files
    coveragerc_path = os.path.join(output_dir, ".coveragerc")
    os.makedirs(output_dir, exist_ok=True)

    coverage_data_file = os.path.join(output_dir, ".coverage")

    with open(coveragerc_path, "w") as f:
        f.write("[run]\n")
        f.write("source = src\n")
        f.write("branch = False\n")
        f.write(f"data_file = {coverage_data_file}\n")
        f.write("\n[report]\n")
        if selected_files:
            f.write("include =\n")
            for file_path in selected_files:
                f.write(f"    {file_path}\n")
        f.write("\nomit =\n")
        f.write("    */__init__.py\n")
        f.write("    */test_*.py\n")

    # Output threshold
    print(threshold)


def calc_success_rate() -> None:
    """Calculate test success rate from pytest output (read from stdin)."""
    text = sys.stdin.read()
    ansi = re.compile(r"\x1b\[[0-9;]*m")

    def norm(s: str) -> str:
        return ansi.sub("", s.replace("\r", "").strip())

    summary = [
        norm(line)
        for line in text.splitlines()
        if re.match(r"^[0-9]+\s+(passed|failed|skipped|xfailed|xpassed|error|errors)\b", norm(line))
    ]

    if not summary:
        print("0/0 (0.00%)")
        return

    line = summary[-1]
    items = re.findall(r"([0-9]+)\s+(passed|failed|errors?|skipped|xfailed|xpassed)\b", line)
    counts: dict[str, int] = {}
    for n, k in items:
        counts[k] = counts.get(k, 0) + int(n)

    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0)
    errors = counts.get("error", 0) + counts.get("errors", 0)
    total = passed + failed + errors
    rate = (passed / total * 100.0) if total else 0.0
    print(f"{passed}/{total} ({rate:.2f}%)")


def extract_coverage(output_dir: str) -> None:
    """Extract coverage percentage from coverage.xml."""
    xml_path = os.path.join(output_dir, "coverage.xml")
    if not os.path.exists(xml_path):
        print("N/A")
    else:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        line_rate = root.attrib.get("line-rate", "0")
        coverage = float(line_rate) * 100.0
        print(f"{coverage:.2f}%")


def check_coverage_threshold(output_dir: str, threshold: float) -> None:
    """Check if coverage meets the threshold."""
    xml_path = os.path.join(output_dir, "coverage.xml")

    if not os.path.exists(xml_path):
        print("Warning: coverage.xml not found, skipping coverage check")
        return

    tree = ET.parse(xml_path)
    root = tree.getroot()
    line_rate = root.attrib.get("line-rate")
    if line_rate is None:
        print("Warning: coverage.xml missing line-rate")
        return

    coverage = float(line_rate) * 100.0
    if coverage + 1e-9 < threshold:
        print(f"Coverage gate FAILED: {coverage:.2f}% < {threshold:.2f}%")
        sys.exit(1)
    else:
        print(f"Coverage gate PASSED: {coverage:.2f}% >= {threshold:.2f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test helper utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-coveragerc command
    subparsers.add_parser("generate-coveragerc", help="Generate .coveragerc and output threshold")

    # calc-success-rate command
    subparsers.add_parser("calc-success-rate", help="Calculate test success rate from stdin")

    # extract-coverage command
    extract_parser = subparsers.add_parser("extract-coverage", help="Extract coverage percentage")
    extract_parser.add_argument("output_dir", help="Output directory containing coverage.xml")

    # check-coverage-threshold command
    check_parser = subparsers.add_parser("check-coverage-threshold", help="Check coverage threshold")
    check_parser.add_argument("output_dir", help="Output directory containing coverage.xml")
    check_parser.add_argument("threshold", type=float, help="Coverage threshold percentage")

    args = parser.parse_args()

    if args.command == "generate-coveragerc":
        generate_coveragerc()
    elif args.command == "calc-success-rate":
        calc_success_rate()
    elif args.command == "extract-coverage":
        extract_coverage(args.output_dir)
    elif args.command == "check-coverage-threshold":
        check_coverage_threshold(args.output_dir, args.threshold)


if __name__ == "__main__":
    main()
