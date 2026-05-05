#!/bin/bash
# Run WebSocket Integration Tests with Live Backend

# Set environment variables for live backend testing
# These should be set in your environment or passed explicitly

if [ -z "$LIVE_INTERVIEW_BASE_URL" ]; then
    echo "ERROR: LIVE_INTERVIEW_BASE_URL not set"
    echo "Please set the following environment variables:"
    echo "  LIVE_INTERVIEW_BASE_URL              (e.g., http://localhost:8000)"
    echo "  LIVE_INTERVIEW_ADMIN_EMAIL           (e.g., admin@example.com)"
    echo "  LIVE_INTERVIEW_ADMIN_PASSWORD        (password)"
    echo "  LIVE_INTERVIEW_CANDIDATE_EMAIL       (e.g., candidate@example.com)"
    echo "  LIVE_INTERVIEW_CANDIDATE_PASSWORD    (password)"
    exit 1
fi

echo "Running WebSocket Integration Tests"
echo "===================================="
echo "Backend URL: $LIVE_INTERVIEW_BASE_URL"
echo ""

# Run pytest with WebSocket tests
pytest tests/integration/test_websocket_events.py -v -s \
    --tb=short \
    --log-cli-level=INFO
