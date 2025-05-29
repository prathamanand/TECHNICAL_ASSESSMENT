import subprocess
from nl2solidity import parse_output, PROMPT, SKELETON, MODEL, ensure_model_installed

def get_solidity_output(nl_instruction):
    ensure_model_installed()
    prompt = PROMPT.format(nl_spec=nl_instruction, skeletal=SKELETON)
    proc = subprocess.run(
        ["ollama", "run", MODEL, prompt],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        return "Model error", proc.stderr
    return parse_output(proc.stdout)
