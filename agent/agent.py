#!/usr/bin/env python3
"""
Agent runner for the Daily Reflection Tree.
Loads the JSON, parses the logic, and runs a terminal UI.

No LLMs used at runtime. Strictly deterministic.
"""

import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --- Helpers ---

def clear_screen() -> None:
    """Clear terminal screen (cross-platform compatible)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def slow_print(text: str, delay: float = 0.02) -> None:
    """
    Print text with typing effect for conversational feel.
    
    Args:
        text: The string to print
        delay: Seconds between character prints (default 0.02)
    """
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def divider() -> None:
    """Print a visual divider line."""
    print("\n" + "─" * 60 + "\n")


# --- State Management ---

def init_state(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize blank state using axes defined in JSON metadata.
    
    Args:
        meta: The metadata dictionary from the tree JSON
        
    Returns:
        State dict with empty signals and answer tracking
    """
    signals: Dict[str, Dict[str, int]] = {}
    for axis_key, axis_info in meta["axes"].items():
        signals[axis_key] = {pole: 0 for pole in axis_info["poles"]}
        signals[axis_key]["last"] = None

    return {
        "answers": {},   # Tracks what they picked: node_id -> label
        "signals": signals,
    }

def record_signal(signal_str: Optional[str], state: Dict[str, Any]) -> None:
    """
    Parse signal string (e.g., 'locus:internal') and increment counter.
    
    Args:
        signal_str: Signal in format "axis:pole" or None
        state: Current state dictionary to update
        
    Raises:
        ValueError: If signal format is invalid
    """
    if not signal_str:
        return
        
    try:
        axis, pole = signal_str.split(":")
        if axis not in state["signals"]:
            raise ValueError(f"Unknown axis: {axis}")
        if pole not in state["signals"][axis]:
            raise ValueError(f"Unknown pole '{pole}' for axis '{axis}'")
            
        state["signals"][axis][pole] = state["signals"][axis].get(pole, 0) + 1
        state["signals"][axis]["last"] = pole
    except ValueError as e:
        logging.warning(f"Invalid signal format '{signal_str}': {e}")

def get_dominant_pole(state: Dict[str, Any], axis: str, poles: Tuple[str, str]) -> str:
    """
    Determine dominant pole by comparing signal counts.
    Ties default to first pole (the 'growth' side).
    
    Args:
        state: Current state dictionary
        axis: Axis name to check
        poles: Tuple of two pole names (a, b)
        
    Returns:
        The dominant pole name
    """
    a, b = poles
    count_a = state["signals"].get(axis, {}).get(a, 0)
    count_b = state["signals"].get(axis, {}).get(b, 0)
    return a if count_a >= count_b else b


# --- Engine Logic ---

def compare_values(a: int, operator: str, b: int) -> bool:
    """
    Safely compare two integers using a string operator.
    
    Args:
        a: Left operand
        operator: One of '>=', '>', '<=', '<', '=='
        b: Right operand
        
    Returns:
        Result of comparison
        
    Raises:
        ValueError: If operator is not recognized
    """
    if operator == ">=":
        return a >= b
    elif operator == ">":
        return a > b
    elif operator == "<=":
        return a <= b
    elif operator == "<":
        return a < b
    elif operator == "==":
        return a == b
    else:
        raise ValueError(f"Unknown operator: {operator}")

