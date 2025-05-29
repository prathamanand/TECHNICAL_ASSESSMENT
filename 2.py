#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from textwrap import dedent

# --- RAG Imports ---
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import Ollama

# --- 1) RAG SETUP ---

loader1 = TextLoader("solidity_security_considerations.rst", encoding="utf-8")
loader2 = TextLoader("openzeppelin_security_best_practices.md", encoding="utf-8")
docs = loader1.load() + loader2.load()

splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
chunks = splitter.split_documents(docs)

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
if os.path.exists("security_ves"):
    vectorstore = Chroma(persist_directory="security_ves", embedding_function=embeddings)
else:
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="security_ves")

llm = Ollama(model="mistral:7b-instruct")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

def get_security_context(query: str) -> str:
    docs = qa_chain({"query": query})["source_documents"]
    return "\n\n".join(d.page_content for d in docs)

# --- 2) SOLIDITY SETUP ---

MODEL = "mistral:7b-instruct"

HEADER = dedent("""\
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;
""").strip()

ERC20_SKELETON = dedent("""\
// ERC-20 Allowlist Token
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract MyToken is ERC20, Ownable, AccessControl {
    uint256 public immutable maxSupply;
    mapping(address => uint256) public allocation;

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    constructor(
        string memory name_,
        string memory symbol_,
        uint256 maxSupply_
    ) ERC20(name_, symbol_) {
        maxSupply = maxSupply_;
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(MINTER_ROLE, msg.sender);
    }

    function setAllocation(address account, uint256 amount_) external onlyOwner {
        require(account != address(0), "Zero address");
        allocation[account] = amount_;
    }

    function revokeAllocation(address account) external onlyOwner {
        allocation[account] = 0;
    }

    function hasAllowance(address _account) public view returns (bool) {
        return allocation[_account] > 0;
    }

    function grantMinter(address account) external onlyOwner {
        grantRole(MINTER_ROLE, account);
    }

    function revokeMinter(address account) external onlyOwner {
        revokeRole(MINTER_ROLE, account);
    }

    function mint(uint256 amount_) external {
        require(hasRole(MINTER_ROLE, msg.sender), "Not a minter");
        require(hasAllowance(msg.sender), "Not allowlisted");
        require(amount_ <= allocation[msg.sender], "Exceeds allocation");
        require(totalSupply() + amount_ <= maxSupply, "Exceeds maxSupply");

        allocation[msg.sender] -= amount_;
        _mint(msg.sender, amount_);
    }
}
""").strip()

ERC721_SKELETON = dedent("""\
// ERC-721 ArtCollectible NFT
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract ArtCollectible is ERC721Enumerable, AccessControl, Ownable {
    using Strings for uint256;
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    string private _baseTokenURI;

    constructor(string memory name_, string memory symbol_)
        ERC721Enumerable(name_, symbol_)
    {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _setupRole(MINTER_ROLE, msg.sender);
    }

    function setBaseURI(string memory uri_) external onlyOwner {
        require(bytes(uri_).length > 0, "URI cannot be empty");
        _baseTokenURI = uri_;
    }

    function grantMinter(address account) external onlyOwner {
        grantRole(MINTER_ROLE, account);
    }

    function revokeMinter(address account) external onlyOwner {
        revokeRole(MINTER_ROLE, account);
    }

    function mint(address to, uint256 tokenId) external {
        require(!_exists(tokenId), "Token already exists");
        require(hasRole(MINTER_ROLE, msg.sender), "Caller is not a minter");
        _safeMint(to, tokenId);
    }

    function tokenURI(uint256 tokenId)
        public view override(ERC721Enumerable)
        returns (string memory)
    {
        require(_exists(tokenId), "URI query for nonexistent token");
        return string(abi.encodePacked(_baseTokenURI, tokenId.toString()));
    }

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721Enumerable, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
""").strip()

def select_skeleton(spec: str) -> str:
    s = spec.upper()
    if "ERC-20" in s or "ERC20" in s:
        return ERC20_SKELETON
    if "ERC-721" in s or "ERC721" in s:
        return ERC721_SKELETON
    return ERC20_SKELETON + "\n\n" + ERC721_SKELETON

def ensure_model_installed():
    out = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
    if MODEL not in out.stdout:
        subprocess.run(["ollama", "pull", MODEL], check=True)

def run_model(spec: str) -> str:
    s = spec.upper()
    if "ERC-20" in s or "ERC20" in s:
        sec = ("Security best practices: use onlyOwner or role-based access for mint; "
               "validate inputs; enforce per-address and global caps; avoid public mint.")
    else:
        sec = get_security_context(spec)

    skel = select_skeleton(spec)
    prompt = dedent(f"""
You are a Solidity security expert.

# Security Context:
{sec}

# Instruction:
{spec}

# Header (include exactly):
{HEADER}

# Solidity Skeleton (do not alter the first line):
{skel}

Respond with NO extra text or markdown (no triple backticks or language tags), only.

You must return both:
1. A complete Solidity snippet between ===BEGIN_CODE=== and ===END_CODE===.
2. A complete explanation between ===BEGIN_EXPLANATION=== and ===END_EXPLANATION===.

The explanation must describe:
- How role-based access is enforced using MINTER_ROLE
- How the allocation mechanism restricts minting
- The purpose of maxSupply and onlyOwner
- Why these checks help enforce safe minting and allowlist control

Example format:
===BEGIN_CODE===
<Your Solidity contract>
===END_CODE===
===BEGIN_EXPLANATION===
<Your explanation here>
===END_EXPLANATION===
""").strip()

    # (Optional) comment this out to avoid printing prompt
    # print(prompt, file=sys.stderr)

    proc = subprocess.run(["ollama", "run", MODEL, prompt], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", errors="ignore")
    if proc.returncode != 0:
        sys.exit("❌ Ollama error:\n" + proc.stderr)
    return proc.stdout


def parse_output(raw: str):
    try:
        if "===BEGIN_CODE===" in raw and "===END_CODE===" in raw:
            code = raw.split("===BEGIN_CODE===")[1].split("===END_CODE===")[0].strip()
            if code.startswith("```"):
                code = "\n".join(code.splitlines()[1:])
            if code.endswith("```"):
                code = "\n".join(code.splitlines()[:-1])
        else:
            raise ValueError("Missing code block markers")

        # Explanation is optional
        expl = ""
        if "===BEGIN_EXPLANATION===" in raw and "===END_EXPLANATION===" in raw:
            expl = raw.split("===BEGIN_EXPLANATION===")[1].split("===END_EXPLANATION===")[0].strip()
            if expl.startswith("```"):
                expl = "\n".join(expl.splitlines()[1:])
            if expl.endswith("```"):
                expl = "\n".join(expl.splitlines()[:-1])
        else:
            print("⚠️ Warning: Explanation section missing.")

        return code, expl

    except Exception as e:
        print(f"❌ Parsing failed due to: {e}")
        print("Raw output:\n", raw)
        sys.exit(1)



def validate_solidity(code: str):
    if not shutil.which("solc"):
        return
    import tempfile
    tf = tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w")
    tf.write(code)
    tf.close()
    res = subprocess.run(["solc", "--ast-json", tf.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        print("✔️ solc parse OK")
    else:
        print("⚠️ solc errors:\n" + res.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} '<natural language spec>'")
        sys.exit(1)
    ensure_model_installed()
    out = run_model(sys.argv[1])
    code, expl = parse_output(out)
    print("\n=== Generated Solidity ===\n" + code)
    print("\n=== Explanation ===\n" + expl)
    validate_solidity(code)
