from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from enum import Enum


class PluginTemplateType(Enum):
    agent = "agent"
    tool = "tool"
    workflow = "workflow"
    prompt = "prompt"
    ui = "ui"
    integration = "integration"


@dataclass
class PluginTemplate:
    id: str
    name: str
    description: str
    type: PluginTemplateType
    files: dict[str, str]
    dependencies: list[str] = field(default_factory=list)
    setup_commands: list[str] = field(default_factory=list)


class PluginTemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, PluginTemplate] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        templates = [
            PluginTemplate(
                id="agent-plugin",
                name="Agent Plugin",
                description="Template for creating autonomous AI agents with tool usage and reasoning.",
                type=PluginTemplateType.agent,
                dependencies=["forge-core"],
                setup_commands=["pip install -r requirements.txt"],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "agent",
  "permissions": [],
  "dependencies": [],
  "entry_point": "main",
  "tags": []
}""",
                    "main.py": """from forge_core import AgentPlugin


class Plugin(AgentPlugin):
    def initialize(self) -> None:
        self.register_tool("example_tool", self.example_tool)
        print(f"Agent plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("Agent plugin shutdown")

    def example_tool(self, input_data: dict) -> dict:
        return {"result": "Hello from {{PLUGIN_NAME}}"}

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "My Agent"},
                "max_iterations": {"type": "integer", "default": 10},
            },
        }
""",
                    "README.md": """# {{PLUGIN_NAME}}

An autonomous AI agent plugin for ForgeAI.

## Features

- Tool registration and usage
- Reasoning and planning capabilities
- Configurable behavior

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| name | string | My Agent | Agent display name |
| max_iterations | integer | 10 | Maximum reasoning iterations |

## Usage

```python
from forge_core import get_plugin
agent = get_plugin("{{PLUGIN_ID}}")
result = agent.example_tool({"query": "hello"})
```
""",
                    "config.json": """{
  "name": "My Agent",
  "max_iterations": 10
}""",
                    "tests/test_plugin.py": """import pytest


def test_plugin_initialization():
    assert True


def test_example_tool():
    assert True
""",
                },
            ),
            PluginTemplate(
                id="tool-plugin",
                name="Tool Plugin",
                description="Template for creating developer tools, utilities, and CLI extensions.",
                type=PluginTemplateType.tool,
                dependencies=["forge-core"],
                setup_commands=["pip install -r requirements.txt"],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "tool",
  "permissions": [],
  "dependencies": [],
  "entry_point": "main",
  "tags": []
}""",
                    "main.py": """from forge_core import ToolPlugin


class Plugin(ToolPlugin):
    def initialize(self) -> None:
        self.register_command("run", self.run)
        print(f"Tool plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("Tool plugin shutdown")

    def run(self, args: dict) -> dict:
        return {"output": "Tool executed successfully", "args": args}

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "verbose": {"type": "boolean", "default": False},
            },
        }
""",
                    "README.md": """# {{PLUGIN_NAME}}

A developer tool plugin for ForgeAI.

## Features

- Command registration
- Configurable output
- Easy integration

## Usage

```python
from forge_core import get_plugin
tool = get_plugin("{{PLUGIN_ID}}")
result = tool.run({"input": "test"})
```
""",
                    "config.json": """{
  "verbose": false
}""",
                    "tests/test_plugin.py": """import pytest


def test_plugin_initialization():
    assert True


def test_run_command():
    assert True
""",
                },
            ),
            PluginTemplate(
                id="workflow-plugin",
                name="Workflow Plugin",
                description="Template for creating automation workflows and pipelines.",
                type=PluginTemplateType.workflow,
                dependencies=["forge-core"],
                setup_commands=["pip install -r requirements.txt"],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "workflow",
  "permissions": [],
  "dependencies": [],
  "entry_point": "main",
  "tags": []
}""",
                    "main.py": """from forge_core import WorkflowPlugin


class Plugin(WorkflowPlugin):
    def initialize(self) -> None:
        self.register_step("validate", self.validate)
        self.register_step("process", self.process)
        self.register_step("finalize", self.finalize)
        print(f"Workflow plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("Workflow plugin shutdown")

    def validate(self, context: dict) -> dict:
        context["validated"] = True
        return context

    def process(self, context: dict) -> dict:
        context["processed"] = True
        return context

    def finalize(self, context: dict) -> dict:
        context["completed"] = True
        return context

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "retry_on_failure": {"type": "boolean", "default": True},
                "timeout_seconds": {"type": "integer", "default": 300},
            },
        }
