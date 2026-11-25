"""
zero_one_knapsack.py - 0/1 Knapsack (dynamic programming, 2-D table).

Problem: we have n study topics. Each topic has
    weight = its study time in minutes (must be a whole number > 0)
    value  = its importance (High=5, Medium=3, Low=1)
and we have W minutes of free time. Choose topics to get the MAXIMUM total
value without going over W minutes. Each topic is taken COMPLETELY or NOT AT ALL
(that is the "0/1" in the name).

DP table:  dp[i][w] = the best total value using only the FIRST i topics when
           the time limit is w minutes.
Recurrence for topic i with weight wt and value v:
    if wt > w :  dp[i][w] = dp[i-1][w]                        (cannot fit)
    else      :  dp[i][w] = max( dp[i-1][w],                  (skip topic i)
                                 dp[i-1][w - wt] + v )        (take topic i)
Row 0 and column 0 are all zeros (no topics, or no time, means no value).
The answer is dp[n][W]. To find WHICH topics were taken, walk backwards from
dp[n][W]: if dp[i][w] differs from dp[i-1][w], topic i was taken.

Time  : O(n * W)
Space : O(n * W) for the 2-D table
(n = number of topics, W = available minutes)
"""

from algorithms import PRIORITY_VALUE


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


def zero_one_knapsack(items, capacity, log=None):
    """
    items    : list of dicts with "name", "value", "weight" (whole minutes > 0)
    capacity : available study time in whole minutes (0 or more)
    log      : optional list; explanation lines are added to it

    Returns a dictionary:
      "selected"    : topics taken completely (in the original input order)
      "rejected"    : topics not taken, each with a "reason"
      "total_value" : best total value found
      "total_weight": study time used (never more than capacity)
      "remaining"   : unused time
      "table"       : the DP table (list of rows) for display
    """
    if not isinstance(capacity, int) or capacity < 0:
        raise ValueError("Capacity must be a whole number of minutes, 0 or more")
    for item in items:
        if not isinstance(item["weight"], int) or item["weight"] <= 0:
            raise ValueError(item["name"] + ": time must be a whole number above zero")
        if item["value"] < 0:
            raise ValueError(item["name"] + ": value cannot be negative")

    n = len(items)

    # Build the table: n+1 rows, capacity+1 columns, all zeros to start.
    table = []
    for _ in range(n + 1):
        table.append([0] * (capacity + 1))

    # Fill the table row by row (row i uses the first i items).
    for i in range(1, n + 1):
        weight = items[i - 1]["weight"]
        value = items[i - 1]["value"]
        for w in range(capacity + 1):
            table[i][w] = table[i - 1][w]                 # option 1: skip topic
            if weight <= w:
                take_value = table[i - 1][w - weight] + value  # option 2: take topic
                if take_value > table[i][w]:
                    table[i][w] = take_value
        if log is not None:
            log.append("Row " + str(i) + " (" + items[i - 1]["name"] + ", time "
                       + str(weight) + ", value " + str(value) + "): best value at "
                       + str(capacity) + " min = " + str(table[i][capacity]))

    # Walk backwards to find which topics were taken.
    chosen = [False] * n
    w = capacity
    for i in range(n, 0, -1):
        if table[i][w] != table[i - 1][w]:  # value changed, so topic i was taken
            chosen[i - 1] = True
            if log is not None:
                log.append("Backtrack: " + items[i - 1]["name"] + " TAKEN (dp["
                           + str(i) + "][" + str(w) + "]=" + str(table[i][w])
                           + " differs from dp[" + str(i - 1) + "][" + str(w) + "]="
                           + str(table[i - 1][w]) + ")")
            w -= items[i - 1]["weight"]
        elif log is not None:
            log.append("Backtrack: " + items[i - 1]["name"] + " not taken (dp["
                       + str(i) + "][" + str(w) + "] equals dp[" + str(i - 1) + "]["
                       + str(w) + "])")

    selected = []
    rejected = []
    used = 0
    for index in range(n):
        item = dict(items[index])  # copy, so the input is never changed
        if chosen[index]:
            selected.append(item)
            used += item["weight"]
        else:
            if item["weight"] > capacity:
                item["reason"] = "needs " + str(item["weight"]) + " min, more than all available time"
            else:
                item["reason"] = "taking it would give less total value than the chosen topics"
            rejected.append(item)

    return {
        "selected": selected,
        "rejected": rejected,
        "total_value": table[n][capacity],
        "total_weight": used,
        "remaining": capacity - used,
        "table": table,
    }


