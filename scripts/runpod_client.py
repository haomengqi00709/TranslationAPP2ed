"""
RunPod Client Example

Simple Python client to test the RunPod serverless endpoint.
"""

import runpod
import base64
import argparse
import json
from pathlib import Path


def translate_pptx(
    input_file: str,
    output_file: str,
    endpoint_id: str,
    api_key: str,
    translator_type: str = "local",
    use_glossary: bool = True,
    context: str = None
):
    """
    Translate a PowerPoint file using RunPod serverless.

    Args:
        input_file: Path to input .pptx file
        output_file: Path to save translated .pptx file
        endpoint_id: RunPod endpoint ID
        api_key: RunPod API key
        translator_type: "local", "openai", or "anthropic"
        use_glossary: Whether to use the glossary
        context: Optional custom terminology instructions
    """

    print(f"📄 Reading file: {input_file}")

    # Read and encode input file
    with open(input_file, "rb") as f:
        file_bytes = f.read()
        file_base64 = base64.b64encode(file_bytes).decode('utf-8')

    print(f"📦 File size: {len(file_bytes):,} bytes")
    print(f"🚀 Sending to RunPod endpoint: {endpoint_id}")

    # Configure RunPod
    runpod.api_key = api_key
    endpoint = runpod.Endpoint(endpoint_id)

    # Prepare input
    job_input = {
        "file_base64": file_base64,
        "file_name": Path(input_file).name,
        "translator_type": translator_type,
        "use_glossary": use_glossary
    }

    if context:
        job_input["context"] = context

    # Run translation with async polling (to handle long-running jobs)
    print("⏳ Translating... (this may take a few minutes)")

    try:
        # Start the job
        run_request = endpoint.run(job_input)

        # Poll for results with longer timeout
        import time
        max_wait_time = 600  # 10 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = run_request.status()

            if status == "COMPLETED":
                result = run_request.output()
                break
            elif status == "FAILED":
                print(f"❌ Job failed on RunPod")
                return False
            else:
                # Still running, wait and check again
                elapsed = int(time.time() - start_time)
                print(f"⏳ Still translating... ({elapsed}s elapsed)", end='\r')
                time.sleep(5)  # Check every 5 seconds
        else:
            print(f"\n❌ Translation timed out after {max_wait_time}s")
            return False

        # Check for errors
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False

        # Decode and save result
        if "file_base64" in result:
            output_bytes = base64.b64decode(result["file_base64"])

            with open(output_file, "wb") as f:
                f.write(output_bytes)

            print(f"✅ Translation complete!")
            print(f"📁 Output saved to: {output_file}")
            print(f"📊 Output size: {len(output_bytes):,} bytes")

            # Print stats if available
            if "stats" in result:
                print(f"\n📈 Statistics:")
                stats = result["stats"]
                print(f"   Total time: {stats.get('total_time_seconds', 'N/A')}s")

                if "steps" in stats:
                    print(f"   Steps completed: {len(stats['steps'])}")

            return True

        else:
            print(f"❌ Unexpected response: {result}")
            return False

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def main():
    """Command-line interface."""

    parser = argparse.ArgumentParser(
        description="Translate PowerPoint files using RunPod serverless"
    )

    parser.add_argument(
        "input",
        help="Input PowerPoint file (.pptx)"
    )

    parser.add_argument(
        "output",
        help="Output PowerPoint file (.pptx)"
    )

    parser.add_argument(
        "--endpoint-id",
        required=True,
        help="RunPod endpoint ID"
    )

    parser.add_argument(
        "--api-key",
        required=True,
        help="RunPod API key"
    )

    parser.add_argument(
        "--translator",
        choices=["local", "openai", "anthropic"],
        default="local",
        help="Translation engine (default: local)"
    )

    parser.add_argument(
        "--no-glossary",
        action="store_true",
        help="Disable glossary usage"
    )

    parser.add_argument(
        "--context",
        help="Custom terminology instructions"
    )

    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        print(f"❌ Error: Input file not found: {args.input}")
        return

    if not args.input.endswith('.pptx'):
        print(f"❌ Error: Input file must be a .pptx file")
        return

    # Run translation
    success = translate_pptx(
        input_file=args.input,
        output_file=args.output,
        endpoint_id=args.endpoint_id,
        api_key=args.api_key,
        translator_type=args.translator,
        use_glossary=not args.no_glossary,
        context=args.context
    )

    if success:
        print("\n✅ Done!")
    else:
        print("\n❌ Translation failed")
        exit(1)


if __name__ == "__main__":
    main()
