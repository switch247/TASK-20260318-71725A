# AI Agent Instructions

This file provides guidance for AI agents operating in this repository.

---

## 1. Build, Lint, and Test Commands

### Common Commands (Node.js/TypeScript)

```bash
# Install dependencies
npm install

# Build project
npm run build

# Run development server
npm run dev

# Run linter
npm run lint

# Fix lint issues
npm run lint:fix

# Run type checking
npm run typecheck
# or: npx tsc --noEmit

# Run tests
npm test

# Run a single test file
npx jest path/to/test.test.ts
# or: npm test -- --testPathPattern="test-name"
# or: npx vitest run path/to/test.test.ts

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Python Projects

```bash
# Install dependencies
pip install -r requirements.txt

# Run linter (ruff)
ruff check .

# Format code
ruff format .

# Type checking (mypy)
mypy .

# Run tests
pytest

# Run a single test
pytest path/to/test.py::test_function_name
pytest -k "test_name_pattern"

# Run with coverage
pytest --cov=. --cov-report=html
```

### Docker Projects

```bash
# Build and start all services
docker compose up

# Build without starting
docker compose build

# Run tests in container
docker compose run --rm app pytest
```

---

## 2. Code Style Guidelines

### General Principles

- Write clean, readable, and maintainable code
- Keep functions small and focused (single responsibility)
- Use meaningful names for variables, functions, and files
- Avoid deep nesting (max 3-4 levels)
- No magic numbers - use constants

### Imports

- Group imports: built-in → external → local
- Use absolute imports when possible
- Prefer specific imports over barrel files for tree-shaking
- Sort alphabetically within groups

```typescript
// Good
import { useState } from 'react';
import { formatDate } from '@/utils/date';
import { ApiError } from '@/errors';

// Avoid
import * as React from 'react';
import { DateUtils } from '../utils';
```

### Formatting

- Use Prettier for code formatting (run before commit)
- 2 spaces for indentation (or 4 spaces - match project style)
- Maximum line length: 80-100 characters
- Use semicolons consistently
- Trailing commas in arrays and objects

### Types

- Use TypeScript strict mode
- Avoid `any` - use `unknown` or proper types
- Use interfaces for object shapes, types for unions
- Enable `noImplicitReturns` and `noImplicitAny`
- Prefer explicit return types for exported functions

```typescript
// Good
interface User {
  id: string;
  name: string;
  email: string;
}

function getUser(id: string): Promise<User> {
  // ...
}

// Avoid
function getUser(id) {
  // ...
}
```

### Naming Conventions

- **Files**: kebab-case (component-name.tsx) or PascalCase (UserService.ts)
- **Functions**: camelCase, verb + noun (getUserById, calculateTotal)
- **Classes/Components**: PascalCase (UserService, HeaderComponent)
- **Constants**: UPPER_SNAKE_CASE or camelCase with prefix
- **Interfaces**: PascalCase, optionally prefixed with "I" (User, IUserProps)

### Error Handling

- Return structured errors, never crash silently

```json
{ "code": 400, "message": "Invalid input", "details": {} }
```

- Use custom error classes for domain errors
- Always log errors with context
- Never expose sensitive data in error messages

```typescript
// Good
class ValidationError extends Error {
  constructor(message: string, public field: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Usage
if (!isValid) {
  throw new ValidationError('Email is required', 'email');
}
```

### Logging

- Log key operations: authentication, data changes, critical flows
- Use appropriate log levels: error, warn, info, debug
- Include context (correlation IDs, user IDs)
- Never log secrets, passwords, or sensitive data

```typescript
logger.info('User logged in', { userId: user.id, method: 'email' });
logger.error('Payment failed', { orderId, error: err.message });
```

### Security

- Validate all inputs (body, query params, path params)
- Use parameterized queries to prevent SQL injection
- Never commit secrets - use environment variables
- Sanitize user inputs before displaying
- Implement proper authentication and authorization

### Testing

- Test happy path, edge cases, and error scenarios
- Use descriptive test names (should return error when...)
- Follow AAA pattern: Arrange, Act, Assert
- Mock external dependencies
- Aim for meaningful coverage of business logic

---

## 3. Project-Specific Notes

### Code Generation Task (Default)

When generating code from prompts:

- Deliver complete, production-like, runnable projects
- Include source code, config files, dependencies, tests
- Use clean directory structure (src/, config/, tests/, README.md)
- Implement real business logic - never fake or hardcode core functionality
- Follow Docker requirements if backend/fullstack:
  - All services in docker-compose.yml
  - Explicit port exposure
  - Public base images only

### Testing Requirements

- Unit tests for core logic, edge cases, error handling
- API tests for valid/invalid requests, permissions
- run_tests.sh that outputs pass/fail summary

### Business Logic

- Ensure logical consistency (no invalid states)
- Prevent duplicate actions
- Validate data before persistence

---

## 4. Cursor/Copilot Rules

No custom Cursor or Copilot rules found in this repository.

Product Accessory Structure Specification
The submitted Compressed Packet must strictly follow the following directory structure:
Plaintext
Root Directory/
├── [Project Type Name]/      # e.g., pure_backend, pure_frontend, fullstack, etc.
│   └── [Project Files...]    # Cleaned project code
├── prompt.md                 # Original Prompt file
├── trajectory.json           # Converted OpenAI format trajectory file 
│                             # In case of multiple trajectory files, change to a "sessions" folder and use trajectory-1.json with numbering.
├── questions.md              # (Required) Record of questions regarding the  original Prompt
└── docs/                     # Document deliverables
    ├── design.md             # Design document
    └── api-spec.md           # API specification
    └── ...