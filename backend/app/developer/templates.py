"""Project and code templates."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TemplateCategory(Enum):
    PROJECT = "project"
    WORKFLOW = "workflow"
    AGENT = "agent"
    PROMPT = "prompt"
    PLUGIN = "plugin"


@dataclass
class Template:
    id: str
    name: str
    description: str
    category: TemplateCategory
    language: str
    files: dict[str, str]
    dependencies: list[str] = field(default_factory=list)
    setup_commands: list[str] = field(default_factory=list)


class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, Template] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        project_templates = [
            Template(
                id="fastapi",
                name="FastAPI Backend",
                description="Production-ready FastAPI backend with async support, Pydantic models, and auto-generated docs",
                category=TemplateCategory.PROJECT,
                language="python",
                files={
                    "main.py": (
                        "from fastapi import FastAPI\nfrom pydantic import BaseModel\n\n"
                        "app = FastAPI(title='ForgeAI Project')\n\n"
                        "class HealthResponse(BaseModel):\n"
                        "    status: str\n\n"
                        "@app.get('/health', response_model=HealthResponse)\n"
                        "async def health_check():\n"
                        "    return HealthResponse(status='ok')\n\n"
                        "if __name__ == '__main__':\n"
                        "    import uvicorn\n"
                        "    uvicorn.run(app, host='0.0.0.0', port=8000)\n"
                    ),
                    "requirements.txt": "fastapi>=0.100.0\nuvicorn>=0.23.0\npydantic>=2.0.0\n",
                    "Dockerfile": (
                        "FROM python:3.11-slim\nWORKDIR /app\n"
                        "COPY requirements.txt .\nRUN pip install -r requirements.txt\n"
                        "COPY . .\nCMD [\"python\", \"main.py\"]\n"
                    ),
                },
                dependencies=["fastapi", "uvicorn", "pydantic"],
                setup_commands=["pip install -r requirements.txt"],
            ),
            Template(
                id="nextjs",
                name="Next.js Frontend",
                description="Next.js 14+ frontend with App Router, Server Components, and Tailwind CSS",
                category=TemplateCategory.PROJECT,
                language="typescript",
                files={
                    "package.json": (
                        '{\n  "name": "forge-project",\n  "version": "0.1.0",\n'
                        '  "scripts": { "dev": "next dev", "build": "next build", "start": "next start" },\n'
                        '  "dependencies": { "next": "^14.0.0", "react": "^18.0.0", "react-dom": "^18.0.0" }\n'
                        '}\n'
                    ),
                    "app/layout.tsx": (
                        "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
                        "    return (\n"
                        "        <html lang='en'>\n"
                        "            <body>{children}</body>\n"
                        "        </html>\n"
                        "    );\n"
                        "}\n"
                    ),
                    "app/page.tsx": (
                        "export default function Home() {\n"
                        "    return (\n"
                        "        <main className='flex min-h-screen items-center justify-center'>\n"
                        "            <h1 className='text-4xl font-bold'>ForgeAI Project</h1>\n"
                        "        </main>\n"
                        "    );\n"
                        "}\n"
                    ),
                    "next.config.js": "/** @type {import('next').NextConfig} */\nconst nextConfig = {};\nmodule.exports = nextConfig;\n",
                },
                dependencies=["next", "react", "react-dom"],
                setup_commands=["npm install"],
            ),
            Template(
                id="react",
                name="React SPA",
                description="React single-page application with Vite, TypeScript, and React Router",
                category=TemplateCategory.PROJECT,
                language="typescript",
                files={
                    "package.json": (
                        '{\n  "name": "forge-react",\n  "version": "0.1.0",\n'
                        '  "scripts": { "dev": "vite", "build": "vite build" },\n'
                        '  "dependencies": { "react": "^18.0.0", "react-dom": "^18.0.0", "react-router-dom": "^6.0.0" },\n'
                        '  "devDependencies": { "vite": "^5.0.0", "@vitejs/plugin-react": "^4.0.0", "typescript": "^5.0.0" }\n'
                        '}\n'
                    ),
                    "src/App.tsx": (
                        "import { BrowserRouter, Routes, Route } from 'react-router-dom';\n\n"
                        "function App() {\n"
                        "    return (\n"
                        "        <BrowserRouter>\n"
                        "            <Routes>\n"
                        "                <Route path='/' element={<h1>ForgeAI React App</h1>} />\n"
                        "            </Routes>\n"
                        "        </BrowserRouter>\n"
                        "    );\n"
                        "}\n\n"
                        "export default App;\n"
                    ),
                    "src/main.tsx": (
                        "import React from 'react';\nimport ReactDOM from 'react-dom/client';\nimport App from './App';\n\n"
                        "ReactDOM.createRoot(document.getElementById('root')!).render(\n"
                        "    <React.StrictMode><App /></React.StrictMode>\n);\n"
                    ),
                    "vite.config.ts": "import { defineConfig } from 'vite';\nimport react from '@vitejs/plugin-react';\n\nexport default defineConfig({ plugins: [react()] });\n",
                },
                dependencies=["react", "react-dom", "react-router-dom"],
                setup_commands=["npm install"],
            ),
            Template(
                id="express",
                name="Express.js API",
                description="Express.js REST API with middleware, routing, and error handling",
                category=TemplateCategory.PROJECT,
                language="typescript",
                files={
                    "package.json": (
                        '{\n  "name": "forge-express",\n  "version": "0.1.0",\n'
                        '  "scripts": { "dev": "ts-node src/index.ts", "build": "tsc" },\n'
                        '  "dependencies": { "express": "^4.18.0" },\n'
                        '  "devDependencies": { "typescript": "^5.0.0", "@types/express": "^4.17.0", "ts-node": "^10.0.0" }\n'
                        '}\n'
                    ),
                    "src/index.ts": (
                        "import express from 'express';\n\n"
                        "const app = express();\napp.use(express.json());\n\n"
                        "app.get('/health', (_req, res) => res.json({ status: 'ok' }));\n\n"
                        "app.listen(3000, () => console.log('Server running on port 3000'));\n"
                    ),
                    "tsconfig.json": '{\n  "compilerOptions": { "target": "ES2020", "module": "commonjs", "outDir": "./dist" }\n}\n',
                },
                dependencies=["express"],
                setup_commands=["npm install"],
            ),
            Template(
                id="spring-boot",
                name="Spring Boot",
                description="Spring Boot Java application with REST controllers and JPA",
                category=TemplateCategory.PROJECT,
                language="java",
                files={
                    "pom.xml": (
                        '<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
                        '  <modelVersion>4.0.0</modelVersion>\n'
                        '  <groupId>dev.forgeai</groupId>\n'
                        '  <artifactId>forge-project</artifactId>\n'
                        '  <version>0.1.0</version>\n'
                        '  <parent><groupId>org.springframework.boot</groupId>'
                        '<artifactId>spring-boot-starter-parent</artifactId><version>3.2.0</version></parent>\n'
                        '  <dependencies>\n'
                        '    <dependency><groupId>org.springframework.boot</groupId>'
                        '<artifactId>spring-boot-starter-web</artifactId></dependency>\n'
                        '  </dependencies>\n'
                        '</project>\n'
                    ),
                    "src/main/java/com/forgeai/Application.java": (
                        "package com.forgeai;\n\n"
                        "import org.springframework.boot.SpringApplication;\n"
                        "import org.springframework.boot.autoconfigure.SpringBootApplication;\n\n"
                        "@SpringBootApplication\n"
                        "public class Application {\n"
                        "    public static void main(String[] args) {\n"
                        "        SpringApplication.run(Application.class, args);\n"
                        "    }\n"
                        "}\n"
                    ),
                },
                dependencies=["spring-boot-starter-web"],
                setup_commands=["mvn spring-boot:run"],
            ),
            Template(
                id="node",
                name="Node.js CLI",
                description="Node.js command-line application with argument parsing",
                category=TemplateCategory.PROJECT,
                language="javascript",
                files={
                    "package.json": (
                        '{\n  "name": "forge-cli",\n  "version": "0.1.0",\n'
                        '  "scripts": { "start": "node src/index.js" },\n'
                        '  "bin": { "forge-cli": "./src/index.js" },\n'
                        '  "dependencies": { "commander": "^11.0.0" }\n'
                        '}\n'
                    ),
                    "src/index.js": (
                        "#!/usr/bin/env node\n"
                        "const { program } = require('commander');\n\n"
                        "program\n"
                        "    .name('forge-cli')\n"
                        "    .description('ForgeAI CLI tool')\n"
                        "    .version('0.1.0');\n\n"
                        "program\n"
                        "    .command('hello')\n"
                        "    .description('Say hello')\n"
                        "    .action(() => console.log('Hello from ForgeAI!'));\n\n"
                        "program.parse();\n"
                    ),
                },
                dependencies=["commander"],
                setup_commands=["npm install"],
            ),
        ]

        workflow_templates = [
            Template(
                id="code-review",
                name="Code Review Workflow",
                description="Automated code review workflow with AI analysis and feedback",
                category=TemplateCategory.WORKFLOW,
                language="yaml",
                files={
                    "workflow.yaml": (
                        "name: code-review\n"
                        "trigger:\n  type: pull_request\n  branches: [main]\n"
                        "steps:\n"
                        "  - name: fetch-changes\n    action: git.diff\n"
                        "  - name: analyze\n    action: agent.execute\n"
                        "    agent: code-reviewer\n    input: '{{steps.fetch-changes.output}}'\n"
                        "  - name: report\n    action: output.comment\n    input: '{{steps.analyze.output}}'\n"
                    ),
                },
                dependencies=[],
                setup_commands=[],
            ),
            Template(
                id="deployment",
                name="Deployment Workflow",
                description="CI/CD deployment workflow with build, test, and deploy stages",
                category=TemplateCategory.WORKFLOW,
                language="yaml",
                files={
                    "workflow.yaml": (
                        "name: deployment\n"
                        "trigger:\n  type: push\n  branches: [main]\n"
                        "steps:\n"
                        "  - name: build\n    action: exec.command\n    command: npm run build\n"
                        "  - name: test\n    action: exec.command\n    command: npm test\n"
                        "  - name: deploy\n    action: deploy.production\n    depends_on: [build, test]\n"
                    ),
                },
                dependencies=[],
                setup_commands=[],
            ),
            Template(
                id="testing",
                name="Testing Workflow",
                description="Automated testing workflow with unit, integration, and e2e tests",
                category=TemplateCategory.WORKFLOW,
                language="yaml",
                files={
                    "workflow.yaml": (
                        "name: testing\n"
                        "trigger:\n  type: pull_request\n"
                        "steps:\n"
                        "  - name: unit-tests\n    action: exec.command\n    command: npm run test:unit\n"
                        "  - name: integration-tests\n    action: exec.command\n    command: npm run test:integration\n"
                        "  - name: e2e-tests\n    action: exec.command\n    command: npm run test:e2e\n"
                    ),
                },
                dependencies=[],
                setup_commands=[],
            ),
        ]

        agent_templates = [
            Template(
                id="software-engineer",
                name="Software Engineer Agent",
                description="AI agent specialized in writing, debugging, and refactoring code",
                category=TemplateCategory.AGENT,
                language="python",
                files={
                    "agent.py": (
                        "from forgeai import Agent\n\n"
                        "agent = Agent(\n"
                        "    name='Software Engineer',\n"
                        "    model='gpt-4',\n"
                        "    system_prompt='You are an expert software engineer. Write clean, efficient code.',\n"
                        "    tools=['file_read', 'file_write', 'shell_exec']\n)\n"
                    ),
                },
                dependencies=["forgeai"],
                setup_commands=[],
            ),
            Template(
                id="code-reviewer",
                name="Code Reviewer Agent",
                description="AI agent specialized in reviewing code quality, security, and best practices",
                category=TemplateCategory.AGENT,
                language="python",
                files={
                    "agent.py": (
                        "from forgeai import Agent\n\n"
                        "agent = Agent(\n"
                        "    name='Code Reviewer',\n"
                        "    model='gpt-4',\n"
                        "    system_prompt='You are an expert code reviewer. Analyze code for issues and suggest improvements.',\n"
                        "    tools=['file_read']\n)\n"
                    ),
                },
                dependencies=["forgeai"],
                setup_commands=[],
            ),
            Template(
                id="devops",
                name="DevOps Agent",
                description="AI agent specialized in infrastructure, CI/CD, and deployment automation",
                category=TemplateCategory.AGENT,
                language="python",
                files={
                    "agent.py": (
                        "from forgeai import Agent\n\n"
                        "agent = Agent(\n"
                        "    name='DevOps Engineer',\n"
                        "    model='gpt-4',\n"
                        "    system_prompt='You are a DevOps expert. Manage infrastructure, CI/CD, and deployments.',\n"
                        "    tools=['shell_exec', 'file_read', 'file_write']\n)\n"
                    ),
                },
                dependencies=["forgeai"],
                setup_commands=[],
            ),
        ]

        all_templates = project_templates + workflow_templates + agent_templates
        for t in all_templates:
            self._templates[t.id] = t

    def register_template(self, template: Template) -> str:
        errors = self.validate_template(template)
        if errors:
            raise ValueError(f"Template validation failed: {', '.join(errors)}")
        if template.id in self._templates:
            raise ValueError(f"Template '{template.id}' is already registered")
        self._templates[template.id] = template
        return template.id

    def get_template(self, template_id: str) -> Template:
        if template_id not in self._templates:
            raise KeyError(f"Template '{template_id}' not found")
        return self._templates[template_id]

    def list_templates(self, category: TemplateCategory | None = None, language: str | None = None) -> list[Template]:
        templates = list(self._templates.values())
        if category is not None:
            templates = [t for t in templates if t.category == category]
        if language is not None:
            templates = [t for t in templates if t.language == language]
        return templates

    def generate_project(self, template_id: str, project_name: str, output_dir: str) -> dict:
        template = self.get_template(template_id)
        os.makedirs(output_dir, exist_ok=True)
        created_files: list[str] = []
        for rel_path, content in template.files.items():
            file_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(rel_path)
        return {
            "project_name": project_name,
            "template": template.name,
            "output_dir": output_dir,
            "files_created": created_files,
            "dependencies": template.dependencies,
            "setup_commands": template.setup_commands,
        }

    def get_template_files(self, template_id: str) -> dict:
        template = self.get_template(template_id)
        return template.files.copy()

    def validate_template(self, template: Template) -> list[str]:
        errors: list[str] = []
        if not template.name:
            errors.append("Template name is required")
        if not template.id:
            errors.append("Template id is required")
        if not template.files:
            errors.append("Template must contain at least one file")
        for rel_path in template.files:
            if rel_path.startswith("/") or rel_path.startswith("\\"):
                errors.append(f"File path '{rel_path}' must be relative")
            if ".." in rel_path:
                errors.append(f"File path '{rel_path}' must not contain '..'")
        return errors


template_registry = TemplateRegistry()
