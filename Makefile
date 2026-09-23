# claude-code-respeak: the repo's checks (conventions section 5).
# PYTHON is the pyenv virtualenv .python-version declares; override on the command line. When
# its python3 exists it is found by path, with no process: the pyenv shim takes a lock that
# stalled every make under load (review R6, T2). `lint` checks the name against .python-version.
PYENV_ROOT ?= $(HOME)/.pyenv
VENV = claude-code-respeak
VENV_PYTHON = $(PYENV_ROOT)/versions/$(VENV)/bin/python3
ifeq ($(origin PYTHON),undefined)
PYTHON := $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(shell python3 -c 'import sys; print(sys.executable)'))
endif
export PYTHON
# Its bin dir first on PATH, so every recipe, and every hook a suite runs, skips the shim.
export PATH := $(patsubst %/,%,$(dir $(PYTHON))):$(PATH)
# The claude CLI `install` and `validate` run; the install suite passes a fake here.
CLAUDE ?= claude

.PHONY: check test lint doclint hygiene readme readme-fresh validate doctor install

check: test lint doclint hygiene readme-fresh validate

# Every spawn here is bounded: respeak-deadline.sh runs it in its own process group and kills
# the group at the wall clock (exit 124), so a hung suite or a slow claude fails the target.
DEADLINE = bash plugin/scripts/respeak-deadline.sh

# The bash suites run the hooks, which find `python3` on PATH: the export above puts $(PYTHON) first.
test:
	$(DEADLINE) 120 $(PYTHON) -m unittest discover tests </dev/null
	@set -e; for t in tests/*.sh; do echo "== $$t"; $(DEADLINE) 120 bash "$$t" </dev/null; done

lint:
	$(PYTHON) -m compileall -q scripts plugin/scripts tests
	$(PYTHON) -c 'import sys; assert sys.version_info >= (3, 12)'
	@[ "$$(cat .python-version)" = "$(VENV)" ] || { echo "lint: .python-version is not $(VENV); update VENV in the Makefile"; exit 2; }

doclint:
	$(PYTHON) scripts/doclint
	bash plugin/scripts/respeak-check.sh

# scripts/hygiene and scripts/doclint are byte-identical to claude-code-session's (conventions
# section 6); a re-sync moves the files and these pins together. The copy source is the
# claude-code-session checkout beside this one, found from `git rev-parse --git-common-dir`
# (the main checkout's .git, whose parent's parent holds both repos), never a home path.
HYGIENE_SHA = d9e99149ec88c943c871795a2d0638a40dd344d0f5a4cac19be8fc02b86f9aa0
DOCLINT_SHA = 4318bc912b4fd57ad111f037dab13f11fb137255515a23f215f2a59c10b1e81a

hygiene:
	@printf '%s  %s\n' $(HYGIENE_SHA) scripts/hygiene $(DOCLINT_SHA) scripts/doclint | shasum -a 256 -c --status || { echo "hygiene: scripts/hygiene or scripts/doclint differ from the canonical copies (conventions section 6)"; exit 2; }
	$(PYTHON) scripts/hygiene

# README.md is rendered from design/readme/source.md (conventions section 6); edit the source.
# The render is an editorial pass, not a summary: design/readme/contract.txt is its contract, and
# scripts/readme-render.sh moves it over README.md only after respeak-verify-edit.py passes.
readme:
	bash scripts/readme-render.sh

readme-fresh:
	bash scripts/readme-fresh.sh

validate:
	@if command -v $(CLAUDE) >/dev/null 2>&1; then $(DEADLINE) 60 sh -c '$(CLAUDE) plugin validate plugin/ && $(CLAUDE) plugin validate .' </dev/null; \
	else echo "validate: skipped, no $(CLAUDE) on PATH"; fi

# One line per check: python, claude, marketplace, plugin, provider, config (conventions section 3).
doctor:
	bash plugin/scripts/respeak-doctor.sh

# Install the plugin from THIS checkout (conventions section 2). Adds the marketplace when absent,
# updates it when it already points here, and never removes a registration: any other source is
# printed with the two commands the owner would run, and the target exits 2.
install:
	@command -v $(CLAUDE) >/dev/null 2>&1 || { echo "install: no claude CLI at CLAUDE=$(CLAUDE); set CLAUDE=/path/to/claude"; exit 2; }
	@src="$$($(CLAUDE) plugin marketplace list --json | $(PYTHON) -c 'import json,sys; m=[m for m in json.load(sys.stdin) if m.get("name")=="claude-code-respeak"]; print(m[0].get("path") or m[0].get("repo") or m[0].get("url") or m[0].get("source") if m else "")')" || exit 2; \
	if [ -z "$$src" ]; then \
	  $(CLAUDE) plugin marketplace add "$(CURDIR)" && $(CLAUDE) plugin install respeak@claude-code-respeak; \
	elif [ "$$src" = "$(CURDIR)" ]; then \
	  $(CLAUDE) plugin marketplace update claude-code-respeak && $(CLAUDE) plugin update respeak@claude-code-respeak; \
	else \
	  echo "install: marketplace claude-code-respeak comes from $$src, not $(CURDIR)"; \
	  echo "install: to install from this checkout, run:"; \
	  echo "  claude plugin marketplace remove claude-code-respeak"; \
	  echo "  make install"; \
	  exit 2; \
	fi
