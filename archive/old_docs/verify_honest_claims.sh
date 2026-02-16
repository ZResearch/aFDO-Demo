#!/bin/bash
# Verify no false claims in documentation

echo "Checking for problematic claims..."
echo ""

ERRORS=0

# Check for "no orchestrator" claims
echo "1. Checking for 'no orchestrator' claims..."
if grep -r "no orchestrator\|no central orchestrator" docs/ README.md ARCHITECTURE.md 2>/dev/null | grep -v "NOT" | grep -v "no longer" | grep -v "They are NOT" | grep -v "no global"; then
    echo "   ❌ Found 'no orchestrator' claim"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No problematic 'no orchestrator' claims"
fi

echo ""

# Check for "pure P2P" claims
echo "2. Checking for 'pure P2P' claims..."
if grep -r "pure P2P\|pure peer-to-peer\|true peer-to-peer" docs/ README.md ARCHITECTURE.md 2>/dev/null | grep -v "NOT" | grep -v "neither" | grep -v "is NOT" | grep -v "Not claimed"; then
    echo "   ❌ Found 'pure P2P' claim"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No problematic 'pure P2P' claims"
fi

echo ""

# Check for "emergent workflow" claims
echo "3. Checking for 'emergent workflow' claims..."
if grep -r "emergent workflow\|emergent coordination" docs/ README.md ARCHITECTURE.md 2>/dev/null | grep -v "NOT" | grep -v "without" | grep -v "Fully Emergent" | grep -v "Not claimed"; then
    echo "   ❌ Found 'emergent workflow' claim"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No problematic 'emergent workflow' claims"
fi

echo ""

# Check for "self-organizing" claims
echo "4. Checking for 'self-organizing' claims..."
if grep -r "self-organizing" docs/ README.md ARCHITECTURE.md 2>/dev/null; then
    echo "   ❌ Found 'self-organizing' claim"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ No 'self-organizing' claims"
fi

echo ""
echo "=================================================="

if [ $ERRORS -eq 0 ]; then
    echo "✅ All checks passed - No false claims found"
    echo "=================================================="
    exit 0
else
    echo "❌ Found $ERRORS problematic claims"
    echo "=================================================="
    exit 1
fi
