"""
lcs.py - Longest Common Subsequence (dynamic programming, 2-D table).

Problem: given two ordered lists of study topics, A and B, find the longest list
of topics that appears in BOTH, in the same order (but not necessarily next to
each other). Example:
    A = Introduction, Arrays, Linked Lists, Trees, Graphs
    B = Introduction, Arrays, Stacks,       Trees, Graphs
    LCS = Introduction, Arrays, Trees, Graphs   (length 4)

DP table:  dp[i][j] = length of the LCS of the first i items of A and the first
           j items of B.
Recurrence:
    if A[i-1] equals B[j-1] :  dp[i][j] = dp[i-1][j-1] + 1
    else                    :  dp[i][j] = max( dp[i-1][j], dp[i][j-1] )
Row 0 and column 0 are zeros (an empty list has nothing in common).
The answer length is dp[m][n]. To rebuild the actual topics, walk backwards from
dp[m][n]: equal items are part of the LCS (move diagonally); otherwise move
towards the neighbour with the bigger value.

Names are compared ignoring upper/lower case and extra spaces.

Time  : O(m * n)
Space : O(m * n) for the table
(m = length of A, n = length of B)
"""


def _same(first, second):
    """Compare two topic names, ignoring case and surrounding spaces."""
    return first.strip().lower() == second.strip().lower()


def lcs(list_a, list_b, log=None):
    """
    list_a, list_b : lists of topic names (text)
    log            : optional list; explanation lines are added to it

    Returns a dictionary:
      "length"    : length of the longest common subsequence
      "common"    : the common topics (names as written in list_a), in order
      "positions" : list of (index in A, index in B) pairs for the common topics
      "table"     : the DP table (list of rows)
    """
    m = len(list_a)
    n = len(list_b)

    # Table with m+1 rows and n+1 columns, filled with zeros.
    table = []
    for _ in range(m + 1):
        table.append([0] * (n + 1))

    # Fill the table row by row.
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if _same(list_a[i - 1], list_b[j - 1]):
                table[i][j] = table[i - 1][j - 1] + 1
            else:
                table[i][j] = max(table[i - 1][j], table[i][j - 1])

    if log is not None:
        log.append("Table filled: " + str(m) + " x " + str(n) + " comparisons. "
                   + "LCS length = dp[" + str(m) + "][" + str(n) + "] = " + str(table[m][n]))

    # Walk backwards to rebuild the subsequence.
    positions = []
    i = m
    j = n
    while i > 0 and j > 0:
        if _same(list_a[i - 1], list_b[j - 1]):
            positions.append((i - 1, j - 1))
            if log is not None:
                log.append("Backtrack: '" + list_a[i - 1] + "' matches (A" + str(i)
                           + " = B" + str(j) + ") -> part of LCS, move diagonally")
            i -= 1
            j -= 1
        elif table[i - 1][j] >= table[i][j - 1]:
            if log is not None:
                log.append("Backtrack: no match at A" + str(i) + "/B" + str(j)
                           + ", dp above (" + str(table[i - 1][j]) + ") >= dp left ("
                           + str(table[i][j - 1]) + ") -> move up (skip '" + list_a[i - 1] + "' in A)")
            i -= 1
        else:
            if log is not None:
                log.append("Backtrack: no match at A" + str(i) + "/B" + str(j)
                           + ", dp left (" + str(table[i][j - 1]) + ") > dp above ("
                           + str(table[i - 1][j]) + ") -> move left (skip '" + list_b[j - 1] + "' in B)")
            j -= 1

    positions.reverse()  # we collected them from the end, so flip the order
    common = [list_a[a_index] for a_index, _ in positions]

    return {
        "length": table[m][n],
        "common": common,
        "positions": positions,
        "table": table,
    }


def format_dp_table(list_a, list_b, table):
    """Return the DP table as text (best for short lists)."""
    width = 9
    short = lambda text: text[:width - 1]
    lines = []
    lines.append(" " * (width + 1) + "".rjust(width) + "".join(short(b).rjust(width) for b in list_b))
    row_names = ["(empty)"] + list(list_a)
    for i, row in enumerate(table):
        lines.append(short(row_names[i]).ljust(width + 1) + "".join(str(v).rjust(width) for v in row))
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.lcs
# ----------------------------------------------------------------------
if __name__ == "__main__":
    plan_a = ["Introduction", "Arrays", "Linked Lists", "Trees", "Graphs"]
    plan_b = ["Introduction", "Arrays", "Stacks", "Trees", "Graphs"]
    print("List A:", plan_a)
    print("List B:", plan_b)

    steps = []
    result = lcs(plan_a, plan_b, log=steps)
    print("\nDP table:")
    print(format_dp_table(plan_a, plan_b, result["table"]))
    print("\nStep-by-step:")
    for line in steps:
        print(" ", line)
    print("\nLCS length:", result["length"])
    print("Common topics:", result["common"])
    print("Positions (A index, B index):", result["positions"])

    print("\n=== Edge cases ===")
    print("Both empty      :", lcs([], [])["common"])
    print("One empty       :", lcs(["A", "B"], [])["common"])
    print("No common       :", lcs(["A", "B"], ["C", "D"])["common"])
    print("Identical       :", lcs(["A", "B", "C"], ["A", "B", "C"])["common"])
    print("Single, equal   :", lcs(["Trees"], ["Trees"])["common"])
    print("Different case  :", lcs(["Arrays", "TREES"], ["arrays", "trees"])["common"])
    print("Different order :", lcs(["A", "B", "C"], ["C", "B", "A"])["length"])
    print("Duplicates      :", lcs(["A", "A", "B"], ["A", "B", "A"])["common"])