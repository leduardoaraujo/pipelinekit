# PipelineKit Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Reorganize the existing ForgeFlow Python library around composable pipeline primitives and migrate its public identity to PipelineKit.

**Architecture:** Keep one distributable Python package, with pipelinekit.core providing stable contracts and sources, transforms, destinations, and pipeline providing the main data-flow components. Keep CLI, API, and Airflow integration outside the required core path and expose optional dependencies through extras. Preserve a documented compatibility surface for important existing ForgeFlow imports during the package transition.

**Tech Stack:** Python 3.11+, asyncio, Pydantic v2, pytest, pytest-asyncio, Ruff, mypy, Hatchling, MkDocs, GitHub Actions.

## Global Constraints

- Public project name: PipelineKit.
- Public Python package and CLI name: pipelinekit.
- Python requirement remains >=3.11.
- Core remains async-first.
- Airflow, HTTP API, and cloud integrations remain optional integrations.
- No dashboard, scheduler replacement, multi-package split, or unrelated new connectors in this migration.
- Structural changes preserve existing behavior unless required for the new module boundaries.
- Final documentation mentions ForgeFlow only in the migration guide and historical changelog entries.

---

### Task 1: Establish a clean migration baseline

**Files:**
- Modify: pyproject.toml, README.md, CHANGELOG.md, CONTRIBUTING.md
- Create: tests/test_package_baseline.py

**Interfaces:**
- Consumes: current forgeflow package, CLI entry point, and documented test commands.
- Produces: repeatable baseline before any module move.

- [ ] Step 1: Add baseline tests for current public behavior.

Create tests/test_package_baseline.py that imports forgeflow, asserts the current version is 0.1.0, and imports the current CLI entry point.

~~~python
def test_current_package_imports():
    import forgeflow
    assert forgeflow.__version__ == "0.1.0"

def test_current_cli_imports():
    from forgeflow.cli.main import cli
    assert cli is not None
~~~

- [ ] Step 2: Run pytest tests/test_package_baseline.py -v. Expected: both tests pass. If the CLI path differs, use the actual current entry point and record it in the implementation commit.

- [ ] Step 3: Inventory all legacy references with rg -n -i "forgeflow|forge flow|dataforge|data-forge" . and classify public references versus historical references.

- [ ] Step 4: Correct only stale metadata and instructions: clone URLs, repository links, test commands, and documentation paths. Do not rename the package in this task.

- [ ] Step 5: Run pytest -q and ruff check ., record any pre-existing failure, and commit with git commit -m "test: establish PipelineKit migration baseline".

---

### Task 2: Define domain-oriented package boundaries

**Files:**
- Create or modify: forgeflow/core/, forgeflow/sources/, forgeflow/transforms/, forgeflow/destinations/, forgeflow/pipeline/, forgeflow/config/
- Modify: tests/

**Interfaces:**
- Consumes: existing core, connectors, transformers, sinks, pipeline, and configuration modules.
- Produces: boundaries where sources, transforms, and destinations depend on contracts in core.

- [ ] Step 1: Add tests/test_package_boundaries.py for the intended public shape:

~~~python
from forgeflow.core import Source, Transform, Destination
from forgeflow.pipeline import Pipeline

def test_domain_exports_exist():
    assert Source is not None
    assert Transform is not None
    assert Destination is not None
    assert Pipeline is not None
~~~

Use existing equivalent class names if the repository uses different names; add the smallest aliases needed without rewriting implementations.

- [ ] Step 2: Run pytest tests/test_package_boundaries.py -v. Expected: failures identify missing boundary modules or exports.

- [ ] Step 3: Move implementations using these mappings: forgeflow/connectors to forgeflow/sources; forgeflow/transformers to forgeflow/transforms; forgeflow/sinks to forgeflow/destinations. Keep Airflow under forgeflow/airflow, API under forgeflow/api, and CLI under forgeflow/cli.

- [ ] Step 4: Update imports and add explicit __init__.py exports for each domain package. Optional integrations must not be imported by the core package.

