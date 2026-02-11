# language_detector/constants.py

# 확장자 → 언어 매핑
EXTENSION_LANGUAGE_MAP = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    
    # Java
    ".java": "java",
    
    # Go
    ".go": "go",
    
    # C/C++
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    
    # C#
    ".cs": "csharp",
    
    # Ruby
    ".rb": "ruby",
    
    # PHP
    ".php": "php",
    
    # Rust
    ".rs": "rust",
    
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    
    # Swift
    ".swift": "swift",
    
    # Shell
    ".sh": "shell",
    ".bash": "shell",
    
    # Configuration
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".toml": "toml",
    ".ini": "ini",
    ".conf": "config",
    ".config": "config",
    ".env": "env",
    
    # Certificates
    ".pem": "certificate",
    ".crt": "certificate",
    ".cer": "certificate",
    ".key": "private_key",
}

# 소스 코드 확장자
SOURCE_CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", 
    ".c", ".cpp", ".cc", ".cxx", ".cs", ".rb", ".php", 
    ".rs", ".kt", ".swift"
}

# 설정 파일 경로 패턴
CONFIG_PATHS = [
    "config/", "conf/", ".config/", "settings/",
    "nginx", "apache", "ssl", "tls"
]

# 의존성 파일명
DEPENDENCY_FILES = {
    # Node.js
    "package.json",
    "package-lock.json",
    "yarn.lock",
    
    # Python
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "setup.py",
    "pyproject.toml",
    
    # Java
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    
    # Go
    "go.mod",
    "go.sum",
    
    # Ruby
    "Gemfile",
    "Gemfile.lock",
    
    # Rust
    "Cargo.toml",
    "Cargo.lock",
}

# Dependency manifest -> language mapping (used for SCA)
DEPENDENCY_LANGUAGE_MAP = {
    "package.json": "javascript",
    "package-lock.json": "javascript",
    "yarn.lock": "javascript",
    "requirements.txt": "python",
    "Pipfile": "python",
    "Pipfile.lock": "python",
    "setup.py": "python",
    "pyproject.toml": "python",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "go.mod": "go",
    "go.sum": "go",
    "Gemfile": "ruby",
    "Gemfile.lock": "ruby",
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
}

# 무시할 디렉토리
IGNORE_DIRECTORIES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    "build",
    "dist",
    "target",  # Java/Rust
    ".gradle",
    "vendor",  # Go/Ruby
}

# 무시할 파일 패턴
IGNORE_FILE_PATTERNS = [
    r".*\.pyc$",
    r".*\.pyo$",
    r".*\.pyd$",
    r".*\.so$",
    r".*\.dll$",
    r".*\.dylib$",
    r".*\.exe$",
    r".*\.zip$",
    r".*\.tar\.gz$",
    r".*\.jpg$",
    r".*\.jpeg$",
    r".*\.png$",
    r".*\.gif$",
    r".*\.pdf$",
]