def format_dp_table(items, table, capacity):
    """Return the DP table as text (best for small capacities)."""
    width = max(4, len(str(table[-1][capacity])) + 1)
    lines = []
    header = "time limit".ljust(16) + "".join(str(w).rjust(width) for w in range(capacity + 1))
    lines.append(header)
    names = ["(no topics)"] + [item["name"] for item in items]
    for i, row in enumerate(table):
        lines.append(names[i][:15].ljust(16) + "".join(str(v).rjust(width) for v in row))
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.zero_one_knapsack
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Small example so the whole DP table fits on screen.
    small = [
        {"name": "Arrays", "value": 3, "weight": 2},
        {"name": "Trees",  "value": 4, "weight": 3},
        {"name": "SQL",    "value": 5, "weight": 4},
        {"name": "Graphs", "value": 6, "weight": 5},
    ]
    print("=== Small example (time in minutes), capacity = 5 ===")
    steps = []
    result = zero_one_knapsack(small, 5, log=steps)
    print(format_dp_table(small, result["table"], 5))
    print("\nStep-by-step:")
    for line in steps:
        print(" ", line)
    print("\nSelected:", [i["name"] for i in result["selected"]])
    print("Rejected:", [i["name"] for i in result["rejected"]])
    print("Total value:", result["total_value"], "| Time used:", result["total_weight"],
          "| Remaining:", result["remaining"])

    # Realistic example: compare with the fractional version (value 14.17).
    real = [
        {"name": "Arrays",   "value": 5, "weight": 30},
        {"name": "Trees",    "value": 5, "weight": 60},
        {"name": "SQL",      "value": 3, "weight": 45},
        {"name": "Graphs",   "value": 5, "weight": 20},
        {"name": "Networks", "value": 1, "weight": 40},
    ]
    print("\n=== Realistic example, capacity = 100 minutes ===")
    result = zero_one_knapsack(real, 100)
    print("Selected:", [(i["name"], i["weight"]) for i in result["selected"]])
    print("Rejected:")
    for i in result["rejected"]:
        print("  ", i["name"], "-", i["reason"])
    print("Total value:", result["total_value"], "| Time used:", result["total_weight"],
          "| Remaining:", result["remaining"])
    print("Table size:", len(result["table"]), "rows x", len(result["table"][0]), "columns")

    print("\n=== Edge cases ===")
    print("Empty items      :", zero_one_knapsack([], 50)["total_value"])
    print("Zero capacity    :", zero_one_knapsack(real, 0)["total_value"])
    one_fit = zero_one_knapsack([{"name": "A", "value": 4, "weight": 10}], 10)
    print("Single, fits     :", [i["name"] for i in one_fit["selected"]])
    one_no = zero_one_knapsack([{"name": "A", "value": 4, "weight": 10}], 9)
    print("Single, too big  :", [i["name"] for i in one_no["selected"]], "|", one_no["rejected"][0]["reason"])
    everything = zero_one_knapsack(real, 1000)
    print("Everything fits  :", len(everything["selected"]), "topics, value", everything["total_value"])
    same = [{"name": "X", "value": 5, "weight": 10}, {"name": "Y", "value": 5, "weight": 10}]
    print("Equal topics     :", [i["name"] for i in zero_one_knapsack(same, 10)["selected"]])
    try:
        zero_one_knapsack([{"name": "Bad", "value": 1, "weight": 0}], 10)
    except ValueError as error:
        print("Zero time        :", error)