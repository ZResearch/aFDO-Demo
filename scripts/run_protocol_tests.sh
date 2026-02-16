#!/bin/bash

echo "========================================="
echo "Running Protocol Tests"
echo "========================================="
echo

echo "Test 1: Negotiation Protocol"
echo "-----------------------------------------"
python3 tests/test_negotiation_protocol.py
if [ $? -ne 0 ]; then
    echo "❌ Negotiation protocol tests failed"
    exit 1
fi
echo

echo "Test 2: Workflow Engine"
echo "-----------------------------------------"
python3 tests/test_workflow_engine.py
if [ $? -ne 0 ]; then
    echo "❌ Workflow engine tests failed"
    exit 1
fi
echo

echo "Test 3: End-to-End Integration"
echo "-----------------------------------------"
python3 tests/test_end_to_end.py
if [ $? -ne 0 ]; then
    echo "❌ Integration test failed"
    exit 1
fi
echo

echo "========================================="
echo "✅ ALL TESTS PASSED"
echo "========================================="
