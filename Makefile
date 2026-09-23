# claude-code-respeak: the repo's checks (conventions section 5).
# PYTHON is the pyenv virtualenv .python-version declares; override on the command line.
PYTHON ?= $(shell python3 -c 'import sys; print(sys.executable)')
export PYTHON

.PHONY: check test lint doclint hygiene readme readme-fresh validate doctor install

check: test lint doclint hygiene readme-fresh validate

# The bash suites run the hooks, which find `python3` on PATH: put $(PYTHON) first.
test:
	$(PYTHON) -m unittest discover tests
	@set -e; for t in tests/*.sh; do echo "== $$t"; PATH="$(dir $(PYTHON)):$$PATH" bash "$$t"; done

lint:
	$(PYTHON) -m compileall -q scripts plugin/scripts tests
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 12)'

doclint:
	$(PYTHON) scripts/doclint
	bash plugin/scripts/respeak-check.sh

# scripts/hygiene and scripts/doclint are byte-identical to claude-code-session's (conventions
# section 6); a re-sync moves the files and these pins together.
HYGIENE_SHA = d9e99149ec88c943c871795a2d0638a40dd344d0f5a4cac19be8fc02b86f9aa0
DOCLINT_SHA = 4318bc912b4fd57ad111f037dab13f11fb137255515a23f215f2a59c10b1e81a

hygiene:
	@printf '%s  %s\n' $(HYGIENE_SHA) scripts/hygiene $(DOCLINT_SHA) scripts/doclint | shasum -a 256 -c --status || { echo "hygiene: scripts/hygiene or scripts/doclint differ from the canonical copies (conventions section 6)"; exit 2; }
	$(PYTHON) scripts/hygiene

# README.md is rendered from design/readme/source.md (conventions section 6); edit the source.
# The render is an editorial pass, not a summary: respeak-verify-edit.py rejects any other change.
README_CONTRACT = This render is an editorial pass over a whole document, not a summary. Output the entire document, top to bottom. \
Keep byte-identical and in order: the HTML img line under the title, every heading, every fenced code block, every inline code span, \
every link with its target, every number, every list item, and every table row (same count, same order, same cells apart from prose). \
Change only prose sentences, to tighten them and clear style-gate hits; add no fact, drop no fact, add no section, add no code span. \
The output is checked with respeak-verify-edit.py against the source and rejected on any structural difference.

readme:
	@c="$$(mktemp)"; printf '%s\n' '$(README_CONTRACT)' > "$$c"; \
	bash plugin/scripts/respeak-render.sh --mode technical --source design/readme/source.md --out README.md --contract "$$c"; \
	rc=$$?; rm -f "$$c"; exit $$rc
	@$(PYTHON) plugin/scripts/respeak-verify-edit.py design/readme/source.md README.md || { git checkout -- README.md; exit 2; }
	bash scripts/readme-fresh.sh --stamp

readme-fresh:
	bash scripts/readme-fresh.sh

validate:
	@if command -v claude >/dev/null 2>&1; then claude plugin validate plugin/ && claude plugin validate .; \
	else echo "validate: skipped, no claude on PATH"; fi

# One line per check: python, claude, marketplace, plugin, provider, config (conventions section 3).
doctor:
	bash plugin/scripts/respeak-doctor.sh

# Install the plugin from THIS checkout (conventions section 2). Adds the marketplace when absent,
# updates it when it already points here, and never removes a registration: any other source is
# printed with the two commands the owner would run, and the target exits 2.
install:
	@src="$$(claude plugin marketplace list --json | $(PYTHON) -c 'import json,sys; m=[m for m in json.load(sys.stdin) if m.get("name")=="claude-code-respeak"]; print(m[0].get("path") or m[0].get("repo") or m[0].get("url") or m[0].get("source") if m else "")')" || exit 2; \
	if [ -z "$$src" ]; then \
	  claude plugin marketplace add "$(CURDIR)" && claude plugin install respeak@claude-code-respeak; \
	elif [ "$$src" = "$(CURDIR)" ]; then \
	  claude plugin marketplace update claude-code-respeak && claude plugin update respeak@claude-code-respeak; \
	else \
	  echo "install: marketplace claude-code-respeak comes from $$src, not $(CURDIR)"; \
	  echo "install: to install from this checkout, run:"; \
	  echo "  claude plugin marketplace remove claude-code-respeak"; \
	  echo "  make install"; \
	  exit 2; \
	fi
