# claude-code-respeak: the repo's checks (conventions section 5).
# PYTHON is the pyenv virtualenv .python-version declares; override on the command line.
PYTHON ?= $(shell python3 -c 'import sys; print(sys.executable)')
export PYTHON

.PHONY: check test lint doclint hygiene validate

check: test lint doclint hygiene validate

# The bash suites run the hooks, which find `python3` on PATH: put $(PYTHON) first.
test:
	$(PYTHON) -m unittest discover tests
	@set -e; for t in tests/*.sh; do echo "== $$t"; PATH="$(dir $(PYTHON)):$$PATH" bash "$$t"; done

lint:
	$(PYTHON) -m compileall -q scripts tests
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 12)'

doclint:
	$(PYTHON) scripts/doclint
	bash scripts/respeak-check.sh

hygiene:
	$(PYTHON) scripts/hygiene

validate:
	@if command -v claude >/dev/null 2>&1; then claude plugin validate .; \
	else echo "validate: skipped, no claude on PATH"; fi
