#!/bin/bash
# XActions Smoke Test - Verify fresh clone works in under 5 minutes
# Run from project root: ./scripts/smoke-test.sh

echo "=== XActions Smoke Test ==="
echo "Verifying fresh clone setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

# 1. Check Node.js version
echo "--- Step1: Environment ---"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        pass "Node.js >= 18 (found $NODE_VERSION)"
    else
        fail "Node.js >= 18 required (found $NODE_VERSION)"
    fi
else
    fail "Node.js not found"
fi

# 2. Install dependencies (if needed)
echo ""
echo "--- Step 2: Dependencies ---"
START=$(date +%s)
if [ -d "node_modules" ]; then
    pass "node_modules exists (dependencies installed)"
else
    echo "Running npm install..."
    if npm install --prefer-offline --no-audit --progress=false 2>&1 | grep -E "(added|removed|changed|audited)" | tail -1; then
        pass "npm install completed"
    else
        fail "npm install failed"
    fi
fi
END=$(date +%s)
echo "Time: $((END - START))s"

# 3. Verify CLI entry point
echo ""
echo "--- Step 3: CLI ---"
HELP_OUTPUT=$(node src/cli/index.js --help 2>&1 || true)
if echo "$HELP_OUTPUT" | grep -q "Commands:"; then
    CMD_COUNT=$(echo "$HELP_OUTPUT" | grep -c "xactions" || echo "50+")
    pass "CLI --help works ($CMD_COUNT commands available)"
else
    fail "CLI --help failed"
fi

VERSION=$(node src/cli/index.js --version 2>&1 || echo "unknown")
if [ "$VERSION" != "unknown" ]; then
    pass "CLI --version: $VERSION"
else
    fail "CLI --version failed"
fi

# 4. Run tests
echo ""
echo "--- Step 4: Tests ---"
START=$(date +%s)
TEST_OUTPUT=$(npm test -- --run 2>&1 || true)
END=$(date +%s)
echo "Time: $((END - START))s"

if echo "$TEST_OUTPUT" | grep -q "passed"; then
    PASSED=$(echo "$TEST_OUTPUT" | grep -o "[0-9]* passed" | head -1 || echo "some")
    pass "Tests: $PASSED"
else
    # Check for partial success
    if echo "$TEST_OUTPUT" | grep -q "failed"; then
        fail "Some tests failed"
    else
        fail "Test run failed"
    fi
fi

# 5. Verify MCP server
echo ""
echo "--- Step 5: MCP Server ---"
if [ -f "src/mcp/server.js" ]; then
    if node --check src/mcp/server.js 2>/dev/null; then
        pass "MCP server.js parses correctly"
    else
        fail "MCP server.js has syntax errors"
    fi
else
    fail "MCP server.js not found"
fi

# Summary
echo ""
echo "=== Summary ==="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
TOTAL=$((PASS + FAIL))

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}✓ Smoke test passed!${NC}"
    echo "XActions is ready to use."
    echo ""
    echo "Quick start:"
    echo "  node src/cli/index.js --help"
    echo "  node src/cli/index.js login"
    exit 0
else
    echo -e "${YELLOW}⚠ Some checks failed (${FAIL}/${TOTAL})${NC}"
    echo "Core functionality may still work. Review errors above."
    exit 1
fi