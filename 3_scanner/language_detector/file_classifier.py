from models.file_metadata import FileMetadata, FileCategory
from .constants import CONFIG_PATHS, DEPENDENCY_FILES, SOURCE_CODE_EXTENSIONS


DEPENDENCY_FILES_LOWER = {name.lower() for name in DEPENDENCY_FILES}


class FileClassifier:
    """Classify repository files for downstream scanners."""

    def classify(self, metadata: FileMetadata) -> FileCategory:
        path_lower = metadata.file_path.lower().replace("\\", "/")
        ext = metadata.extension.lower()
        filename_lower = metadata.file_name.lower()

        if filename_lower in DEPENDENCY_FILES_LOWER:
            return FileCategory.DEPENDENCY_MANIFEST

        if self._is_config_file(path_lower, ext):
            return FileCategory.CONFIGURATION

        if ext in SOURCE_CODE_EXTENSIONS:
            return FileCategory.SOURCE_CODE

        if metadata.is_binary:
            return FileCategory.BINARY

        if ext in [".md", ".txt", ".rst", ".doc", ".docx"]:
            return FileCategory.DOCUMENTATION

        return FileCategory.UNKNOWN

    def _is_config_file(self, path: str, ext: str) -> bool:
        normalized_path = path.replace("\\", "/")

        for config_path in CONFIG_PATHS:
            if config_path in normalized_path:
                return True

        config_extensions = [
            ".yml",
            ".yaml",
            ".xml",
            ".toml",
            ".ini",
            ".conf",
            ".config",
            ".env",
        ]
        if ext in config_extensions:
            return True

        if ext in [".pem", ".crt", ".cer", ".key"]:
            return True

        config_files = ["dockerfile", "docker-compose.yml", "nginx.conf", "apache.conf"]
        if normalized_path.rsplit("/", 1)[-1].lower() in config_files:
            return True

        return False
