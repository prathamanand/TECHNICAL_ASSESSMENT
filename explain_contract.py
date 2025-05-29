import os
import sys
import requests
import subprocess
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_URL = "https://api-sepolia.etherscan.io/api"
OLLAMA_MODEL = "mistral:7b-instruct"  # or codellama:instruct

VERBOSE = False

def debug(msg):
    if VERBOSE:
        print(msg)

def fetch_contract_source(address):
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": ETHERSCAN_API_KEY
    }
    response = requests.get(ETHERSCAN_URL, params=params)
    
    try:
        json_data = response.json()
        result = json_data.get("result", [])
    except Exception as e:
        debug(f"Failed to decode JSON: {e}")
        return None, None

    if not isinstance(result, list) or not result or not isinstance(result[0], dict):
        debug(f"Unexpected result format: {result}")
        return None, None

    if "SourceCode" not in result[0] or not result[0]["SourceCode"]:
        debug("No source code found in the result.")
        return None, None

    source_code_raw = result[0]["SourceCode"]
    abi = result[0]["ABI"]

    if source_code_raw.startswith('"') and source_code_raw.endswith('"'):
        source_code_raw = source_code_raw[1:-1]

    source_code_raw = source_code_raw.strip()

    if source_code_raw.startswith('{') and '"sources"' in source_code_raw:
        try:
            source_json = json.loads(source_code_raw)
            combined_code = ""
            for file_info in source_json.get("sources", {}).values():
                combined_code += file_info.get("content", "") + "\n\n"
            return combined_code.strip(), abi
        except Exception as e:
            debug(f"Failed to parse SourceCode as structured JSON: {e}")

    return source_code_raw, abi


def prompt_llm(solidity_code):
    if isinstance(solidity_code, str) and solidity_code.startswith("\""):
        solidity_code = solidity_code.strip("\"")

    prompt = f"""
You are a Solidity smart contract auditor.

ONLY return a valid JSON string with the following fields:
{{
  "summary": "What the contract does and its key logic.",
  "security": "Security risks or issues like reentrancy, unchecked inputs, or lack of access control."
}}

DO NOT include markdown, explanations, or any text before/after the JSON.

===BEGIN_SOLIDITY===
{solidity_code}
===END_SOLIDITY===
""".strip()

    result = subprocess.run(
        ["ollama", "run", OLLAMA_MODEL],
        input=prompt,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    raw_output = result.stdout.strip()

    with open("last_raw_llm_output.json", "w", encoding="utf-8") as f:
        f.write(raw_output)

    start = raw_output.find('{')
    end = raw_output.rfind('}') + 1
    return raw_output[start:end] if start != -1 and end != -1 else raw_output

def parse_llm_output(raw):
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        return parsed.get("summary", "Summary not found"), parsed.get("security", "Security notes not found")
    except Exception as e:
        debug(f"JSON Parsing Error: {e}")
        fallback_lines = raw.strip().splitlines()
        fallback_summary = "\n".join(fallback_lines[:10]).strip() or "Summary section missing or malformed."
        return fallback_summary, "Security overview not found or not formatted correctly."

def explain_contract(input_text):
    if input_text.startswith("0x") and len(input_text) == 42:
        print(f"Fetching contract from address: {input_text}")
        source, _ = fetch_contract_source(input_text)
        if not source:
            print("Failed to fetch verified source.")
            return
        print("Source code fetched.")
    elif os.path.isfile(input_text) and input_text.endswith(".sol"):
        with open(input_text, "r", encoding="utf-8") as f:
            source = f.read()
        print(f"Loaded Solidity file: {input_text}")
    else:
        source = input_text
        print("Treating input as raw Solidity code.")

    output = prompt_llm(source)
    summary, security = parse_llm_output(output)

    print("\n=== Summary ===")
    print(summary)
    print("\n=== Security Overview ===")
    print(security)

def parse_args():
    parser = argparse.ArgumentParser(description="Analyze a Solidity contract by address, file, or raw code.")
    parser.add_argument("input", help="Contract address (0x...), path to a .sol file, or raw Solidity code.")
    parser.add_argument("--verbose", action="store_true", help="Show debug logs.")
    return parser.parse_args()

def main():
    global VERBOSE
    args = parse_args()
    VERBOSE = args.verbose
    explain_contract(args.input)

if __name__ == "__main__":
    main()
