
# Contributing to GPS Tracker

Thank you for your interest in contributing to **GPS Tracker**! 🚀

This guide explains how to contribute to the project, report issues, and propose improvements.

---

## How to Contribute

1. **Fork the repository** to your own GitHub account.
2. **Create a new branch** for your changes:
bash
git checkout -b feature/my-new-feature

3. Make your changes in your branch.
4. Commit your changes with a clear message:
git commit -am "Add short description of changes"

5. Push your branch to your fork:

git push origin feature/my-new-feature

6. Open a Pull Request here on GitHub, describing your changes and purpose.




---

Coding Style

Use clear and descriptive names for functions and variables.

Keep functions small and focused.

Add comments in English explaining complex logic.

Follow PEP8 standards for Python formatting.



---

Testing

All new features or bug fixes should include tests in the tests/ directory.

Example:


# tests/test_gps_tracker.py
import pytest
from gps_tracker import GPSTracker, Position

def test_position_creation():
    pos = Position(10.0, 20.0, 5.0, 1234567890)
    assert pos.lat == 10.0
    assert pos.lon == 20.0

Run tests with:


pytest


---

Reporting Bugs

Open a new issue on GitHub with:

A clear description of the problem

Steps to reproduce the issue

Any error messages or logs (if available)




---

Feature Requests

Open an issue labeled enhancement.

Describe your idea clearly and why it would improve the project.



---

Code of Conduct

Be respectful and collaborative.

Keep discussions friendly and constructive.

Personal attacks or offensive language will not be tolerated.



---

Thank you for helping make GPS Tracker better! 🌟

---

Se você quiser, posso também criar um **README.md atualizado** com instruções claras, exemplos de uso e referência ao `CONTRIBUTING.md`, para deixar seu repositório **completamente pronto para receber contribuições**.  

Quer que eu faça isso também?
