"""
algorithms/__init__.py

Shared helpers used by all the algorithm files.
The algorithms themselves are written by hand (no built-in sorted()/sort()).
"""

# Priority -> importance value (used later by the knapsack algorithms).
PRIORITY_VALUE = {"High": 5, "Medium": 3, "Low": 1}

# Priority -> position when sorting (smaller number = comes first).
PRIORITY_RANK = {"High": 1, "Medium": 2, "Low": 3}

# Topics with no deadline are treated as "very far in the future".
NO_DEADLINE = "9999-12-31"


def make_key(criterion):
    """
    Return a small function that tells a sorting algorithm WHAT to compare.

    criterion can be: "deadline", "priority", "duration" or "name".
    Example: make_key("duration")(topic) -> topic["estimated_duration"]
    """
    if criterion == "deadline":
        return lambda topic: topic.get("deadline") or NO_DEADLINE
    if criterion == "priority":
        return lambda topic: PRIORITY_RANK[topic["priority"]]
    if criterion == "duration":
        return lambda topic: topic["estimated_duration"]
    if criterion == "name":
        return lambda topic: topic["topic_name"].lower()
    raise ValueError("Unknown sort criterion: " + str(criterion))