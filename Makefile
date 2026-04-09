# CONFIGURATION
project_name=dce-tools
module_name=dcetools

.PHONY: dev
dev: venv
	${VPYTHON} ${SRC_ROOT}/launcher.py

.PHONY: release
release: exe
	mv -v "dist/${project_name}.exe" "dist/${project_name}-$(GIT_TAG).exe"

# IMPLEMENTATION

# Get GIT_TAG from environment variable, fallback to git command if not set
GIT_TAG ?= $(shell git describe --tags --abbrev=0 2>/dev/null || echo snapshot-$(date +'%Y-%m-%d'))

VPYTHON=venv/Scripts/python.exe

SRC_ROOT=.
MODULE_SRCS=$(shell /bin/find ${module_name} -type f -name '*.py')
SCRIPT_SRCS=$(wildcard ${SRC_ROOT}/*.py)
HOOK_SRCS=$(wildcard ${SRC_ROOT}/hooks/*)

TARGET_EXES=\
	dist/${project_name}.exe

# TARGET_EXES=\
# 	$(patsubst ${SRC_ROOT}/%.py,dist/${project_name}-%.exe,${SCRIPT_SRCS})

.PHONY: all
all: lint test exe

.PHONY: watch
watch:
	nodemon --watch ${module_name}/ -e "py" --exec make dev


# Check
.PHONY: docs
docs: Docs_CLI.md

Docs_CLI.md: venv autodoc.py launcher.py ${MODULE_SRCS}
	${VPYTHON} autodoc.py > $@

.PHONY: check
check: venv lint test

.PHONY: lint
lint: venv
	-${VPYTHON} -m mypy --install-types --non-interactive --check-untyped-defs --follow-untyped-imports ${SCRIPT_SRCS}
	-vulture ${SCRIPT_SRCS} ${MODULE_SRCS}

.PHONY: test
test: venv
	${VPYTHON} -m doctest ${SRC_ROOT}/*.py
	${VPYTHON} -c "import ${module_name}; import doctest; doctest.testmod(${module_name})"
	${VPYTHON} -m unittest

.PHONY: clean
clean:
	$(RM) -r venv/ \
		build/ \
		dist/ \
		.mypy_cache/ \
		${SRC_ROOT}/__pycache__ ${SRC_ROOT}/*/__pycache__

# Env
venv: venv/pyvenv.cfg
venv/pyvenv.cfg: pyproject.toml
	python3 -m venv ./venv
	${VPYTHON} -m pip install -e ".[dev]"

# Build
.PHONY: exe
exe: venv ${TARGET_EXES}

dist/${project_name}-%.exe: ${SRC_ROOT}/%.py ${MODULE_SRCS} ${SCRIPT_SRCS} ${HOOK_SRCS} Makefile
	mkdir -p dist build
# 	cp icon.png build/
	${VPYTHON} -m PyInstaller \
		--name $(basename $(notdir $@)) \
		--paths src \
		--onefile \
		--console \
		--additional-hooks-dir=hooks \
		--distpath dist \
		--workpath build \
		--specpath build \
		$<

# 		--icon "icon.png" \
# 		--add-data="icon.png:." \
