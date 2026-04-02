import json
import re
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


class Dependency:
    """Dependency metadata extracted from a manifest."""

    def __init__(self, name: str, version: str, dep_type: str = "runtime"):
        self.name = name
        self.version = version
        self.dep_type = dep_type


class NPMParser:
    """Parse package.json files."""

    def parse(self, file_path: str) -> List[Dependency]:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        dependencies = []

        for name, version in data.get("dependencies", {}).items():
            dependencies.append(Dependency(name, version, "runtime"))

        for name, version in data.get("devDependencies", {}).items():
            dependencies.append(Dependency(name, version, "dev"))

        return dependencies


class PipParser:
    """Parse requirements.txt files."""

    def parse(self, file_path: str) -> List[Dependency]:
        dependencies = []

        with open(file_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                match = re.match(r"([a-zA-Z0-9_.-]+)(==|>=|<=|~=|>|<)?(.+)?", line)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else "unknown"
                    dependencies.append(Dependency(name, version, "runtime"))

        return dependencies


class MavenParser:
    """Parse pom.xml files."""

    def parse(self, file_path: str) -> List[Dependency]:
        dependencies = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            ns = {"maven": "http://maven.apache.org/POM/4.0.0"}

            for dep in root.findall(".//maven:dependency", ns):
                group_id = dep.find("maven:groupId", ns)
                artifact_id = dep.find("maven:artifactId", ns)
                version = dep.find("maven:version", ns)

                if group_id is not None and artifact_id is not None:
                    name = f"{group_id.text}.{artifact_id.text}"
                    ver = version.text if version is not None else "unknown"
                    dependencies.append(Dependency(name, ver, "runtime"))

        except Exception as e:
            print(f"SCA parser error (pom.xml): {e}")

        return dependencies


class GoModParser:
    """Parse go.mod files."""

    def parse(self, file_path: str) -> List[Dependency]:
        dependencies = []

        with open(file_path, "r", encoding="utf-8") as f:
            in_require_block = False

            for line in f:
                line = line.strip()

                if line.startswith("require ("):
                    in_require_block = True
                    continue

                if in_require_block:
                    if line == ")":
                        in_require_block = False
                        continue

                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append(Dependency(parts[0], parts[1], "runtime"))

        return dependencies


class PyProjectParser:
    """Parse pyproject.toml files used by PEP 621, Poetry, or PDM."""

    def parse(self, file_path: str) -> List[Dependency]:
        data = _load_toml(file_path)
        dependencies: List[Dependency] = []

        project = data.get("project", {})
        for spec in project.get("dependencies", []) or []:
            dep = _dependency_from_spec(spec, "runtime")
            if dep:
                dependencies.append(dep)

        optional_dependencies = project.get("optional-dependencies", {}) or {}
        for specs in optional_dependencies.values():
            for spec in specs or []:
                dep = _dependency_from_spec(spec, "dev")
                if dep:
                    dependencies.append(dep)

        poetry = ((data.get("tool", {}) or {}).get("poetry", {}) or {})
        dependencies.extend(_parse_poetry_dependencies(poetry.get("dependencies", {}), "runtime"))
        dependencies.extend(_parse_poetry_dependencies(poetry.get("dev-dependencies", {}), "dev"))

        poetry_groups = poetry.get("group", {}) or {}
        for group_name, group_data in poetry_groups.items():
            dep_type = "dev" if group_name.lower() in {"dev", "test"} else "runtime"
            dependencies.extend(
                _parse_poetry_dependencies((group_data or {}).get("dependencies", {}), dep_type)
            )

        pdm = ((data.get("tool", {}) or {}).get("pdm", {}) or {})
        for spec in pdm.get("dependencies", []) or []:
            dep = _dependency_from_spec(spec, "runtime")
            if dep:
                dependencies.append(dep)

        return _dedupe_dependencies(dependencies)


class PipfileParser:
    """Parse Pipfile manifests."""

    def parse(self, file_path: str) -> List[Dependency]:
        data = _load_toml(file_path)
        dependencies: List[Dependency] = []
        dependencies.extend(_parse_key_value_dependencies(data.get("packages", {}), "runtime"))
        dependencies.extend(_parse_key_value_dependencies(data.get("dev-packages", {}), "dev"))
        return _dedupe_dependencies(dependencies)


class GradleParser:
    """Parse build.gradle and build.gradle.kts files."""

    _PATTERNS = [
        re.compile(
            r'^\s*(?P<scope>[A-Za-z][A-Za-z0-9]*)\s*\(?\s*[\'"](?P<group>[^:\'"]+):(?P<artifact>[^:\'"]+)(?::(?P<version>[^\'"]+))?[\'"]'
        ),
        re.compile(
            r'^\s*(?P<scope>[A-Za-z][A-Za-z0-9]*)\s*\(?\s*group\s*:\s*[\'"](?P<group>[^\'"]+)[\'"]\s*,\s*name\s*:\s*[\'"](?P<artifact>[^\'"]+)[\'"](?:\s*,\s*version\s*:\s*[\'"](?P<version>[^\'"]+)[\'"])?'
        ),
    ]

    def parse(self, file_path: str) -> List[Dependency]:
        dependencies: List[Dependency] = []

        with open(file_path, "r", encoding="utf-8-sig") as f:
            for raw_line in f:
                line = raw_line.split("//", 1)[0].strip()
                if not line:
                    continue

                dependency = self._parse_line(line)
                if dependency:
                    dependencies.append(dependency)

        return _dedupe_dependencies(dependencies)

    def _parse_line(self, line: str) -> Optional[Dependency]:
        for pattern in self._PATTERNS:
            match = pattern.search(line)
            if not match:
                continue

            scope = match.group("scope") or "runtime"
            dep_type = "dev" if "test" in scope.lower() else "runtime"
            name = f"{match.group('group')}.{match.group('artifact')}"
            version = (match.group("version") or "unknown").strip()
            return Dependency(name, version, dep_type)
        return None


def _load_toml(file_path: str) -> Dict[str, Any]:
    if tomllib is None:
        raise RuntimeError("tomllib is required to parse TOML dependency manifests.")

    with open(file_path, "rb") as f:
        return tomllib.load(f)


def _dependency_from_spec(spec: str, dep_type: str) -> Optional[Dependency]:
    normalized = (spec or "").strip()
    if not normalized:
        return None

    if ";" in normalized:
        normalized = normalized.split(";", 1)[0].strip()

    match = re.match(r"([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*(.*)", normalized)
    if not match:
        return None

    name = match.group(1)
    version = match.group(2).strip() or "unknown"
    return Dependency(name, version, dep_type)


def _parse_poetry_dependencies(section: Dict[str, Any], dep_type: str) -> List[Dependency]:
    dependencies: List[Dependency] = []

    for name, value in (section or {}).items():
        if name.lower() == "python":
            continue

        if isinstance(value, str):
            version = value or "unknown"
        elif isinstance(value, dict):
            version = (
                value.get("version")
                or value.get("ref")
                or value.get("branch")
                or value.get("git")
                or "unknown"
            )
        else:
            version = "unknown"

        dependencies.append(Dependency(name, str(version), dep_type))

    return dependencies


def _parse_key_value_dependencies(section: Dict[str, Any], dep_type: str) -> List[Dependency]:
    dependencies: List[Dependency] = []

    for name, value in (section or {}).items():
        if isinstance(value, str):
            version = value or "unknown"
        elif isinstance(value, dict):
            version = value.get("version") or "unknown"
        else:
            version = "unknown"

        dependencies.append(Dependency(name, str(version), dep_type))

    return dependencies


def _dedupe_dependencies(dependencies: List[Dependency]) -> List[Dependency]:
    seen = set()
    deduped: List[Dependency] = []

    for dep in dependencies:
        key = (dep.name.lower(), dep.version, dep.dep_type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(dep)

    return deduped


PARSERS = {
    "package.json": NPMParser(),
    "requirements.txt": PipParser(),
    "pipfile": PipfileParser(),
    "pyproject.toml": PyProjectParser(),
    "pom.xml": MavenParser(),
    "build.gradle": GradleParser(),
    "build.gradle.kts": GradleParser(),
    "go.mod": GoModParser(),
}
