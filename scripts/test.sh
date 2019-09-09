#!/bin/sh

exec 1>&2

cd `git rev-parse --show-toplevel`

(cd bot; pytest)
PYTEST_EXIT_CODE=$?
(cd web-client; npm run --silent test)
JSTEST_EXIT_CODE=$?

if [ $PYTEST_EXIT_CODE -ne 0 ] || [ $JSTEST_EXIT_CODE -ne 0 ]; then
    exit 1
fi

echo All tests completed successfully
exit 0
