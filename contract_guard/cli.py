"""
CLI entry point for ContractGuard.
"""

import argparse
import sys
from pathlib import Path

from .comparator import ContractComparator
from .git_utils import get_file_content_from_git
from .parser import OpenAPISpec, load_spec_from_file, load_spec_from_string
from .reporter import MarkdownReporter, SarifReporter, TerminalReporter


def _ensure_utf8_io() -> None:
    """Ensure stdout and stderr use utf-8 encoding on all platforms."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def main() -> None:
    _ensure_utf8_io()
    parser = argparse.ArgumentParser(

        prog="contractguard",
        description="ContractGuard: Automated API Breaking Change & Schema Drift Detector",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    diff_parser = subparsers.add_parser("diff", help="Diff two OpenAPI specification files")
    diff_parser.add_argument("--base", required=True, help="Path to base OpenAPI spec (v1/baseline)")
    diff_parser.add_argument("--head", required=True, help="Path to head OpenAPI spec (v2/current PR)")
    diff_parser.add_argument("--format", choices=["terminal", "markdown", "sarif"], default="terminal", help="Output format")
    diff_parser.add_argument("--output", help="Write report to output file instead of stdout")
    diff_parser.add_argument("--fail-on-breaking", action="store_true", default=True, help="Exit with code 1 if breaking changes exist")

    git_parser = subparsers.add_parser("git-diff", help="Diff current spec against a git revision (e.g., origin/main)")
    git_parser.add_argument("--spec", required=True, help="Path to OpenAPI spec in repository (e.g., openapi.json)")
    git_parser.add_argument("--base-ref", default="origin/main", help="Git revision for base spec (default: origin/main)")
    git_parser.add_argument("--format", choices=["terminal", "markdown", "sarif"], default="terminal", help="Output format")
    git_parser.add_argument("--output", help="Write report to output file")
    git_parser.add_argument("--fail-on-breaking", action="store_true", default=True, help="Exit with code 1 if breaking changes exist")

    args = parser.parse_args()

    if args.command == "diff":
        base_dict = load_spec_from_file(args.base)
        head_dict = load_spec_from_file(args.head)
    elif args.command == "git-diff":
        head_dict = load_spec_from_file(args.spec)
        base_content = get_file_content_from_git(args.base_ref, args.spec)
        if base_content is None:
            sys.stderr.write(f"Warning: Could not read {args.spec} at {args.base_ref}. Treating as initial spec.\n")
            base_dict = {"openapi": "3.0.0", "info": {"title": "Base", "version": "0.0.0"}, "paths": {}}
        else:
            base_dict = load_spec_from_string(base_content)

    base_spec = OpenAPISpec(base_dict)
    head_spec = OpenAPISpec(head_dict)

    comparator = ContractComparator(base_spec, head_spec)
    result = comparator.compare()

    if args.format == "terminal":
        output_str = TerminalReporter().render(result)
    elif args.format == "markdown":
        output_str = MarkdownReporter().render(result)
    elif args.format == "sarif":
        output_str = SarifReporter().render(result)
    else:
        output_str = TerminalReporter().render(result)

    if getattr(args, "output", None):
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_str)

    if args.fail_on_breaking and result.is_breaking:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
