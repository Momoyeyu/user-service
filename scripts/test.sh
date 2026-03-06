#!/usr/bin/env bash
# Run all tests (unit + integration) with coverage and success rate statistics
# Configuration is read from tests/cfg.yml
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export ROOT_DIR
cd "$ROOT_DIR"

OUTPUT_DIR="$ROOT_DIR/output"
mkdir -p "$OUTPUT_DIR"

export COVERAGE_FILE="$OUTPUT_DIR/.coverage"

TEST_CONFIG_PATH="${TEST_CONFIG_PATH:-$ROOT_DIR/tests/cfg.yml}"
export TEST_CONFIG_PATH
export OUTPUT_DIR

# Parse cfg.yml and generate .coveragerc
COVERAGE_THRESHOLD="$(uv run python "$SCRIPT_DIR/test_helper.py" generate-coveragerc)"
export COVERAGE_THRESHOLD

# Coverage config file location
COVERAGERC_PATH="$OUTPUT_DIR/.coveragerc"

# Build coverage arguments
SERVICE_COV_ARGS=(
    "--cov=src"
    "--cov-config=$COVERAGERC_PATH"
)

# Helper function to calculate success rate
calc_success_rate() {
    local output="$1"
    uv run python "$SCRIPT_DIR/test_helper.py" calc-success-rate <<< "$output"
}

echo "========================================"
echo "Running Unit Tests"
echo "========================================"

set +e
UNIT_OUTPUT="$(uv run pytest tests/unit -q \
    "${SERVICE_COV_ARGS[@]}" \
    --cov-report=term-missing \
    --cov-report=xml:"$OUTPUT_DIR/coverage.xml" \
    --junitxml="$OUTPUT_DIR/junit-unit.xml" 2>&1)"
UNIT_STATUS=$?
set -e

echo "$UNIT_OUTPUT"
echo "$UNIT_OUTPUT" > "$OUTPUT_DIR/pytest-unit.log"

UNIT_RATE=$(calc_success_rate "$UNIT_OUTPUT")

echo ""
echo "========================================"
echo "Running Integration Tests"
echo "========================================"

set +e
INT_OUTPUT="$(uv run pytest tests/integration -q \
    --junitxml="$OUTPUT_DIR/junit-integration.xml" 2>&1)"
INT_STATUS=$?
set -e

echo "$INT_OUTPUT"
echo "$INT_OUTPUT" > "$OUTPUT_DIR/pytest-integration.log"

INT_RATE=$(calc_success_rate "$INT_OUTPUT")

echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"

# Extract coverage percentage
COVERAGE_PCT=$(uv run python "$SCRIPT_DIR/test_helper.py" extract-coverage "$OUTPUT_DIR")

echo "Unit Tests:        $UNIT_RATE"
echo "Unit Coverage:     $COVERAGE_PCT (threshold: ${COVERAGE_THRESHOLD}%)"
echo "Integration Tests: $INT_RATE"

# Check coverage threshold
uv run python "$SCRIPT_DIR/test_helper.py" check-coverage-threshold "$OUTPUT_DIR" "$COVERAGE_THRESHOLD"

# Exit with failure if any tests failed
if [[ $UNIT_STATUS -ne 0 ]]; then
    echo ""
    echo "Unit tests FAILED"
    exit $UNIT_STATUS
fi

if [[ $INT_STATUS -ne 0 ]]; then
    echo ""
    echo "Integration tests FAILED"
    exit $INT_STATUS
fi

# Clean up temporary coverage files
rm -f "$ROOT_DIR/.coverage" 2>/dev/null || true
rm -f "$OUTPUT_DIR/.coverage" 2>/dev/null || true

echo ""
echo "All tests PASSED"
