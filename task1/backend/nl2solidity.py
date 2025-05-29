#!/usr/bin/env python3
import shutil
import subprocess
import sys
from textwrap import dedent

MODEL = "mistral:7b-instruct"

# A canonical skeleton to guide generation
SKELETON = dedent("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    uint256 public immutable maxSupply;
    mapping(address => uint256) public allocation;

    constructor(
        string memory name,
        string memory symbol,
        uint256 maxSupply_
    ) ERC20(name, symbol) {
        maxSupply = maxSupply_;
    }

    /// @notice Owner sets per-address mint limit
    function setAllocation(address user, uint256 amount) external onlyOwner {
        allocation[user] = amount;
    }

    /// @notice Owner can revoke an address's allocation
    function revokeAllocation(address user) external onlyOwner {
        allocation[user] = 0;
    }

    /// @notice Mint up to your allocation, respecting maxSupply
    function mint(uint256 amount) external {
        uint256 allowed = allocation[msg.sender];
        require(allowed > 0, "Not allowlisted");
        require(amount <= allowed, "Exceeds allocation");
        require(totalSupply() + amount <= maxSupply, "Exceeds maxSupply");

        allocation[msg.sender] = allowed - amount;
        _mint(msg.sender, amount);
    }
}
""")

PROMPT = dedent("""
You are a Solidity security expert.

# Instruction:
{nl_spec}

# Skeleton (include exactly as given, with no modifications to these lines):
{skeletal}

Respond with NO extra text, only:

===BEGIN_CODE===
<Your complete Solidity snippet>
===END_CODE===
===BEGIN_EXPLANATION===
<Concise rationale accurately describing setAllocation, revokeAllocation, and mint, including security trade-offs and explicit security-aware logic (e.g., avoiding public mint, role-based access, input validation)>
===END_EXPLANATION===

**IMPORTANT**: The code snippet must start with the Skeleton's SPDX and pragma lines exactly as shown. Do not add, remove, or reorder those lines.
""").strip()


def ensure_model_installed():
    proc = subprocess.run(
        ["ollama", "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )
    if MODEL not in proc.stdout:
        print(f"Pulling model {MODEL}…")
        subprocess.run(
            ["ollama", "pull", MODEL],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="ignore",
            check=True
        )


def run_model(spec):
    prompt = PROMPT.format(nl_spec=spec, skeletal=SKELETON)
    proc = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="ignore"
    )
    if proc.returncode != 0:
        sys.exit("❌ Ollama error:\n" + proc.stderr)
    return proc.stdout


def parse_output(raw):
    try:
        after = raw.split("===BEGIN_CODE===", 1)[1]
        code_block = after.split("===END_CODE===", 1)[0].strip()
        lines = code_block.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines).strip()

        remainder = after.split("===END_CODE===", 1)[1]
        if "===BEGIN_EXPLANATION===" in remainder:
            expl = remainder.split("===BEGIN_EXPLANATION===",1)[1].split("===END_EXPLANATION===",1)[0].strip()
        else:
            expl = remainder.strip()
        expl_lines = expl.splitlines()
        if expl_lines and expl_lines[0].startswith("```"):
            expl_lines = expl_lines[1:]
        if expl_lines and expl_lines[-1].startswith("```"):
            expl_lines = expl_lines[:-1]
        explanation = "\n".join(expl_lines).strip()

        return code, explanation
    except Exception:
        sys.exit(f"❌ Parsing failed. Raw output:\n{raw}")


def validate_solidity(code):
    if not shutil.which("solc"):
        return
    import tempfile
    tf = tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w")
    tf.write(code)
    tf.flush()
    tf.close()
    res = subprocess.run(
        ["solc", "--ast-json", tf.name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if res.returncode == 0:
        print("✔️ solc parse OK")
    else:
        print("⚠️ solc errors:\n" + res.stderr)


if __name__ == "__main__":
    print("pratham code")
    if len(sys.argv) != 2:
        print("Usage: nl2solidity.py '<natural language spec>'")
        sys.exit(1)
    ensure_model_installed()
    output = run_model(sys.argv[1])
    code, explanation = parse_output(output)
    print("\n=== Generated Solidity ===\n" + code)
    print("\n=== Explanation ===\n" + explanation)
    validate_solidity(code)