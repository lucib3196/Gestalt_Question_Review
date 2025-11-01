from typing import Any, Dict, Optional


def generate() -> Dict[str, Any]:
    a = 1
    b = 2
    sum_val = a + b
    print("This is the value of a", a)
    print("This is the value of b", b)
    print("This is a structure", {"params": {"a": a, "b": b}})

    return {
        "params": {"a": a, "b": b},
        "correct_answers": {"sum": sum_val},
        "intermediate": {"step": f"{a} + {b} = {sum_val}"},
        "test_results": {"pass": 1, "message": "Addition successful"},
        "nDigits": 3,
        "sigfigs": 3,
    }
