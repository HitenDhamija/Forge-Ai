# Repository Intelligence Engine

## Overview

The Repository Intelligence Engine is ForgeAI's core system for analyzing, understanding, and indexing codebases. It automatically detects languages, frameworks, architecture patterns, and builds a semantic graph representing the entire repository structure. This intelligence powers AI-assisted code navigation, impact analysis, and contextual suggestions.

## Component Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Repository Intelligence Engine                  │
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │  Importers   │──▶│  Analyzers   │──▶│    Graph     │            │
│  │              │   │              │   │   Builder    │            │
│  │  - Zip       │   │  - Language  │   │              │            │
│  │  - Git       │   │  - Framework │   │  - Nodes     │            │
│  │  - Folder    │   │  - AST       │   │  - Edges     │            │
│  └──────────────┘   │  - Database  │   │  - Metadata  │            │
│         │           │  - Route     │   └──────┬───────┘            │
│         │           │  - Directory │          │                    │
│         │           │  - Config    │          ▼                    │
│         │           │  - Semantic  │   ┌──────────────┐            │
│         │           └──────────────┘   │  Services    │            │
│         │                              │              │            │
│         │                              │  - Repository│            │
│         ▼                              │  - Analysis  │            │
│  ┌──────────────┐                      │  - Search    │            │
│  │    Schemas   │                      └──────────────┘            │
│  │              │                                                   │
│  │  - Repository│   ┌──────────────┐   ┌──────────────┐            │
│  │  - Analysis  │◀──│   Config     │   │  Exceptions  │            │
│  │  - Graph     │   │              │   │              │            │
│  └──────────────┘   └──────────────┘   └──────────────┘            │
└──────────────────────────────────────────────────────────────────────┘
```

## Analysis Pipeline Flow

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Import  │──▶│ Validate │──▶│  Scan    │──▶│  Detect  │
│          │   │          │   │          │   │          │
│ zip/git  │   │ size     │   │ files    │   │ language │
│ /folder  │   │ structure│   │ dirs     │   │ framework│
└─────────┘    └──────────┘    └──────────┘    └──────────┘
                                                       │
    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
    │  Build   │◀──│  Analyze │◀──│  Parse   │◀─────┘
    │  Graph   │   │  Arch    │   │  AST     │
    │          │   │          │   │          │
    │ nodes    │   │ patterns │   │ code     │
    │ edges    │   │ styles   │   │ elements │
    └──────────┘    └──────────┘    └──────────┘
```

### Pipeline Stages

1. **Import**: Repository is cloned (git), extracted (zip), or referenced (folder)
2. **Validate**: Size limits, structure checks, permission verification
3. **Scan**: Walk directory tree, collect files and directories
4. **Detect**: Identify languages by extension, frameworks by config files and patterns
5. **Parse**: Extract code elements via AST (tree-sitter) for supported languages
6. **Analyze**: Determine architecture style, routes, database models
7. **Build Graph**: Construct semantic graph with nodes and edges

## Language Detection System

Language detection uses a multi-signal approach:

### Extension-Based Detection
Each programming language has associated file extensions:

| Language | Extensions |
|----------|-----------|
| Python | `.py`, `.pyw`, `.pyi` |
| JavaScript | `.js`, `.mjs`, `.cjs` |
| TypeScript | `.ts`, `.tsx`, `.mts` |
| Java | `.java` |
| Go | `.go` |
| Rust | `.rs` |
| C | `.c`, `.h` |
| C++ | `.cpp`, `.cc`, `.cxx`, `.hpp` |
| C# | `.cs` |
| Ruby | `.rb`, `.rake` |
| PHP | `.php` |
| Swift | `.swift` |
| Kotlin | `.kt`, `.kts` |
| Scala | `.scala` |
| Shell | `.sh`, `.bash`, `.zsh` |

### Shebang Detection
Files without extensions are checked for `#!` shebang lines:
- `#!/usr/bin/env python` → Python
- `#!/bin/bash` → Shell

### Confidence Scoring
Each detected language receives a confidence score based on:
- Number of files found
- Total lines of code
- Presence of config files (e.g., `pyproject.toml` for Python)
- Directory conventions (e.g., `src/main/java/` for Java)

## Framework Detection System

Frameworks are detected through multiple signals:

### Configuration File Detection
```
package.json          → Node.js ecosystem (React, Vue, Next.js, etc.)
requirements.txt      → Python (Django, Flask, FastAPI)
pyproject.toml        → Python (Poetry, modern Python)
Cargo.toml            → Rust (Actix, Rocket)
go.mod                → Go
pom.xml / build.gradle → Java (Spring, Quarkus)
```

### Dependency Analysis
Parsed from manifest files to identify specific frameworks:
- `package.json` → `dependencies` and `devDependencies` keys
- `pyproject.toml` → `[project.dependencies]` section
- `requirements.txt` → line-by-line parsing

### Pattern Detection
Framework-specific code patterns in source files:
- **FastAPI**: `@app.get()`, `APIRouter`, `Depends()`
- **Django**: `models.Model`, `views.py`, `settings.py`
- **Flask**: `@app.route`, `Blueprint`
- **React**: JSX components, `useState`, `useEffect`
- **Next.js**: `pages/` or `app/` router, `getServerSideProps`

