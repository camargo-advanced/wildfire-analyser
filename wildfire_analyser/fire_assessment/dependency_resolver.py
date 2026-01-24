# SPDX-License-Identifier: MIT
#
# Dependency resolution utilities for the fire assessment pipeline.
#
# This module implements dependency resolution logic for the internal
# processing graph of the fire assessment pipeline. Given a set of requested
# dependencies, it computes the full transitive closure of required
# dependencies and returns them in a valid execution order.
#
# The resolution is performed using a depth-first traversal with cycle
# detection, producing a topologically sorted list suitable for sequential
# execution.
#
# Design notes:
# - Dependencies are resolved declaratively based on the dependency graph.
# - Execution order is deterministic and respects all prerequisite
#   constraints defined in the DAG.
# - Circular dependencies are explicitly detected and reported as errors.
#
# Responsibilities of this module:
# - Resolve dependency prerequisites recursively.
# - Detect and prevent circular dependency graphs.
# - Produce an ordered execution plan for the pipeline executor.
#
# This module does NOT:
# - Execute any processing logic or Earth Engine operations.
# - Define dependency relationships (see dependency_graph.py).
# - Expose user-facing deliverables.
#
# Copyright (C) 2025
# Marcelo Camargo.
#
# This file is part of wildfire-analyser and is distributed under the terms
# of the MIT license. See the LICENSE file for details.


from typing import List, Set
from wildfire_analyser.fire_assessment.dependency_graph import DEPENDENCY_GRAPH
from wildfire_analyser.fire_assessment.dependencies import Dependency


def resolve_dependencies(requested: List[Dependency]) -> List[Dependency]:
    """
    Given a list of requested dependencies, returns all required dependencies
    in a valid execution order (topological sort).
    """

    resolved: Set[Dependency] = set()
    temporary: Set[Dependency] = set()
    result: List[Dependency] = []

    def visit(dep: Dependency):
        if dep in resolved:
            return
        if dep in temporary:
            raise RuntimeError(f"Circular dependency detected: {dep}")

        temporary.add(dep)

        for parent in DEPENDENCY_GRAPH.get(dep, set()):
            visit(parent)

        temporary.remove(dep)
        resolved.add(dep)
        result.append(dep)

    for dependency in requested:
        visit(dependency)

    return result
