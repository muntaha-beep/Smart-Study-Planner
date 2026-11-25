"""
fractional_knapsack.py - Fractional Knapsack (greedy algorithm).

*** This is a fractional-RESOURCE-ALLOCATION demonstration. ***
Here each item has a VALUE (importance of a study task) and a WEIGHT (the study
time it needs). We have a limited amount of study time (the capacity).
This algorithm is allowed to take only a PART of the last item.

It does NOT mean a student can "half-complete" a topic. A fraction such as 0.83
only says "83% of that topic's time would fit in the remaining time". The real
planner uses 0/1 Knapsack, where a topic is taken completely or not at all.

Greedy idea:
  1. Calculate ratio = value / weight for every item (value per minute).
  2. Sort items by ratio, best ratio first.
  3. Take whole items while they fit. For the first item that does not fit,
     take only the fraction that fits, then stop.

Time  : O(n log n) for sorting + O(n) for the selection = O(n log n)
Space : O(n)
"""

from algorithms import PRIORITY_VALUE
from algorithms.merge_sort import merge_sort


def topics_to_items(topics):
    """Turn topic dictionaries into knapsack items (value from priority)."""
    items = []
    for topic in topics:
        items.append({
            "name": topic["topic_name"],
            "value": PRIORITY_VALUE[topic["priority"]],
            "weight": topic["estimated_duration"],
        })
    return items


def fractional_knapsack(items, capacity, log=None):
    """
    items    : list of dicts with "name", "value", "weight" (weight > 0)
    capacity : total available study time (minutes), 0 or more
    log      : optional list; explanation lines are added to it

    Returns a dictionary:
      "selected"    : items taken (fully or partly), best ratio first. Each has
                      "ratio", "fraction" (0..1), "taken_weight", "taken_value"
      "rejected"    : items not taken at all (same fields, fraction = 0)
      "total_value" : sum of taken values
      "total_weight": study time used (never more than capacity)
      "remaining"   : unused capacity
    """
    if capacity < 0:
        raise ValueError("Capacity cannot be negative")
    for item in items:
        if item["weight"] <= 0:
            raise ValueError(item["name"] + ": weight (time) must be greater than zero")
        if item["value"] < 0:
            raise ValueError(item["name"] + ": value cannot be negative")

    # Step 1: ratio = value per minute.
    ranked = []
    for item in items:
        copy = dict(item)  # never change the caller's data
        copy["ratio"] = item["value"] / item["weight"]
        ranked.append(copy)

    # Step 2: sort by ratio, biggest first (negative ratio = descending order).
    ranked = merge_sort(ranked, key=lambda item: -item["ratio"])
    if log is not None:
        log.append("Sorted by value/time ratio (best first):")
        for item in ranked:
            log.append("   " + item["name"] + ": " + str(item["value"]) + "/"
                       + str(item["weight"]) + " = " + str(round(item["ratio"], 4)))

    # Step 3: take items greedily.
    selected = []
    rejected = []
    remaining = capacity
    total_value = 0.0

    for item in ranked:
        if remaining <= 0:
            item["fraction"] = 0.0
            item["taken_weight"] = 0
            item["taken_value"] = 0.0
            rejected.append(item)
            if log is not None:
                log.append("SKIP " + item["name"] + " - no capacity left")
        elif item["weight"] <= remaining:
            item["fraction"] = 1.0
            item["taken_weight"] = item["weight"]
            item["taken_value"] = float(item["value"])
            selected.append(item)
            remaining -= item["weight"]
            total_value += item["taken_value"]
            if log is not None:
                log.append("TAKE ALL " + item["name"] + " (" + str(item["weight"])
                           + " min) - remaining capacity: " + str(remaining))
        else:
            fraction = remaining / item["weight"]
            item["fraction"] = fraction
            item["taken_weight"] = remaining
            item["taken_value"] = item["value"] * fraction
            selected.append(item)
            total_value += item["taken_value"]
            if log is not None:
                log.append("TAKE PART " + item["name"] + " - only " + str(remaining)
                           + " of " + str(item["weight"]) + " min fit, fraction = "
                           + str(round(fraction, 4)))
            remaining = 0

    used = capacity - remaining
    return {
        "selected": selected,
        "rejected": rejected,
        "total_value": total_value,
        "total_weight": used,
        "remaining": remaining,
    }


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.fractional_knapsack
# ----------------------------------------------------------------------
if __name__ == "__main__":
    study_items = [
        {"name": "Arrays",   "value": 5, "weight": 30},
        {"name": "Trees",    "value": 5, "weight": 60},
        {"name": "SQL",      "value": 3, "weight": 45},
        {"name": "Graphs",   "value": 5, "weight": 20},
        {"name": "Networks", "value": 1, "weight": 40},
    ]
    available = 100
    print("Capacity (available study minutes):", available)
    print("Input items:")
    for it in study_items:
        print("  ", it["name"], "value =", it["value"], "time =", it["weight"])

    steps = []
    result = fractional_knapsack(study_items, available, log=steps)

    print("\nStep-by-step:")
    for line in steps:
        print(" ", line)

    print("\nSelected:")
    for it in result["selected"]:
        print("  ", it["name"], "fraction =", round(it["fraction"], 4),
              "time =", it["taken_weight"], "value =", round(it["taken_value"], 2))
    print("Not selected:", [it["name"] for it in result["rejected"]])
    print("Total value :", round(result["total_value"], 2))
    print("Time used   :", result["total_weight"], "| Remaining:", result["remaining"])

    print("\n--- Edge cases ---")
    print("Empty items     :", fractional_knapsack([], 50)["total_value"])
    print("Zero capacity   :", fractional_knapsack(study_items, 0)["total_value"])
    big = fractional_knapsack(study_items, 1000)
    print("Capacity > total:", len(big["selected"]), "items, remaining =", big["remaining"])
    one = fractional_knapsack([{"name": "A", "value": 10, "weight": 20}], 5)
    print("Single, partial :", round(one["selected"][0]["fraction"], 2),
          "value =", one["total_value"])
    try:
        fractional_knapsack([{"name": "Bad", "value": 1, "weight": 0}], 10)
    except ValueError as error:
        print("Zero weight     :", error)