---
icon: lucide/git-pull-request
---

# Contributing

Thank you for considering contributing to fileup! This guide will help you get started.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/basnijholt/fileup.git
   cd fileup
   ```

2. Install development dependencies with uv:
   ```bash
   uv sync --group test --group docs
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run the test suite with:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=fileup --cov-report=html
```

## Code Style

This project uses:

- **Ruff** for linting and formatting
- **mypy** for type checking
- **pre-commit** for automated checks

Run checks manually:

```bash
ruff check .
ruff format .
mypy fileup.py
```

## Building Documentation

Generate and build the documentation locally:

```bash
uv run markdown-code-runner docs/*.md README.md
uv run zensical build
```

Preview the docs:

```bash
uv run zensical serve
```

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting
5. Commit with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Reporting Issues

When reporting issues, please include:

- Your Python version
- Your operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Any error messages

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
