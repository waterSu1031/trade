# Common Resources for Trade MSA Project

This directory contains shared resources for all microservices in the Trade project.

## Directory Structure

```
common/
├── libs/            # Shared libraries
│   ├── python/     # Python common modules
│   └── java/       # Java common libraries
├── templates/       # Project templates
│   ├── api-spec/   # API specification templates
│   └── docs/       # Documentation templates
├── tools/          # Development tools
│   ├── linters/    # Code style checkers
│   └── git-hooks/  # Git pre-commit hooks
└── docs/           # Common documentation
```

## Usage

### Shared Libraries

Place common code that is used across multiple services here:
- Python: Utility functions, data models, API clients
- Java: Common interfaces, utility classes, shared DTOs

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