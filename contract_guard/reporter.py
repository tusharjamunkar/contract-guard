"""
Reporters for Terminal CLI output, GitHub PR Markdown comments, and SARIF export.
"""

import json
from .models import DiffResult, Severity


class TerminalReporter:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def render(self, result: DiffResult) -> str:
        lines = []
        lines.append(f"{self.BOLD}{self.CYAN}=== ContractGuard API Diff Summary ==={self.RESET}")
        lines.append(f"Base: {result.base_title or 'Base'} ({result.base_version or 'v1'})")
        lines.append(f"Head: {result.head_title or 'Head'} ({result.head_version or 'v2'})")
        lines.append("")

        if result.is_breaking:
            lines.append(f"{self.RED}{self.BOLD}❌ BREAKING CHANGES DETECTED ({len(result.breaking_changes)}){self.RESET}")
            for c in result.breaking_changes:
                lines.append(f"  {self.RED}[BREAKING]{self.RESET} {c.method} {c.path} -> {c.description} ({c.location})")
            lines.append("")
        else:
            lines.append(f"{self.GREEN}{self.BOLD}✅ NO BREAKING CHANGES{self.RESET}")

        if result.warnings:
            lines.append(f"{self.YELLOW}{self.BOLD}⚠️ WARNINGS ({len(result.warnings)}){self.RESET}")
            for c in result.warnings:
                lines.append(f"  {self.YELLOW}[WARNING]{self.RESET} {c.method} {c.path} -> {c.description}")
            lines.append("")

        if result.info_changes:
            lines.append(f"{self.CYAN}ℹ️ ADDITIVE & SAFE CHANGES ({len(result.info_changes)}){self.RESET}")
            for c in result.info_changes:
                lines.append(f"  [INFO] {c.method} {c.path} -> {c.description}")
            lines.append("")

        lines.append(
            f"Summary: {len(result.breaking_changes)} breaking | {len(result.warnings)} warnings | {len(result.info_changes)} additive"
        )
        return "\n".join(lines)


class MarkdownReporter:
    def render(self, result: DiffResult) -> str:
        lines = []
        lines.append("## 🛡️ ContractGuard API Contract Review")
        lines.append("")

        if result.is_breaking:
            lines.append("> [!CAUTION]")
            lines.append(f"> **{len(result.breaking_changes)} BREAKING CHANGES DETECTED**")
            lines.append("> Merging this PR without a major SemVer bump or backward-compatibility migration may break live clients and frontend integrations.")
            lines.append("")
        elif result.warnings:
            lines.append("> [!WARNING]")
            lines.append(f"> **API Review: {len(result.warnings)} Deprecation/Contract Warnings Detected**")
            lines.append("")
        else:
            lines.append("> [!TIP]")
            lines.append("> **✅ All API contract changes are backward-compatible!**")
            lines.append("")

        lines.append("| Metric | Count |")
        lines.append("| :--- | :---: |")
        lines.append(f"| 🔴 Breaking Changes | **{len(result.breaking_changes)}** |")
        lines.append(f"| 🟡 Deprecations / Warnings | **{len(result.warnings)}** |")
        lines.append(f"| 🟢 Non-Breaking Additions | **{len(result.info_changes)}** |")
        lines.append("")

        if result.breaking_changes:
            lines.append("### 🔴 Breaking Changes Breakdown")
            lines.append("| Method | Endpoint | Location | Description |")
            lines.append("| :---: | :--- | :--- | :--- |")
            for c in result.breaking_changes:
                lines.append(f"| `{c.method}` | `{c.path}` | `{c.location}` | {c.description} |")
            lines.append("")

        if result.warnings:
            lines.append("### 🟡 Warnings & Deprecations")
            for c in result.warnings:
                lines.append(f"- `{c.method} {c.path}`: {c.description}")
            lines.append("")

        if result.info_changes:
            lines.append(f"<details><summary><b>🟢 View Additive Changes ({len(result.info_changes)})</b></summary>")
            lines.append("")
            for c in result.info_changes:
                lines.append(f"- `{c.method} {c.path}`: {c.description}")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("*Generated automatically by [ContractGuard](https://github.com/tusharjamunkar/contract-guard) — Zero-API OpenAPI Drift Guardian.*")
        return "\n".join(lines)


class SarifReporter:
    def render(self, result: DiffResult) -> str:
        rules = []
        results = []
        rule_indices = {}

        for c in result.changes:
            cat_name = c.category.value
            if cat_name not in rule_indices:
                rule_indices[cat_name] = len(rules)
                rules.append({
                    "id": cat_name,
                    "name": cat_name,
                    "shortDescription": {"text": f"ContractGuard API Rule: {cat_name}"},
                    "defaultConfiguration": {
                        "level": "error" if c.severity == Severity.BREAKING else ("warning" if c.severity == Severity.WARNING else "note")
                    }
                })

            rule_idx = rule_indices[cat_name]
            results.append({
                "ruleId": cat_name,
                "ruleIndex": rule_idx,
                "level": "error" if c.severity == Severity.BREAKING else ("warning" if c.severity == Severity.WARNING else "note"),
                "message": {"text": f"{c.method} {c.path}: {c.description} at {c.location}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "openapi.json"},
                        "region": {"startLine": 1}
                    }
                }]
            })

        sarif_doc = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "ContractGuard",
                        "informationUri": "https://github.com/tusharjamunkar/contract-guard",
                        "version": "0.1.0",
                        "rules": rules
                    }
                },
                "results": results
            }]
        }
        return json.dumps(sarif_doc, indent=2)
