# Contributing to Trade System

Thank you for your interest in contributing to the Trade System project! This guide will help you get started.

## 🏗️ Project Structure

This is a monorepo containing multiple microservices:
- `trade_batch` - Java/Spring Boot batch processing
- `trade_dashboard` - Python/FastAPI dashboard backend
- `trade_engine` - Python trading engine
- `trade_frontend` - Svelte frontend application
- `trade_infra` - Infrastructure configurations
- `common` - Shared libraries and resources

## 🔄 Development Workflow

### 1. Branch Strategy

We use a simplified Git Flow:
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Feature development
- `fix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### 2. Creating a Feature

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat(scope): description"

# Push and create PR
git push origin feature/your-feature-name
```

## 📝 Commit Message Convention

We follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Scopes
- `batch`: Changes to trade_batch service
- `dashboard`: Changes to trade_dashboard service
- `engine`: Changes to trade_engine service
- `frontend`: Changes to trade_frontend service
- `infra`: Infrastructure changes
- `common`: Changes to shared resources
- `all`: Changes affecting multiple services

### Examples
```
feat(engine): add new momentum strategy
fix(dashboard): resolve WebSocket connection timeout
docs(all): update API documentation
chore(infra): upgrade PostgreSQL to v15
```

## 🧪 Testing Requirements

### Before Submitting PR

1. **Run tests for affected services:**
   ```bash
   # Use the Makefile
   make test-all
   
   # Or test individually
   cd trade_batch && ./mvnw test
   cd trade_dashboard && pytest
   cd trade_engine && pytest
   cd trade_frontend && npm test
   ```

2. **Check code quality:**
   ```bash
   # Python projects
   black .
   isort .
   pylint src/
   
   # Frontend
   npm run lint
   npm run check
   ```

3. **Update documentation:**
   - Update README if adding new features
   - Document API changes
   - Update environment variables in `.env.example`

## 💻 Development Setup

### Prerequisites
- Docker & Docker Compose
- Java 17
- Python 3.11+
- Node.js 18+
- Git

### Initial Setup
```bash
# Clone repository
git clone https://github.com/waterSu1031/trade.git
cd trade

# Install Git hooks
git config commit.template .gitmessage

# Setup infrastructure
cd trade_infra/docker/compose
docker-compose up -d

# Install dependencies for each service
make install-all
```

## 🔍 Code Review Process

1. **Self Review**: Check your own PR first
2. **Automated Tests**: Must pass all CI checks
3. **Code Review**: At least one approval required
4. **Testing**: Reviewer should test locally if possible

### Review Checklist
- [ ] Code follows project conventions
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No sensitive data (passwords, keys) committed
- [ ] Performance impact considered
- [ ] Error handling is appropriate

## 🚀 Release Process

1. Features are merged to `develop`
2. When ready for release:
   ```bash
   git checkout main
   git merge --no-ff develop
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin main --tags
   ```

## 📋 Pull Request Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## 🐛 Reporting Issues

When reporting issues, please include:
1. Service affected
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Environment details (OS, versions)
6. Relevant logs

## 💡 Suggesting Enhancements

We welcome suggestions! Please:
1. Check existing issues first
2. Clearly describe the enhancement
3. Explain the use case
4. Consider implementation approach

## 📞 Getting Help

- Check service-specific README files
- Review existing issues and PRs
- Ask in discussions section
- Contact maintainers

## 🙏 Recognition

Contributors will be recognized in:
- Release notes
- Contributors section in README
- Project statistics

Thank you for contributing to Trade System!