""",
                    "README.md": """# {{PLUGIN_NAME}}

An automation workflow plugin for ForgeAI.

## Steps

1. **validate** - Validates input context
2. **process** - Processes the data
3. **finalize** - Completes the workflow

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| retry_on_failure | boolean | true | Retry failed steps |
| timeout_seconds | integer | 300 | Maximum execution time |
""",
                    "config.json": """{
  "retry_on_failure": true,
  "timeout_seconds": 300
}""",
                    "tests/test_workflow.py": """import pytest


def test_workflow_steps():
    assert True
""",
                },
            ),
            PluginTemplate(
                id="prompt-plugin",
                name="Prompt Plugin",
                description="Template for creating prompt templates and prompt engineering packs.",
                type=PluginTemplateType.prompt,
                dependencies=["forge-core"],
                setup_commands=[],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "prompt",
  "permissions": [],
  "dependencies": [],
  "entry_point": "main",
  "tags": []
}""",
                    "main.py": """from forge_core import PromptPlugin


PROMPTS = {
    "summarize": "Summarize the following text concisely:\\n\\n{{text}}",
    "analyze": "Analyze the following and provide insights:\\n\\n{{input}}",
    "generate": "Generate content based on: {{instruction}}\\n\\nContext: {{context}}",
}


class Plugin(PromptPlugin):
    def initialize(self) -> None:
        for name, template in PROMPTS.items():
            self.register_prompt(name, template)
        print(f"Prompt plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("Prompt plugin shutdown")

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "default_model": {"type": "string", "default": "gpt-4"},
                "temperature": {"type": "number", "default": 0.7},
            },
        }
""",
                    "README.md": """# {{PLUGIN_NAME}}

A prompt template pack for ForgeAI.

## Included Prompts

- **summarize** - Summarize text concisely
- **analyze** - Analyze input for insights
- **generate** - Generate content from instructions

## Usage

```python
from forge_core import get_plugin
prompts = get_plugin("{{PLUGIN_ID}}")
result = prompts.render("summarize", text="Your long text here...")
```
""",
                    "config.json": """{
  "default_model": "gpt-4",
  "temperature": 0.7
}""",
                    "tests/test_prompts.py": """import pytest


def test_prompt_rendering():
    assert True
""",
                },
            ),
            PluginTemplate(
                id="ui-plugin",
                name="UI Component Plugin",
                description="Template for creating custom UI components and frontend extensions.",
                type=PluginTemplateType.ui,
                dependencies=["forge-core", "forge-ui"],
                setup_commands=["npm install"],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "ui",
  "permissions": [],
  "dependencies": [],
  "entry_point": "main",
  "frontend_entry": "index.ts",
  "tags": []
}""",
                    "main.py": """from forge_core import UIPlugin


class Plugin(UIPlugin):
    def initialize(self) -> None:
        self.register_component("{{PLUGIN_ID}}", {
            "name": "{{PLUGIN_NAME}}",
            "component": "MainComponent",
        })
        print(f"UI plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("UI plugin shutdown")

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "default": "light"},
            },
        }
""",
                    "index.ts": """import React from 'react';

interface {{PLUGIN_ID}}Props {
  data?: any;
}

export const MainComponent: React.FC<{{PLUGIN_ID}}Props> = ({ data }) => {
  return (
    <div className="forge-plugin-{{PLUGIN_ID}}">
      <h2>{{PLUGIN_NAME}}</h2>
      <p>Plugin component rendered successfully</p>
    </div>
  );
};

export default MainComponent;
""",
                    "README.md": """# {{PLUGIN_NAME}}

A UI component plugin for ForgeAI.

## Components

- **MainComponent** - Primary plugin component

## Props

| Prop | Type | Description |
|------|------|-------------|
| data | any | Optional data to display |

## Development

```bash
npm install
npm run dev
```
""",
                    "config.json": """{
  "theme": "light"
}""",
                    "tests/test_component.py": """import pytest


def test_component_renders():
    assert True