### Confidence Score
Each framework detection includes a confidence score (0.0-1.0) based on:
- Number of evidence signals found
- Strength of each signal
- Absence of conflicting signals

## AST Parsing Approach

The engine uses [tree-sitter](https://tree-sitter.github.io/) for robust, incremental parsing of source code.

### Why Tree-Sitter
- **Incremental**: Re-parsing is efficient when files change
- **Error-tolerant**: Produces partial AST even for syntactically invalid code
- **Multi-language**: Single API for 50+ languages
- **Fast**: Written in C, bindings available for Python

### Supported Languages for AST
| Language | Package |
|----------|---------|
| Python | `tree-sitter-python` |
| JavaScript | `tree-sitter-javascript` |
| TypeScript | `tree-sitter-typescript` |
| Java | `tree-sitter-java` |
| Go | `tree-sitter-go` |
| Rust | `tree-sitter-rust` |

### Fallback Strategy
When tree-sitter is unavailable, the engine falls back to:
- Regex-based pattern matching for code elements
- Simple heuristics for function/class detection
- Reduced accuracy but functional analysis

### Extracted Code Elements
- **Functions/Methods**: Name, parameters, return type, decorators
- **Classes**: Name, parent class, methods, docstrings
- **Imports**: Source, target, type (relative, absolute)
- **Exports**: Public API surface
- **Decorators**: Applied to functions and classes

## Database Detection

Database models are detected through ORM patterns:

### Python ORMs
| ORM | Detection Pattern |
|-----|-------------------|
| SQLAlchemy | `Column()`, `relationship()`, `Base` |
| Django ORM | `models.Model`, `models.Field` |
| Tortoise ORM | `Model`, `fields` |

### Other ORMs
| ORM | Detection Pattern |
|-----|-------------------|
| Sequelize | `DataTypes`, `define()` |
| TypeORM | `@Entity`, `@Column` |
| Prisma | `prisma/schema.prisma` |
| ActiveRecord | `ActiveRecord::Base` |

### Detection Strategy
1. Scan for ORM-specific base class imports
2. Find class definitions inheriting from ORM base
3. Extract field definitions and relationships
4. Map primary/foreign keys

## Route Detection

API routes are detected through framework-specific patterns:

### FastAPI
```python
@app.get("/users")
@app.post("/users")
@router.get("/users/{id}")
```

### Django
```python
path("users/", views.user_list),
re_path(r"^users/(?P<id>\d+)$", views.user_detail),
```

### Express.js
```javascript
app.get("/users", handler);
router.post("/users", handler);
```

### Detected Route Information
- HTTP method (GET, POST, PUT, DELETE, etc.)
- URL path with parameters
- Handler function name
- File path and line number
- Authentication middleware
- Request/response models

## Architecture Analysis

The engine classifies the overall project architecture:

### Detected Styles

| Style | Indicators |
|-------|-----------|
| **MVC** | `models/`, `views/`, `controllers/` directories |
| **Clean** | `domain/`, `application/`, `infrastructure/` layers |
| **Layered** | `controllers/`, `services/`, `repositories/` |
| **Microservices** | Multiple `docker-compose` services, independent packages |
| **Serverless** | `serverless.yml`, `handler.py`, `functions/` |
| **Monolith** | Single deployment unit, shared database |

### Analysis Signals
- Directory structure conventions
- File naming patterns
- Import/dependency graph between modules
- Configuration file presence
- Deployment configurations (Docker, Kubernetes, etc.)

## Semantic Graph Structure

The semantic graph represents the repository as a network of interconnected nodes and edges.

### Node Types

| Type | Description | Metadata |
|------|-------------|----------|
| `repository` | Root node | name, url, branch |
| `folder` | Directory | path, purpose |
| `module` | Source file | language, size |
| `class` | Class definition | parent, methods |
| `function` | Function/method | parameters, returns |
| `route` | API endpoint | method, path |
| `database` | DB model | table, fields |
| `dependency` | External package | version, source |
| `config` | Configuration file | format, settings |

### Edge Types

| Relationship | Source → Target | Example |
|-------------|----------------|---------|
| `contains` | folder → module | src/ contains main.py |
| `imports` | module → module | main.py imports utils.py |
| `defines` | module → class | main.py defines User |
| `defines` | class → function | User defines __init__ |
| `calls` | function → function | save() calls validate() |
| `extends` | class → class | Admin extends User |
| `uses` | module → dependency | main.py uses requests |
| `serves` | route → function | GET /users serves list_users |
| `maps_to` | class → database | User maps_to users table |

### Graph Traversal Use Cases
- **Impact Analysis**: Find all affected code when changing a function
- **Dependency Chains**: Trace import chains across modules
- **Code Navigation**: Jump from route to handler to service to database
- **Dead Code Detection**: Identify unreachable functions/classes
- **Complexity Analysis**: Measure coupling between modules

## Supported Languages and Frameworks

### Fully Supported (AST Parsing)
| Language | AST | Frameworks Detected |
|----------|-----|-------------------|
| Python | ✅ | FastAPI, Django, Flask, SQLAlchemy |
| JavaScript | ✅ | Express, React, Vue, Angular, Next.js, Node.js |
| TypeScript | ✅ | Express, React, Vue, Angular, Next.js, NestJS |
| Java | ✅ | Spring, Quarkus, Micronaut |
| Go | ✅ | Gin, Echo, Fiber, Chi |
| Rust | ✅ | Actix, Rocket, Axum |

### Partially Supported (Regex/Heuristic)
| Language | Frameworks Detected |
|----------|-------------------|
| C# | ASP.NET, Entity Framework |
| Ruby | Rails, Sinatra |
| PHP | Laravel, Symfony |
| Swift | Vapor |
| Kotlin | Ktor, Spring Boot |
| Scala | Play, Akka HTTP |

## Extension Guide

### Adding a New Language

1. Create a new file in `backend/app/repo_intelligence/analyzers/`:

```python
"""Language analyzer for NewLang."""

from app.repo_intelligence.schemas.repository import LanguageInfo


class NewLangAnalyzer:
    """Analyzer for NewLang source files."""

    LANGUAGE_NAME = "NewLang"
    EXTENSIONS = [".nl", ".nlang"]

    def detect(self, file_path: str, content: str) -> bool:
        """Detect if a file is NewLang."""
        return any(file_path.endswith(ext) for ext in self.EXTENSIONS)

    def analyze(self, file_path: str, content: str) -> dict:
        """Analyze a NewLang file."""
        lines = content.splitlines()
        return {
            "language": self.LANGUAGE_NAME,
            "lines": len(lines),
            "functions": self._extract_functions(content),
            "classes": self._extract_classes(content),
        }
```

2. Register the language in the language detector:

```python
# In the language detection module
from app.repo_intelligence.analyzers.newlang import NewLangAnalyzer

LANGUAGE_DETECTORS = {
    # ... existing languages
    "NewLang": NewLangAnalyzer(),
}
```

3. Add tree-sitter grammar (optional, for AST support):

```bash
pip install tree-sitter-newlang
```

4. Add grammar mapping in the AST parser:

```python
GRAMMAR_MAP = {
    # ... existing grammars
    ".nl": "newlang",
    ".nlang": "newlang",
}
```

### Adding a New Framework

1. Create a detection rule:

```python
"""Framework detection rules for NewFramework."""

FRAMEWORK_RULES = {
    "NewFramework": {
        "config_files": ["newframework.config.js"],
        "dependencies": ["newframework"],
        "patterns": [
            r"@nf\.route\(",
            r"from newframework import",
        ],
        "confidence_boost": 0.2,
    }
}
```

2. Add the rule to the framework detector:

```python
# In framework detection module
from app.repo_intelligence.analyzers.frameworks.newframework import FRAMEWORK_RULES

FRAMEWORK_RULES.update(FRAMEWORK_RULES)
```

## API Reference

### Repository Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/repositories` | Create/import a repository |
| `GET` | `/api/v1/repositories` | List all repositories |
| `GET` | `/api/v1/repositories/{id}` | Get repository details |
| `DELETE` | `/api/v1/repositories/{id}` | Delete a repository |
| `POST` | `/api/v1/repositories/{id}/analyze` | Trigger analysis |
| `GET` | `/api/v1/repositories/{id}/analysis` | Get analysis results |

### Graph Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/repositories/{id}/graph` | Get semantic graph |
| `GET` | `/api/v1/repositories/{id}/graph/nodes` | Get all nodes |
| `GET` | `/api/v1/repositories/{id}/graph/edges` | Get all edges |
| `GET` | `/api/v1/repositories/{id}/graph/search` | Search the graph |

### Configuration

Configuration is managed via environment variables with the `REPO_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `REPO_MAX_REPOSITORY_SIZE_MB` | `500` | Maximum repository size in MB |
| `REPO_MAX_FILE_SIZE_KB` | `1024` | Maximum individual file size in KB |
| `REPO_MAX_FILES_TO_ANALYZE` | `10000` | Maximum files to analyze |
| `REPO_GIT_TIMEOUT` | `60` | Git clone timeout in seconds |
| `REPO_TEMP_DIR` | `/tmp/forgeai/repos` | Temporary repository storage |

### Error Responses

All endpoints return standard error responses:

```json
{
  "detail": {
    "code": "REPOSITORY_NOT_FOUND",
    "message": "Repository with ID abc123 not found",
    "status": 404
  }
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `REPOSITORY_NOT_FOUND` | 404 | Repository does not exist |
| `REPOSITORY_TOO_LARGE` | 413 | Exceeds size limits |
| `IMPORT_FAILED` | 500 | Import operation failed |
| `ANALYSIS_FAILED` | 500 | Analysis pipeline failed |
| `UNSUPPORTED_LANGUAGE` | 422 | Language not supported |
| `INVALID_REPOSITORY` | 422 | Invalid repository structure |
| `GIT_CLONE_FAILED` | 500 | Git clone operation failed |

---

*For API usage examples, see [Repository-API.md](Repository-API.md).*
