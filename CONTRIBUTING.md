# Contributing to Wiki7

Thank you for your interest in contributing to Wiki7, the fan wiki for Hapoel Beer Sheva FC.

## Getting Started

See [docs/SETUP.md](docs/SETUP.md) for instructions on setting up a local development environment.

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `master` | Stable, deployed to production |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `claude/*` | AI-assisted development sessions |

Create your branch from `master` and keep it focused on a single change.

## Coding Standards

- **PHP**: Follow [MediaWiki coding conventions](https://www.mediawiki.org/wiki/Manual:Coding_conventions)
- **JavaScript**: Follow [eslint-config-wikimedia](https://github.com/wikimedia/eslint-config-wikimedia)
- **Python**: Follow [ruff](https://docs.astral.sh/ruff/) defaults
- **LESS**: Follow [stylelint-config-wikimedia](https://github.com/wikimedia/stylelint-config-wikimedia)

Run `make lint` to check your code before committing.

## Commit Messages

Use a conventional format that describes what the change does:

- `Fix XSS in search highlight`
- `Add Hebrew translations for command palette`
- `Update Docker health check intervals`
- `Remove unused CSS variables`

Keep the first line under 72 characters. Add a blank line and further explanation if needed.

## Pull Request Process

1. Create a branch following the naming convention above.
2. Make your changes and ensure `make test` and `make lint` pass.
3. Push your branch and open a pull request against `master`.
4. Describe what you changed and why in the PR description.
5. Wait for review before merging.

## Project Structure

```
Wiki7/
  cdk/          — AWS CDK infrastructure (TypeScript)
  data/         — Data scraping and normalization pipeline (Python)
  docker/       — Docker Compose local development environment
    skins/Wiki7 — MediaWiki skin (PHP, JS, LESS)
  docs/         — Project documentation
```

For more details, see:

- [docs/INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) — AWS infrastructure
- [docs/SKIN-DEVELOPMENT.md](docs/SKIN-DEVELOPMENT.md) — Skin development
- [data/README.md](data/README.md) — Data pipeline
