#!/usr/bin/env bash

FAILED_TESTS=0

run_test() {
    local command="$1"
    local expected_code="${2:-0}"

    eval "$command" 
    local actual_code=$?

    if [ "$actual_code" -eq "$expected_code" ]; then
        echo "✅ Test passed: '$command' (Exit code: $actual_code)"
        return 0
    else
        echo "❌ Test failed: '$command'"
        echo "ℹ️    Expected exit code: $expected_code"
        echo "ℹ️    Actual exit code: $actual_code"
        return 1
    fi
}

for manifest in tests/iiif_manifests/*.json; do
    echo "ℹ️  Testing import of manifest: $manifest"
    if ! run_test "blender --background --online-mode --python tests/setup_logging.py --python run_blender_with_plugin.py -- '$manifest'"; then
        ((FAILED_TESTS++))
    fi
done

if [ $FAILED_TESTS -gt 0 ]; then
    echo "❌ $FAILED_TESTS test(s) failed"
    exit 1
else
    echo "✅ All tests passed"
    exit 0
fi