def evaluate_condition(condition: str, state: Dict[str, Any]) -> bool:
    """
    Evaluate routing condition from JSON.
    Supports three patterns:
    - q_node.answer in ['A', 'B']
    - q_node.answer == 'A'
    - state.axis.pole >= state.axis.pole
    
    Args:
        condition: Condition string to evaluate
        state: Current state dictionary
        
    Returns:
        Boolean result of condition
    """
    condition = condition.strip()

    # Pattern 1: q_node.answer in ['A', 'B']
    m = re.match(r"(\w+)\.answer\s+in\s+\[(.+?)\]", condition)
    if m:
        node_id, raw_values = m.groups()
        values = [v.strip().strip("'\"") for v in re.split(r",\s*(?=')", raw_values)]
        result = state["answers"].get(node_id) in values
        logging.debug(f"Condition '{condition}' -> {result}")
        return result

    # Pattern 2: q_node.answer == 'A'
    m = re.match(r"(\w+)\.answer\s*==\s*['\"](.+?)['\"]", condition)
    if m:
        node_id, value = m.groups()
        result = state["answers"].get(node_id) == value
        logging.debug(f"Condition '{condition}' -> {result}")
        return result

    # Pattern 3: state.axis.pole >= state.axis.pole
    m = re.match(r"state\.(\w+)\.(\w+)\s*(>=|>|<=|<|==)\s*state\.(\w+)\.(\w+)", condition)
    if m:
        axis_a, pole_a, op, axis_b, pole_b = m.groups()
        count_a = state["signals"].get(axis_a, {}).get(pole_a, 0)
        count_b = state["signals"].get(axis_b, {}).get(pole_b, 0)
        
        try:
            result = compare_values(count_a, op, count_b)
            logging.debug(f"Condition '{condition}' ({count_a} {op} {count_b}) -> {result}")
            return result
        except ValueError as e:
            logging.error(f"Invalid comparison operator: {e}")
            return False

    logging.warning(f"Condition failed to parse: {condition}")
    return False

def interpolate(text: Optional[str], state: Dict[str, Any], meta: Dict[str, Any]) -> str:
    """
    Replace placeholders in text with actual data from state.
    Supported placeholders:
    - {node_id.answer}: Previously recorded answer
    - {axis.dominant}: Dominant pole for an axis
    - {summary_insight}: Personalized summary based on axis dominance
    
    Args:
        text: Template text with placeholders
        state: Current state dictionary
        meta: Metadata dictionary
        
    Returns:
        Interpolated text with placeholders replaced
    """
    if not text:
        return ""
        
    # Inject previous answers
    for node_id, answer in state["answers"].items():
        text = text.replace(f"{{{node_id}.answer}}", answer)

    # Inject dominant poles
    for axis_key, axis_info in meta["axes"].items():
        dom = get_dominant_pole(state, axis_key, axis_info["poles"])
        text = text.replace(f"{{{axis_key}.dominant}}", dom)

    # Inject the big summary insight
    if "{summary_insight}" in text:
        key_parts = [get_dominant_pole(state, k, v["poles"]) for k, v in meta["axes"].items()]
        lookup_key = "_".join(key_parts)
        
        # Fallback in case combination is missing from JSON
        insight = meta.get("summary_insights", {}).get(
            lookup_key, 
            "You took the time to reflect today. That matters."
        )
        text = text.replace("{summary_insight}", insight)

    return text


# --- Node Runners ---

