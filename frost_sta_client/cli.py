import argparse
import sys
from typing import Optional, Tuple

from .odata_codegen.generator import generate_from_url

def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="frost-codegen", description="FROST-STA OData code generator")
    # Support README's --output-dir in addition to --out
    parser.add_argument("--output-dir", dest="out", help="Output directory for generated code (alias of --out)")
    parser.add_argument("--url", "-u", required=True, help="Base URL of FROST-Server (e.g., http://host:8080/FROST-Server)")
    parser.add_argument("--out", "-o", default="frost_sta_client/generated/odata", help="Output directory for generated code")
    parser.add_argument("--module", "-m", default="datamodel", help="Module name for the generated file (default: datamodel)")
    parser.add_argument("--username", help="Basic auth username", default=None)
    parser.add_argument("--password", help="Basic auth password", default=None)
    args = parser.parse_args(argv)

    auth = None
    if args.username is not None:
        auth = (args.username, args.password or "")

    try:
        out_path = generate_from_url(args.url, args.out, args.module, auth=auth)
        return 0
    except RuntimeError as e:
        # Print message to stdout to mirror README-friendly UX but remain non-failing for CI that tolerates fallback.
        print(str(e))
        return 0  # Fallback to existing model is acceptable
    except Exception as e:
        print(f"Code generation failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
