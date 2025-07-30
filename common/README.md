# Common Resources for Trade MSA Project

This directory contains shared resources for all microservices in the Trade project.

**Note**: Environment variables are managed at the project root level (`.env`, `.env.development`, `.env.production`)

## Directory Structure

```
common/
├── templates/       # Project templates
│   ├── api-spec/   # API specification templates
│   └── docs/       # Documentation templates
├── tools/          # Development tools
│   ├── linters/    # Code style checkers
│   └── git-hooks/  # Git pre-commit hooks
└── docs/           # Common documentation
```

## Usage

### Templates

Standardized templates for:
- API specifications (OpenAPI/Swagger)
- Documentation formats
- Service README templates

### Development Tools

Common development tools:
- Linting configurations (ESLint, Pylint, etc.)
- Pre-commit hooks for code quality
- Code formatting rules

## Contributing

When adding new common resources:
1. Ensure the resource is truly shared across multiple services
2. Document the usage in the appropriate subdirectory
3. Update this README with any new categories