# Contributing to ForgeAI

Thank you for your interest in contributing to ForgeAI! This guide will help you get started and ensure a smooth contribution process.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:

1. **Clear title** - Summarize the issue
2. **Environment details** - OS, Python/Node versions, Docker version
3. **Steps to reproduce** - Detailed steps to trigger the bug
4. **Expected behavior** - What should happen
5. **Actual behavior** - What actually happens
6. **Screenshots** - If applicable
7. **Error messages** - Full stack trace if available

### Suggesting Features

Feature requests are welcome! Please provide:

1. **Problem statement** - What problem does this solve?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - Other approaches
4. **Additional context** - Examples, mockups, etc.

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (recommended)
- Git 2.30+

### Setup Steps

1. **Fork and clone the repository**

```bash
git clone https://github.com/your-username/forgeai.git
cd forgeai
git remote add upstream https://github.com/org/forgeai.git
```

2. **Run setup script**

```bash
./scripts/setup.sh
```

3. **Create a branch**

```bash
git checkout -b feat/your-feature-name
```

4. **Start development**

```bash
./scripts/dev.sh
```

### Development Workflow

1. Make changes in your feature branch
2. Write tests for new code
3. Run the full test suite
4. Update documentation
5. Commit with clear messages
6. Push and create PR

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Standards

Positive behavior includes:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

Unacceptable behavior includes:

- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information without consent
- Other conduct inappropriate in a professional setting

### Enforcement

Project maintainers can remove, ban, or block contributors for inappropriate behavior.

## Issue Templates

### Bug Report

```markdown
## Bug Description

A clear and concise description of the bug.

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- OS: [e.g., Windows 11, macOS 14]
- Python: [e.g., 3.12.0]
- Node.js: [e.g., 20.10.0]
- Docker: [e.g., 24.0.7]

## Additional Context

Any other context about the problem.
```

### Feature Request

```markdown
## Description

A clear and concise description of the feature.

## Problem Statement

What problem does this feature solve?

## Proposed Solution

How should this feature work?

## Alternatives Considered

Other approaches you've considered.

## Additional Context

Mockups, examples, or references.
```

## PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Test update

## Related Issues

Closes #(issue number)

## Changes Made

- Change 1
- Change 2
- Change 3

## Testing

Describe tests you ran:

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist

- [ ] My code follows the project style guidelines
- [ ] I have added tests that prove my fix/feature works
- [ ] All new and existing tests pass
- [ ] I have updated documentation accordingly
- [ ] My changes generate no new warnings

## Screenshots (if applicable)

Add screenshots to illustrate changes.
```

## Development Guidelines

### Code Style

- Follow [Coding Standards](CodingStandards.md)
- Use meaningful variable/function names
- Keep functions small and focused
- Write self-documenting code

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error scenarios
- Use appropriate test fixtures

### Documentation

- Update README if adding features
- Add docstrings to new functions
- Update API documentation for new endpoints
- Include examples for complex features

### Performance

- Consider performance implications
- Use async/await for I/O operations
- Implement caching where appropriate
- Profile before optimizing

## Getting Help

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Search existing issues
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our community (if available)

## Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- Annual contributor report

---

*Thank you for contributing to ForgeAI!*
