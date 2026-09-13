# Contributing to ContractGuard

Thank you for your interest in improving **ContractGuard**! We welcome contributions from developers worldwide.

## Quickstart for Contributors

1. **Fork & Clone**:
   ```bash
   git clone https://github.com/tusharjamunkar/contract-guard.git
   cd contract-guard
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
   pip install -e .
   pip install pytest
   ```

3. **Run Tests**:
   ```bash
   pytest -v
   ```

4. **Code Quality**:
   - Ensure 100% test coverage for new diffing rules.
   - Maintain zero external paid API dependencies.

## Submitting Pull Requests
- Open PRs against the `main` branch.
- Clearly describe the schema drift scenario or new CLI feature.
