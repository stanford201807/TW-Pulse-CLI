# Contributing to Pulse CLI

Thank you for your interest in contributing to Pulse CLI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- A GitHub account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/pulse-cli.git
cd pulse-cli
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/pulse-cli.git
```

## Development Setup

### Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Install Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install Playwright browsers (for Stockbit integration)
playwright install chromium
```

### Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

### Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check pulse/

# Run type checking
mypy pulse/

# Start the application
pulse
```

## Making Changes

### Create a Branch

Always create a new branch for your changes:

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### Branch Naming Convention

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications

### Commit Messages

Follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(screener): add small cap filter support
fix(sapta): correct absorption score calculation
docs(readme): update installation instructions
test(trading_plan): add RR ratio calculation tests
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting, missing semicolons, etc.
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance tasks

## Pull Request Process

### Before Submitting

1. **Update from upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks:**
   ```bash
   # Linting
   ruff check pulse/
   
   # Type checking
   mypy pulse/
   
   # Tests
   pytest
   ```

3. **Format code:**
   ```bash
   ruff format pulse/
   ```

### Submitting

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub

3. Fill in the PR template with:
   - Description of changes
   - Related issue numbers
   - Screenshots (if UI changes)
   - Testing performed

### PR Review Process

- At least one maintainer must review and approve
- All CI checks must pass
- Address review comments promptly
- Keep PRs focused and reasonably sized

## Coding Standards

### Python Style

We follow PEP 8 with some modifications. Use `ruff` for linting:

```bash
ruff check pulse/
ruff format pulse/
```

### Key Guidelines

1. **Type Hints:** Use type hints for all function parameters and returns
   ```python
   async def analyze(self, ticker: str) -> Optional[AnalysisResult]:
       ...
   ```

2. **Docstrings:** Use Google-style docstrings
   ```python
   def calculate_rsi(prices: List[float], period: int = 14) -> float:
       """Calculate Relative Strength Index.
       
       Args:
           prices: List of closing prices
           period: RSI period (default: 14)
           
       Returns:
           RSI value between 0 and 100
           
       Raises:
           ValueError: If prices list is shorter than period
       """
   ```

3. **Imports:** Order imports as:
   - Standard library
   - Third-party packages
   - Local imports

4. **Line Length:** Maximum 100 characters

5. **Async/Await:** Use async for I/O operations
   ```python
   async def fetch_data(self, ticker: str) -> dict:
       # Use aiohttp or similar for async HTTP
       ...
   ```

### Project Structure

When adding new features:

- **Data fetching** → `pulse/core/data/`
- **Analysis modules** → `pulse/core/analysis/`
- **CLI commands** → `pulse/cli/commands/`
- **AI integration** → `pulse/ai/`
- **SAPTA modules** → `pulse/core/sapta/modules/`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pulse --cov-report=html

# Run specific test file
pytest tests/test_core/test_screener.py

# Run specific test
pytest tests/test_core/test_screener.py::test_oversold_screening -v

# Run tests matching pattern
pytest -k "test_rsi"
```

### Writing Tests

1. Place tests in `tests/` directory mirroring source structure
2. Use `pytest` fixtures for common setup
3. Test both success and failure cases
4. Mock external API calls

Example:
```python
import pytest
from pulse.core.screener import StockScreener, ScreenPreset

@pytest.fixture
def screener():
    return StockScreener(universe=["BBCA", "BBRI", "BMRI"])

@pytest.mark.asyncio
async def test_oversold_screening(screener):
    results = await screener.screen_preset(ScreenPreset.OVERSOLD)
    assert isinstance(results, list)
    for result in results:
        assert result.rsi_14 is not None
        assert result.rsi_14 < 30
```

### Test Coverage

Aim for at least 80% coverage for new code. Check coverage:

```bash
pytest --cov=pulse --cov-report=term-missing
```

## Documentation

### Code Documentation

- All public functions need docstrings
- Complex algorithms should have inline comments
- Update type hints when changing signatures

### README Updates

When adding features:
1. Update command reference in README.md
2. Add usage examples
3. Update configuration section if needed

### Changelog

For significant changes, add entry to CHANGELOG.md:

```markdown
## [Unreleased]

### Added
- New small cap screening filter (#123)

### Fixed
- SAPTA absorption calculation error (#124)

### Changed
- Improved RSI calculation performance
```

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for general questions
- Tag maintainers for urgent matters

Thank you for contributing to Pulse CLI!