""",
                },
            ),
            PluginTemplate(
                id="integration-plugin",
                name="Integration Plugin",
                description="Template for creating external service integrations and API connectors.",
                type=PluginTemplateType.integration,
                dependencies=["forge-core", "httpx"],
                setup_commands=["pip install -r requirements.txt"],
                files={
                    "manifest.json": """{
  "id": "{{PLUGIN_ID}}",
  "name": "{{PLUGIN_NAME}}",
  "version": "0.1.0",
  "author": "{{AUTHOR}}",
  "description": "{{DESCRIPTION}}",
  "category": "integration",
  "permissions": [],
  "dependencies": ["httpx"],
  "entry_point": "main",
  "tags": []
}""",
                    "main.py": """from forge_core import IntegrationPlugin


class Plugin(IntegrationPlugin):
    def initialize(self) -> None:
        self.base_url = self.config.get("base_url", "https://api.example.com")
        self.api_key = self.config.get("api_key", "")
        print(f"Integration plugin '{{self.config.get('name', 'unknown')}}' initialized")

    def shutdown(self) -> None:
        print("Integration plugin shutdown")

    async def request(self, method: str, path: str, **kwargs) -> dict:
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, f"{self.base_url}{path}", headers=headers, **kwargs
            )
            return response.json()

    def get_config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "base_url": {"type": "string", "default": "https://api.example.com"},
                "api_key": {"type": "string", "default": ""},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["api_key"],
        }
""",
                    "README.md": """# {{PLUGIN_NAME}}

An external service integration plugin for ForgeAI.

## Configuration

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| base_url | string | No | API base URL |
| api_key | string | Yes | API authentication key |
| timeout | integer | No | Request timeout in seconds |

## Usage

```python
from forge_core import get_plugin
integration = get_plugin("{{PLUGIN_ID}}")
result = await integration.request("GET", "/endpoint")
```
""",
                    "config.json": """{
  "base_url": "https://api.example.com",
  "api_key": "",
  "timeout": 30
}""",
                    "tests/test_integration.py": """import pytest


def test_plugin_initialization():
    assert True
""",
                },
            ),
        ]

        for template in templates:
            self._templates[template.id] = template

    def get_template(self, template_id: str) -> PluginTemplate | None:
        return self._templates.get(template_id)

    def list_templates(
        self, template_type: PluginTemplateType | None = None
    ) -> list[PluginTemplate]:
        if template_type is None:
            return list(self._templates.values())
        return [t for t in self._templates.values() if t.type == template_type]

    def generate_plugin(
        self, template_id: str, plugin_name: str, output_dir: str
    ) -> dict:
        template = self._templates.get(template_id)
        if template is None:
            return {"success": False, "error": f"Template '{template_id}' not found"}

        if not self.validate_name(plugin_name):
            return {"success": False, "error": f"Invalid plugin name: '{plugin_name}'"}

        plugin_id = plugin_name.lower().replace(" ", "-").replace("_", "-")
        plugin_id = re.sub(r"[^a-z0-9-]", "", plugin_id)
        plugin_id = f"forge-{plugin_id}" if not plugin_id.startswith("forge-") else plugin_id

        try:
            os.makedirs(output_dir, exist_ok=True)

            for file_path, content in template.files.items():
                full_path = os.path.join(output_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                content = content.replace("{{PLUGIN_ID}}", plugin_id)
                content = content.replace("{{PLUGIN_NAME}}", plugin_name)
                content = content.replace("{{DESCRIPTION}}", f"A {template.type.value} plugin for ForgeAI")
                content = content.replace("{{AUTHOR}}", "ForgeAI Developer")

                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return {
                "success": True,
                "plugin_id": plugin_id,
                "plugin_name": plugin_name,
                "template_id": template_id,
                "output_dir": output_dir,
                "files_created": list(template.files.keys()),
                "dependencies": template.dependencies,
                "setup_commands": template.setup_commands,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_template_files(self, template_id: str) -> dict:
        template = self._templates.get(template_id)
        if template is None:
            return {}
        return dict(template.files)

    def validate_name(self, name: str) -> bool:
        if not name or len(name.strip()) == 0:
            return False
        if len(name) > 64:
            return False
        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\s_-]*$"
        return bool(re.match(pattern, name))


plugin_template_registry = PluginTemplateRegistry()
