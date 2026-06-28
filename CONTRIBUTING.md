# Welcome to gget's contributing guide <!-- omit in toc -->

Thank you for investing your time in contributing to our project! Any contribution you make will be reflected on the [gget repo](https://github.com/scverse/gget). ✨

Read our [Code of Conduct](./code_of_conduct.md) to keep our community approachable and respectable.

Please note that `gget` aims to **maintain backward compatibility** whenever possible. When contributing changes, avoid breaking existing user workflows, APIs, command-line behavior, or documented outputs unless there is a strong reason to do so and the change has been clearly discussed.

In this guide you will get an overview of the contribution workflow from opening an issue or creating a pull request (PR) to reviewing and merging a PR.

## Issues

### Create a new issue

If you spot a problem with gget or you have an idea for a new feature, [check if an issue already exists](https://github.com/scverse/gget/issues). If a related issue doesn't exist, you can open a new issue using the relevant [issue form](https://github.com/scverse/gget/issues/new/choose).

### Solve an issue

Scan through our [existing issues](https://github.com/scverse/gget/issues) to find one that interests you. You can narrow down the search using `labels` as filters. If you find an issue to work on, you are welcome to open a PR with a fix.

## Contribute through pull requests

### Getting started

1. Fork the repository.
- Using GitHub Desktop:
  - [Getting started with GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) will guide you through setting up Desktop.
  - Once Desktop is set up, you can use it to [fork the repo](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!

- Using the command line:
  - [Fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) so that you can make your changes without affecting the original project until you're ready to merge them.

2. Create a working branch and start with your changes!

### Commit your update

Commit the changes once you are happy with them.

### ‼️ Self-review the following before creating a Pull Request ‼️

1. Review the content for technical accuracy and biological relevance (who are your target users and is this useful to them?).
2. Copy-edit the changes/comments for grammar, spelling, and adherence to the general style of existing gget code.
3. **Command line interface:** Make sure edits keep the Python function and the command-line interface in sync. Any change to a function's arguments must be reflected in both the Python signature and the CLI argument parser.
    - The command line interface and arguments are defined in ./gget/main.py
4. **Documentation:** Add new modules/arguments to the documentation if applicable:
    - The manual for each module can be added/edited in `./docs/src/en/*.md` (the Spanish version of the docs in `./docs/src/es/*.md` is automatically generated/updated, and does not need to be edited manually)
    - **Document all edits in `./docs/src/en/updates.md`.** Keep this brief and succinct.
5. **Add unit tests:** Add new unit tests if applicable:
    - Arguments and expected results are stored in json files in ./tests/fixtures/
    - Unit tests can be added to ./tests/test_*.py and will be automatically detected
6. **Run unit tests:** Make sure the unit tests pass:
    - The tested environments are defined in `pyproject.toml` under `[tool.hatch.envs.hatch-test]` (the single source of truth used by CI). Run the full matrix with `uvx hatch test`.
    - For a quick single-environment run, install the test dependencies with `uv sync --group test` and run `uv run pytest -ra -v --cov=gget --cov-report=term-missing tests`. To also exercise the `gget cellxgene` module, install its extra (`uv sync --group test --extra cellxgene`) on Python 3.12/3.13 — its dependency has no wheels for newer Python versions yet, and that test skips itself when the dependency is absent.

If you have any questions, feel free to start a [discussion](https://github.com/scverse/gget/discussions) or create an issue as described above.

### Keep PRs small and focused

Reviewers move faster on small, focused PRs. Whenever possible:

- **Scope each PR to a single `gget` module or issue**. If you find yourself changing more than one module to address several distinct concerns, please open them as separate PRs — one per module. Bug fixes and small refactors inside one module can be combined; cross-module work should be split.
- **Don't bundle unrelated changes** (e.g. a bug fix plus a new feature plus a refactor) in the same PR.

### Pull Request

When you're finished with the changes, [create a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request), also known as a PR.

‼️ Please DO NOT commit AI-generated code without careful review.

‼️ Please make all PRs against the `dev` branch of the gget repository.

- Don't forget to [link PR to issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue) if you are solving one.
- Enable the checkbox to [allow maintainer edits](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests/allowing-changes-to-a-pull-request-branch-created-from-a-fork) so the branch can be updated for a merge.
- If you run into any merge issues, checkout this [git tutorial](https://github.com/skills/resolve-merge-conflicts) to help you resolve merge conflicts and other issues.

Once you submit your PR, a `gget` team member will review your proposal. We may ask questions or request additional information.

### What runs automatically on your PR

When you open a PR, a few checks run automatically — you don't need to set anything up:

- **Linting & formatting** ([pre-commit.ci](https://pre-commit.ci)): runs [ruff](https://docs.astral.sh/ruff/) (lint + format), [biome](https://biomejs.dev/), and basic hygiene hooks. It **auto-fixes** formatting issues by pushing a commit to your branch; it only fails the check for problems it can't fix automatically (e.g. lint errors).
- **Type checking** (mypy, via pre-commit.ci): newly introduced type errors fail this check.
- **Unit tests** (`CI - tests`): the complete test suite for all modules runs on Python 3.12, 3.13, and 3.14.
- **Build check**: confirms the package still builds and is publishable.

Optional: You can run these manually first (especially `uvx hatch test` and `prek run --all-files`) to catch most issues before creating the PR.

### Failing tests for modules you didn't touch

The `gget` test suite hits real upstream databases (Ensembl, UniProt, NCBI, ARCHS4, Open Targets, ELM, etc.). When those services change their data or schemas — which they do regularly — tests for the affected modules can start failing without anyone changing `gget` itself. **If automated CI tests fail in your PR for a module you did not touch, you can safely ignore those failures** when judging whether your PR is ready to merge. The maintainers track upstream-drift failures separately and do not expect contributors to fix unrelated breakages as a condition of merging.

### Your PR gets merged!

Congratulations! 🎉	 The `gget` team thanks you. ✨

Once your PR is merged, your contributions will be publicly visible on the [gget repo](https://github.com/scverse/gget).