- [ ] Step 5: Run pytest -q, ruff check ., and mypy forgeflow/. Expected: focused tests, full tests, lint, and type checking pass. Commit with git commit -m "refactor: organize pipeline components by domain".

---

### Task 3: Introduce the PipelineKit package namespace

**Files:**
- Create: pipelinekit/__init__.py, pipelinekit/core/, pipelinekit/sources/, pipelinekit/transforms/, pipelinekit/destinations/, pipelinekit/pipeline/, pipelinekit/config/, pipelinekit/integrations/
- Modify: forgeflow/__init__.py, pyproject.toml
- Create: tests/test_pipelinekit_namespace.py

**Interfaces:**
- Consumes: domain-oriented implementation from Task 2.
- Produces: canonical pipelinekit imports and a limited top-level ForgeFlow compatibility surface.

- [ ] Step 1: Add namespace tests:

~~~python
def test_pipelinekit_is_canonical_package():
    import pipelinekit
    assert pipelinekit.__version__ == "0.2.0"

def test_pipelinekit_core_exports():
    from pipelinekit.core import Source, Transform, Destination
    assert Source is not None
    assert Transform is not None
    assert Destination is not None

def test_legacy_top_level_import_is_available():
    import forgeflow
    assert forgeflow.__version__ == "0.2.0"
~~~

- [ ] Step 2: Run pytest tests/test_pipelinekit_namespace.py -v. Expected: the new package import fails before implementation.

- [ ] Step 3: Make pipelinekit the canonical implementation namespace. Update production imports to pipelinekit.* and do not leave production code depending on forgeflow.*.

- [ ] Step 4: Make forgeflow/__init__.py re-export the canonical version and documented top-level symbols. Document that compatibility covers top-level public imports unless a submodule alias has an explicit test.

- [ ] Step 5: In pyproject.toml change project name to pipelinekit, version to 0.2.0, update all canonical URLs, set the console script to pipelinekit = "pipelinekit.cli.main:cli", and fix the combined all extra so it does not recursively depend on itself.

- [ ] Step 6: Run pytest tests/test_pipelinekit_namespace.py -v, python -m build, and python -c "import pipelinekit; print(pipelinekit.__version__)". Expected: tests pass, build produces wheel and source archive, and the command prints 0.2.0.

- [ ] Step 7: Commit with git commit -m "refactor: introduce pipelinekit package namespace".

---

### Task 4: Migrate CLI, configuration, and optional integrations

**Files:**
- Modify: pipelinekit/cli/, pipelinekit/config/, pipelinekit/integrations/airflow/, pipelinekit/api/
- Create: tests/test_pipelinekit_cli.py
- Modify: tests/ files that import forgeflow

**Interfaces:**
- Consumes: canonical package from Task 3.
- Produces: CLI, YAML configuration, API, and Airflow integration using the canonical namespace.

- [ ] Step 1: Add a CLI test using Click's CliRunner:

~~~python
from click.testing import CliRunner
from pipelinekit.cli.main import cli

def test_pipelinekit_help():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "pipeline" in result.output.lower()
~~~

Add a temporary YAML configuration test using the repository's existing loader and schema.

- [ ] Step 2: Replace internal forgeflow imports with pipelinekit imports. Keep compatibility wrappers only at the old public boundary.

- [ ] Step 3: Verify core imports do not require Airflow, FastAPI, BigQuery, S3, MongoDB, or Snowflake. Run integration-specific tests with their extras separately.

- [ ] Step 4: Run pipelinekit --help, pytest tests/test_pipelinekit_cli.py -v, and pytest -q. Expected: help output succeeds and the full suite remains green.

- [ ] Step 5: Commit with git commit -m "refactor: migrate cli and integrations to pipelinekit".

---

### Task 5: Rewrite public documentation and migration guidance

**Files:**
- Modify: README.md, docs/index.md, docs/guides/getting-started.md, CONTRIBUTING.md, CHANGELOG.md
- Create or modify: docs/concepts/, docs/reference/, docs/examples/, docs/integrations/
- Create: docs/migration/forgeflow-to-pipelinekit.md

