"""Semantic graph builder."""

from app.repo_intelligence.schemas.analysis import CodeElement, DatabaseModelInfo, RouteInfo
from app.repo_intelligence.schemas.graph import GraphEdge, GraphNode, GraphNodeType, SemanticGraph
from app.repo_intelligence.schemas.repository import DependencyInfo, FolderInfo


class SemanticGraphBuilder:
    """Builds a semantic graph from analysis results."""

    def build(
        self,
        repository_id: str,
        repository_name: str,
        folder_structure: list[FolderInfo],
        code_elements: list[CodeElement],
        routes: list[RouteInfo],
        database_models: list[DatabaseModelInfo],
        dependencies: list[DependencyInfo],
        config_files: list[str],
    ) -> SemanticGraph:
        """Build a semantic graph from all analysis results.

        Args:
            repository_id: Unique repository identifier.
            repository_name: Repository name.
            folder_structure: List of folder information.
            code_elements: List of extracted code elements.
            routes: List of detected routes.
            database_models: List of detected database models.
            dependencies: List of detected dependencies.
            config_files: List of configuration file paths.

        Returns:
            Complete SemanticGraph object.
        """
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        repo_node = self._create_repository_node(repository_id, repository_name)
        nodes.append(repo_node)

        folder_nodes = self._create_folder_nodes(folder_structure)
        nodes.extend(folder_nodes)

        class_elements = [e for e in code_elements if e.type == "class"]
        function_elements = [e for e in code_elements if e.type in ("function", "method")]

        class_nodes = self._create_class_nodes(class_elements)
        nodes.extend(class_nodes)

        function_nodes = self._create_function_nodes(function_elements)
        nodes.extend(function_nodes)

        route_nodes = self._create_route_nodes(routes)
        nodes.extend(route_nodes)

        database_nodes = self._create_database_nodes(database_models)
        nodes.extend(database_nodes)

        dependency_nodes = self._create_dependency_nodes(dependencies)
        nodes.extend(dependency_nodes)

        config_nodes = self._create_config_nodes(config_files)
        nodes.extend(config_nodes)

        edges.extend(
            self._create_edges(
                repo_node,
                folder_nodes,
                class_nodes,
                function_nodes,
                route_nodes,
                database_nodes,
                dependency_nodes,
                config_nodes,
                folder_structure,
                code_elements,
                class_elements,
            )
        )

        return SemanticGraph(
            nodes=nodes,
            edges=edges,
            root_id=repo_node.id,
        )

    def _create_repository_node(self, repo_id: str, name: str) -> GraphNode:
        """Create the root repository node.

        Args:
            repo_id: Repository identifier.
            name: Repository name.

        Returns:
            GraphNode for the repository.
        """
        return GraphNode(
            id=f"repo:{repo_id}",
            type=GraphNodeType.REPOSITORY,
            name=name,
            metadata={"repository_id": repo_id},
        )

    def _create_folder_nodes(self, folders: list[FolderInfo]) -> list[GraphNode]:
        """Create nodes for folders.

        Args:
            folders: List of folder information.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for folder in folders:
            node_id = f"folder:{folder.path}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.FOLDER,
                    name=folder.name,
                    metadata={
                        "path": folder.path,
                        "purpose": folder.purpose,
                        "file_count": folder.file_count,
                    },
                )
            )
        return nodes

    def _create_class_nodes(self, elements: list[CodeElement]) -> list[GraphNode]:
        """Create nodes for classes.

        Args:
            elements: List of class code elements.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for element in elements:
            node_id = f"class:{element.file_path}:{element.name}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.CLASS,
                    name=element.name,
                    metadata={
                        "file_path": element.file_path,
                        "line_start": element.line_start,
                        "line_end": element.line_end,
                        "docstring": element.docstring,
                        "decorators": element.decorators,
                    },
                )
            )
        return nodes

    def _create_function_nodes(self, elements: list[CodeElement]) -> list[GraphNode]:
        """Create nodes for functions/methods.

        Args:
            elements: List of function code elements.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for element in elements:
            node_type = (
                GraphNodeType.FUNCTION
                if element.type == "function"
                else GraphNodeType.FUNCTION
            )
            node_id = f"func:{element.file_path}:{element.name}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=node_type,
                    name=element.name,
                    metadata={
                        "file_path": element.file_path,
                        "line_start": element.line_start,
                        "line_end": element.line_end,
                        "parent_class": element.parent_class,
                        "parameters": element.parameters,
                        "return_type": element.return_type,
                    },
                )
            )
        return nodes

    def _create_route_nodes(self, routes: list[RouteInfo]) -> list[GraphNode]:
        """Create nodes for API routes.

        Args:
            routes: List of detected routes.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for route in routes:
            node_id = f"route:{route.method}:{route.path}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.ROUTE,
                    name=f"{route.method} {route.path}",
                    metadata={
                        "method": route.method,
                        "path": route.path,
                        "function_name": route.function_name,
                        "file_path": route.file_path,
                        "line_number": route.line_number,
                    },
                )
            )
        return nodes

    def _create_database_nodes(
        self, models: list[DatabaseModelInfo]
    ) -> list[GraphNode]:
        """Create nodes for database models.

        Args:
            models: List of detected database models.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for model in models:
            node_id = f"db:{model.name}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.DATABASE,
                    name=model.name,
                    metadata={
                        "table_name": model.table_name,
                        "file_path": model.file_path,
                        "line_number": model.line_number,
                        "fields": [f.name for f in model.fields],
                    },
                )
            )
        return nodes

    def _create_dependency_nodes(
        self, deps: list[DependencyInfo]
    ) -> list[GraphNode]:
        """Create nodes for dependencies.

        Args:
            deps: List of detected dependencies.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for dep in deps:
            node_id = f"dep:{dep.name}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.DEPENDENCY,
                    name=dep.name,
                    metadata={
                        "version": dep.version,
                        "is_production": dep.is_production,
                        "source_file": dep.source_file,
                    },
                )
            )
        return nodes

    def _create_config_nodes(self, config_files: list[str]) -> list[GraphNode]:
        """Create nodes for configuration files.

        Args:
            config_files: List of configuration file paths.

        Returns:
            List of GraphNode objects.
        """
        nodes = []
        for file_path in config_files:
            node_id = f"config:{file_path}"
            nodes.append(
                GraphNode(
                    id=node_id,
                    type=GraphNodeType.CONFIG,
                    name=file_path,
                    metadata={"file_path": file_path},
                )
            )
        return nodes

    def _create_edges(
        self,
        repo_node: GraphNode,
        folder_nodes: list[GraphNode],
        class_nodes: list[GraphNode],
        function_nodes: list[GraphNode],
        route_nodes: list[GraphNode],
        database_nodes: list[GraphNode],
        dependency_nodes: list[GraphNode],
        config_nodes: list[GraphNode],
        folder_structure: list[FolderInfo],
        code_elements: list[CodeElement],
        class_elements: list[CodeElement],
    ) -> list[GraphEdge]:
        """Create edges between nodes based on relationships.

        Args:
            repo_node: Root repository node.
            folder_nodes: List of folder nodes.
            class_nodes: List of class nodes.
            function_nodes: List of function nodes.
            route_nodes: List of route nodes.
            database_nodes: List of database nodes.
            dependency_nodes: List of dependency nodes.
            config_nodes: List of config nodes.
            folder_structure: Folder structure information.
            code_elements: All code elements.
            class_elements: Class code elements only.

        Returns:
            List of GraphEdge objects.
        """
        edges: list[GraphEdge] = []

        for folder_node in folder_nodes:
            edges.append(
                GraphEdge(
                    source=repo_node.id,
                    target=folder_node.id,
                    relationship="contains",
                )
            )

        folder_map = {f.path: f for f in folder_structure}
        for folder in folder_structure:
            for child in folder.children:
                parent_id = f"folder:{folder.path}"
                child_id = f"folder:{child.path}"
                edges.append(
                    GraphEdge(
                        source=parent_id,
                        target=child_id,
                        relationship="contains",
                    )
                )

        class_map = {}
        for element in class_elements:
            node_id = f"class:{element.file_path}:{element.name}"
            class_map[element.name] = node_id

        function_class_map = {}
        for element in code_elements:
            if element.parent_class and element.parent_class in class_map:
                func_id = f"func:{element.file_path}:{element.name}"
                function_class_map[func_id] = class_map[element.parent_class]

        for func_id, class_id in function_class_map.items():
            edges.append(
                GraphEdge(
                    source=class_id,
                    target=func_id,
                    relationship="contains",
                )
            )

        for route in route_nodes:
            if route.metadata.get("function_name"):
                func_id = f"func:{route.metadata['file_path']}:{route.metadata['function_name']}"
                edges.append(
                    GraphEdge(
                        source=func_id,
                        target=route.id,
                        relationship="exposes",
                    )
                )

        for element in code_elements:
            if element.parent_class:
                class_id = class_map.get(element.parent_class)
                if class_id:
                    func_id = f"func:{element.file_path}:{element.name}"
                    if func_id in [n.id for n in function_nodes]:
                        edges.append(
                            GraphEdge(
                                source=class_id,
                                target=func_id,
                                relationship="contains",
                            )
                        )

        for element in class_elements:
            if element.imports:
                for imp in element.imports:
                    imp_class_id = class_map.get(imp)
                    if imp_class_id:
                        edges.append(
                            GraphEdge(
                                source=f"class:{element.file_path}:{element.name}",
                                target=imp_class_id,
                                relationship="imports",
                            )
                        )

        return edges
