# scanners/sca/parsers.py
import json
import re
from typing import List, Dict
from xml.etree import ElementTree as ET

class Dependency:
    """의존성 정보"""
    def __init__(self, name: str, version: str, dep_type: str = "runtime"):
        self.name = name
        self.version = version
        self.dep_type = dep_type

class NPMParser:
    """package.json 파서"""
    
    def parse(self, file_path: str) -> List[Dependency]:
        """package.json 파싱"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dependencies = []
        
        # dependencies
        for name, version in data.get('dependencies', {}).items():
            dependencies.append(Dependency(name, version, "runtime"))
        
        # devDependencies
        for name, version in data.get('devDependencies', {}).items():
            dependencies.append(Dependency(name, version, "dev"))
        
        return dependencies

class PipParser:
    """requirements.txt 파서"""
    
    def parse(self, file_path: str) -> List[Dependency]:
        """requirements.txt 파싱"""
        dependencies = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 주석 및 빈 줄 무시
                if not line or line.startswith('#'):
                    continue
                
                # 패키지명과 버전 분리
                match = re.match(r'([a-zA-Z0-9\-_]+)(==|>=|<=|~=|>|<)?(.+)?', line)
                if match:
                    name = match.group(1)
                    version = match.group(3) if match.group(3) else "unknown"
                    dependencies.append(Dependency(name, version, "runtime"))
        
        return dependencies

class MavenParser:
    """pom.xml 파서"""
    
    def parse(self, file_path: str) -> List[Dependency]:
        """pom.xml 파싱"""
        dependencies = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # 네임스페이스 처리
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            # dependencies 찾기
            for dep in root.findall('.//maven:dependency', ns):
                group_id = dep.find('maven:groupId', ns)
                artifact_id = dep.find('maven:artifactId', ns)
                version = dep.find('maven:version', ns)
                
                if group_id is not None and artifact_id is not None:
                    name = f"{group_id.text}.{artifact_id.text}"
                    ver = version.text if version is not None else "unknown"
                    dependencies.append(Dependency(name, ver, "runtime"))
        
        except Exception as e:
            print(f"⚠️  Error parsing pom.xml: {e}")
        
        return dependencies

class GoModParser:
    """go.mod 파서"""
    
    def parse(self, file_path: str) -> List[Dependency]:
        """go.mod 파싱"""
        dependencies = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            in_require_block = False
            
            for line in f:
                line = line.strip()
                
                if line.startswith('require ('):
                    in_require_block = True
                    continue
                
                if in_require_block:
                    if line == ')':
                        in_require_block = False
                        continue
                    
                    # 패키지명 버전 파싱
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        dependencies.append(Dependency(name, version, "runtime"))
        
        return dependencies

# 파서 매핑
PARSERS = {
    "package.json": NPMParser(),
    "requirements.txt": PipParser(),
    "pom.xml": MavenParser(),
    "go.mod": GoModParser(),
}