import re
from typing import Dict, List

from .crypto_rules import CRYPTO_PATTERNS


def analyze_java_file(file_path: str, source_code: str) -> List[Dict]:
    """Analyze Java source using regex patterns."""
    vulnerabilities = []
    seen = set()
    patterns = CRYPTO_PATTERNS.get("java", {})

    for rule_name, rule in patterns.items():
        for pattern_str in rule["patterns"]:
            for match in re.finditer(pattern_str, source_code, re.MULTILINE):
                line_num = source_code[: match.start()].count("\n") + 1
                dedupe_key = (rule_name, line_num)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                vulnerabilities.append(
                    {
                        "type": rule_name,
                        "line": line_num,
                        "code": match.group(0),
                        "severity": rule["severity"],
                        "algorithm": rule["algorithm"],
                        "description": rule["description"],
                        "recommendation": rule["recommendation"],
                    }
                )

    return vulnerabilities