def run_start(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """Display start screen and wait for user to continue."""
    clear_screen()
    divider()
    slow_print(node["text"])
    print()
    input("  [Press Enter to start] ")
    return node.get("next")

def run_question(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """
    Display a question with options and record the user's choice.
    Re-prompts until valid selection is made.
    """
    clear_screen()
    divider()
    text = interpolate(node.get("text", ""), state, meta)
    print(text + "\n")
    
    options = node["options"]
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt['label']}")
    print()

    # Input loop until valid selection
    while True:
        raw = input(f"  Your choice (1-{len(options)}): ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                chosen = options[idx]
                state["answers"][node["id"]] = chosen["label"]
                record_signal(chosen.get("signal"), state)
                logging.debug(f"Question {node['id']}: Selected option {idx + 1}")
                return chosen.get("next")
        print(f"  -> Please pick a valid number.")

def run_decision(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """
    Invisible node that evaluates routing conditions.
    Returns the next node based on condition evaluation.
    """
    for route in node["routes"]:
        if evaluate_condition(route["condition"], state):
            logging.debug(f"Decision {node['id']}: Route selected via condition")
            return route["next"]
            
    # Fallback to prevent crashes if all conditions fail
    logging.warning(f"Decision {node['id']}: No matching condition, using fallback")
    return node["routes"][0]["next"]

def run_reflection(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """Display reflection text (personalized with interpolation) and wait for user."""
    clear_screen()
    divider()
    text = interpolate(node.get("text", ""), state, meta)
    slow_print(text)
    print()
    input("  [Press Enter to continue] ")
    return node.get("next")

def run_bridge(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """Display transition text briefly to create flow."""
    clear_screen()
    divider()
    text = interpolate(node.get("text", ""), state, meta)
    print(f"— {text}")
    time.sleep(1.2)  # Pause for readability
    return node.get("next")

def run_summary(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """Display final summary with personalized insights."""
    clear_screen()
    divider()
    text = interpolate(node.get("text", ""), state, meta)
    slow_print(text)
    print()
    input("  [Press Enter to finish] ")
    return node.get("next")

def run_end(node: Dict[str, Any], state: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
    """Display end screen."""
    clear_screen()
    divider()
    print(node.get("text", "Session complete."))
    divider()
    logging.info("Session completed successfully")
    return None

# Router mapping node types to their runner functions
NODE_RUNNERS: Dict[str, Any] = {
    "start": run_start,
    "question": run_question,
    "decision": run_decision,
    "reflection": run_reflection,
    "bridge": run_bridge,
    "summary": run_summary,
    "end": run_end,
}

def validate_tree_structure(tree: Dict[str, Any]) -> bool:
    """
    Validate that the tree JSON has required structure.
    
    Args:
        tree: The tree dictionary to validate
        
    Returns:
        True if valid, raises ValueError otherwise
    """
    if "nodes" not in tree or not tree["nodes"]:
        raise ValueError("Tree must have 'nodes' array")
    if "meta" not in tree:
        raise ValueError("Tree must have 'meta' section")
    
    node_ids = {n.get("id") for n in tree["nodes"]}
    for node in tree["nodes"]:
        node_type = node.get("type")
        if node_type not in NODE_RUNNERS:
            raise ValueError(f"Unknown node type: {node_type}")
        
        # Validate references (next/routes point to existing nodes)
        next_id = node.get("next")
        if next_id and next_id not in node_ids:
            logging.warning(f"Node {node.get('id')}: next '{next_id}' not found")
    
    return True

def walk_tree(tree: Dict[str, Any]) -> None:
    """
    Main execution loop. Steps through nodes until completion.
    
    Args:
        tree: The complete tree structure from JSON
    """
    nodes = {n["id"]: n for n in tree["nodes"]}
    meta = tree["meta"]
    state = init_state(meta)

    current_id = tree["nodes"][0]["id"]  # Start at first node
    logging.info("Tree traversal started")

    try:
        while current_id:
            node = nodes.get(current_id)
            if not node:
                logging.error(f"Node '{current_id}' not found in tree")
                break

            runner = NODE_RUNNERS.get(node["type"])
            if not runner:
                logging.error(f"No runner for node type: '{node['type']}'")
                break

            logging.debug(f"Running node: {current_id} (type: {node['type']})")
            current_id = runner(node, state, meta)
            
    except KeyboardInterrupt:
        print("\n\n  [Session aborted by user. See you tomorrow.]")
        logging.info("User cancelled session")
        sys.exit(0)


# --- Main ---

def main() -> None:
    """
    Entry point. Load tree from JSON file and run traversal.
    Usage: python agent.py [path/to/reflection-tree.json]
    """
    # Get file path from args or use default
    path = sys.argv[1] if len(sys.argv) > 1 else "reflection-tree.json"
    
    if not os.path.exists(path):
        logging.error(f"Tree file not found: {path}")
        print(f"\nOops, couldn't find the tree file: {path}")
        print("Usage: python agent.py [path/to/reflection-tree.json]\n")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = json.load(f)
        
        # Validate structure before running
        validate_tree_structure(tree)
        logging.info(f"Loaded tree from {path}")
        
        walk_tree(tree)
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parse error: {e}")
        print(f"\nFailed to parse JSON. Check your syntax:\n{e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        print(f"\nTree validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()