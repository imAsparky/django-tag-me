# Contributing to Django-Tag-Me

Thank you for considering contributing to Django-Tag-Me! Every contribution helps make the project better, and all contributors will be acknowledged. This guide will help you get started with the development process.

## Ways to Contribute

### Reporting Bugs
If you find a bug, please report it at our [issue tracker](https://github.com/imAsparky/django-tag-me/issues). When reporting bugs, please include:
- Your operating system name and version
- Your Python and Django versions
- Detailed steps to reproduce the bug
- Any relevant error messages or screenshots

### Contributing Code
- Look for issues labeled `bug` and `help wanted` if you want to fix bugs
- Check issues labeled `enhancement` and `help wanted` for new features to implement
- Feel free to propose new features through the issue tracker

### Improving Documentation
We always welcome documentation improvements, whether it's:
- Official documentation
- Code docstrings
- Code comments
- Blog posts or articles about Django-Tag-Me

### Providing Feedback
Share your ideas and feedback through our [issue tracker](https://github.com/imAsparky/django-tag-me/issues). When proposing new features:
- Explain the feature in detail
- Keep the scope focused and specific
- Consider implementation complexity

## Development Setup

1. **Fork the Repository**
   Fork [django-tag-me](https://github.com/imAsparky/django-tag-me.git) by clicking the "Fork" button

2. **Clone Your Fork**
   ```bash
   cd <your_workspace>
   git clone git@github.com:YOUR_NAME/django-tag-me.git
   cd django-tag-me
   ```

3. **Create Virtual Environment**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r example/requirements_dev.txt
   pip install -e .  # Install in editable mode
   ```

5. **Set Up Example Project**
   ```bash
   cd example/
   ./manage.py reset_and_seed_blog
   ./manage.py runserver
   ```
   Visit http://127.0.0.1:8000/ to view the example blog

6. **Create a Feature Branch**
   ```bash
   git checkout -b feature-name
   ```

## Testing

We use `tox` for testing across multiple Python and Django versions. Here are some helpful commands:

```bash
# Run all tests
tox

# List all test environments
tox list

# Run tests for a specific environment
tox -e py310-django41
```

### Speeding Up Test Runs
- Use `-p` flag with tox to run environments in parallel: `tox -p auto`
- Run specific test files: `tox -e py310-django41 tests/test_specific.py`
- Use pytest markers to run specific test categories: `tox -e py310-django41 -m "not slow"`

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. The format is:

```
<type>(<scope>): <description> #<issue-number>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```bash
git commit -S -m "feat(auth): Add social login support #123"
```

### Important Notes:
- All commits must be signed (`-S` flag)
- Always reference relevant issue numbers
- Keep commits focused and atomic
- Write clear, descriptive commit messages

## Pull Request Process

1. Ensure your code passes all tests (`tox`)
2. Update documentation if needed
3. Add tests for new functionality
4. Follow the existing code style
5. Update CHANGELOG.md if applicable
6. Submit PR against the `main` branch

## Test Matrix

The project supports:
- Python: 3.10, 3.11, 3.12, 3.13
- Django: 4.1, 4.2, 5.0, 6.0

## Need Help?

Feel free to ask questions on the issue tracker or reach out to maintainers. We're here to help make your contribution process smooth and enjoyable!


