# claude-code-respeak: the repo's checks (conventions section 5).
# PYTHON is the pyenv virtualenv .python-version declares; override on the command line.
PYTHON ?= $(shell python3 -c 'import sys; print(sys.executable)')
export PYTHON

.PHONY: check test lint doclint hygiene readme readme-fresh validate

check: test lint doclint hygiene readme-fresh validate

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

# README.md is rendered from design/readme/source.md (conventions section 6); edit the source.
readme:
	bash scripts/respeak-render.sh --mode technical --source design/readme/source.md --out README.md
	@$(PYTHON) scripts/respeak-verify-edit.py design/readme/source.md README.md || { git checkout -- README.md; exit 2; }
	bash scripts/readme-fresh.sh --stamp

readme-fresh:
	bash scripts/readme-fresh.sh

validate:
	@if command -v claude >/dev/null 2>&1; then claude plugin validate .; \
	else echo "validate: skipped, no claude on PATH"; fi
