# Natural Language to Solidity & Smart Contract Auditor

This project provides tools to generate secure, ERC-compliant smart contracts from natural language descriptions and to audit or explain existing Solidity contracts for vulnerabilities.

## Features
- **Natural Language to Solidity (`nl2solidity.py`)**: Converts natural language descriptions into secure, ERC-compliant smart contracts using a fixed contract skeleton.
- **Contract Auditor/Explainer (`explain_contract.py`)**: Analyzes deployed or local Solidity contracts, providing JSON-structured summaries and security insights.

## System Design
### Components
1. **Natural Language to Code Generator (`nl2solidity.py`)**
   - Uses structured prompts with a predefined contract skeleton.
   - Enforces strict formatting for safety and compatibility.
   - Parses LLM output to provide both code and security explanations.
2. **Contract Explainer/Auditor (`explain_contract.py`)**
   - Fetches verified contracts via the Etherscan API or reads local `.sol` files.
   - Uses an LLM to generate JSON-structured summaries and identify vulnerabilities.

### Design Trade-offs
| Aspect                     | Decision                                                                 |
|----------------------------|--------------------------------------------------------------------------|
| 🔐 Skeleton Enforcement    | Fixes core logic structure to prevent insecure code generation.           |
| 🤖 Lightweight LLM         | Uses `mistral:7b-instruct` for compatibility with local hardware.         |
| 📊 No Fine-tuning          | Relies on prompt engineering due to resource constraints.                 |
| 🔎 Code Audit Structure    | Returns raw JSON for easy parsing and minimal noise.                      |
| ⏱️ Runtime Subprocess       | Uses subprocess calls to `ollama`, reducing integration complexity but increasing latency. |

## Security Considerations
### 1. Natural Language to Code
- **Skeleton Avoids**:
  - Public `mint()` access.
  - Missing ownership checks.
  - Overflow issues via `maxSupply` checks.
- **Skeleton Enforces**:
  - Input validation (`require` conditions).
  - Role-based access (`onlyOwner`).
  - Per-address mint limits (`allocation` mapping).

### 2. Code Explanation & Audit
- Outputs restricted to JSON to prevent injection of untrusted text.
- Audits highlight issues like reentrancy, access control gaps, and unchecked inputs.

### 3. Execution Risks
- Subprocess calls for model inference introduce shell execution risks; user input must be sanitized in web settings.
- Etherscan API key is loaded via `.env`, but rate-limiting and key security must be managed in deployment.

## Scaling Roadmap
| Phase         | Plan                                                                 |
|---------------|----------------------------------------------------------------------|
| 🚀 MVP        | Use small open-source models (`mistral:7b`) for offline development.  |
| 🔁 Iteration   | Support additional contract types (ERC721, custom DeFi protocols).    |
| 🔐 Audit       | Enhance explanation engine for gas efficiency and modifier analysis.  |
| 🌍 Web UI      | Deploy a web interface with file upload, Etherscan fetch, and editing.|
| 🤖 LLM Upgrade | Transition to larger LLMs (e.g., LLaMA3 70B) via cloud inferencing.   |
| 📦 Dockerized CLI | Bundle as a Docker service with REST endpoints for CI/CD integration.|

## LLM Risk Mitigation
### Why Risks Exist
- LLMs may hallucinate or generate incorrect code logic.
- Smaller models (e.g., `mistral:7b`) lack deep knowledge of:
  - Solidity-specific DSL syntax.
  - Real-world edge cases (e.g., gas griefing, proxy patterns).
  - Advanced DeFi or upgradeability patterns.

### Mitigation Steps
- **Canonical Skeleton**: Acts as a trusted boundary for generated code.
- **Prompt Structuring**: Forces LLMs to provide clear, delimited rationale.
- **Validation with `solc`**: Ensures generated Solidity compiles correctly.

### Known Limitation
- Small parameter LLMs struggle with complex patterns (e.g., factory patterns, access proxy contracts).

## Why Not LLaMA3-70B?
LLaMA3-70B offers superior Solidity understanding but requires ~350–400GB VRAM, making it impractical for consumer hardware. This project prioritizes:
- Speed and accessibility.
- Security via skeleton enforcement.
- Local device compatibility.

To upgrade to a larger model, update the model endpoint in `nl2solidity.py` and `explain_contract.py` with a cloud-inference backend (e.g., Groq, Together AI).

## Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the Etherscan API key in a `.env` file:
   ```plaintext
   ETHERSCAN_API_KEY=your_api_key_here
   ```
4. Install `ollama` and pull the `mistral:7b-instruct` model:
   ```bash
   ollama pull mistral:7b-instruct
   ```
5. Run the tools:
   - Generate a contract: `python nl2solidity.py`
   - Audit a contract: `python explain_contract.py`

## Usage
- **Generate a Contract**: Provide a natural language description to `nl2solidity.py` to create an ERC-compliant contract.
- **Audit a Contract**: Use `explain_contract.py` with a contract address (via Etherscan) or a local `.sol` file to get a JSON summary and vulnerability report.