**Interfaces:**
- Consumes: canonical package and CLI from Tasks 3 and 4.
- Produces: coherent first-use documentation and an explicit migration path.

- [ ] Step 1: Document a minimal Python pipeline using the actual stable Pipeline, source, transform, and destination signatures.

- [ ] Step 2: Document installation and existing extras, including pip install pipelinekit and pip install "pipelinekit[postgres]". List only extras present in pyproject.toml.

- [ ] Step 3: Add the migration guide covering imports, CLI commands, URLs, configuration changes, compatibility limits, and upgrade order from ForgeFlow 0.1.x to PipelineKit 0.2.0.

- [ ] Step 4: Remove stale paths, old clone commands, contradictory feature lists, and unsupported claims. Keep historical rename information only in the migration guide and changelog.

- [ ] Step 5: Run rg -n -i "forgeflow|forge flow|dataforge|data-forge" README.md docs CONTRIBUTING.md pyproject.toml. Expected: matches occur only in the migration guide and historical changelog entries.

- [ ] Step 6: Commit with git commit -m "docs: document PipelineKit and ForgeFlow migration".

---

### Task 6: Add release and repository migration automation

**Files:**
- Modify: pyproject.toml, .gitignore
- Create or modify: .github/workflows/test.yml, .github/workflows/build.yml, .github/workflows/release.yml
- Create: tests/test_build_metadata.py
- Create: SECURITY.md if absent

**Interfaces:**
- Consumes: buildable pipelinekit package and documentation from Tasks 3–5.
- Produces: repeatable CI validation and release metadata.

- [ ] Step 1: Add tests asserting project name pipelinekit, version 0.2.0, the new console script, and no recursive all extra.

- [ ] Step 2: Configure CI for Python 3.11 and 3.12 with tests, Ruff, mypy, and package build. Keep optional integration jobs separate.

- [ ] Step 3: Configure release artifacts first; publish only after package ownership, repository rename, and credentials are confirmed.

- [ ] Step 4: Run pytest tests/test_build_metadata.py -v and python -m build. Validate workflow YAML syntax before committing.

- [ ] Step 5: Commit with git commit -m "ci: validate and build PipelineKit".

---

### Task 7: Rename the GitHub repository and perform release cutover

**Files:**
- Modify: repository settings for leduardoaraujo/forgeflow
- Modify: pyproject.toml, README.md, CHANGELOG.md, docs if redirects do not cover all links
- Create: release notes for PipelineKit 0.2.0

**Interfaces:**
- Consumes: passing code, documentation, CI, and build checks from Tasks 1–6.
- Produces: canonical repository leduardoaraujo/pipelinekit.

- [ ] Step 1: Run pytest -q, ruff check ., mypy pipelinekit/, python -m build, and the legacy-reference scan. Expected: all checks pass and old references are limited to the migration guide and historical changelog.

- [ ] Step 2: Confirm pipelinekit is available for publication and that metadata points to the intended repository.

- [ ] Step 3: Rename the repository to leduardoaraujo/pipelinekit in GitHub settings. Preserve the old repository redirect and do not delete the old name.

- [ ] Step 4: Update canonical links and publish release notes describing package imports, CLI change, compatibility surface, and rollback path.

- [ ] Step 5: Verify from a clean virtual environment:

~~~bash
python -m venv /tmp/pipelinekit-check
source /tmp/pipelinekit-check/bin/activate
python -m pip install --upgrade pip
python -m pip install pipelinekit
pipelinekit --help
python -c "import pipelinekit; print(pipelinekit.__version__)"
~~~

Expected: installation succeeds, CLI help works, and the installed version prints 0.2.0.

- [ ] Step 6: Commit final metadata with git commit -m "release: cut over from ForgeFlow to PipelineKit".

## Self-review

- Naming, architecture, migration, documentation, testing, and out-of-scope requirements from the design spec are covered by Tasks 1–7.
- No TBD, TODO, or unspecified “appropriate handling” steps remain.
- The canonical package name is pipelinekit, the compatibility package is forgeflow, and the release target is 0.2.0.
- Repository rename is last and depends on passing tests, lint, type checks, build, and a clean-reference scan.
