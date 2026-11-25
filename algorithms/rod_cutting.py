"""
rod_cutting.py - Rod Cutting (dynamic programming, bottom-up).

*** This is a study-TIME-ALLOCATION SIMULATION. ***
It does not pick real topics from the database. It answers: "If I have T minutes
and I can study in blocks of certain lengths, each block giving a certain
benefit, how should I cut my time into blocks to get the most total benefit?"

Mapping to the classic problem:
    rod length          -> total available study time T
    piece lengths       -> allowed study-block lengths (for example 25, 45, 60)
    piece prices        -> benefit of each block length
    cut the rod         -> split the time into blocks

Recurrence (best[j] = best total benefit that j minutes of time can give):
    best[0] = 0
    best[j] = max( best[j - L] + benefit[L]   for every block length L <= j )
Extension for real life: if no block fits the leftover time, those minutes can
stay UNUSED (benefit 0), so  best[j] can also be best[j - 1].
The chosen block for each j is remembered in last_block[j], so we can rebuild
the actual list of blocks by walking back from T.

Time  : O(T * m) where m = number of block lengths. When every length 1..T is
        allowed (the textbook version) m = T, so this is O(T^2).
Space : O(T) for the best[] and last_block[] arrays
Blocks may be used any number of times.
"""


def rod_cutting(total_time, blocks, log=None):
    """
    total_time : available study time (whole minutes, 0 or more)
    blocks     : dict {block_length: benefit}, e.g. {25: 4, 45: 8, 60: 11}
    log        : optional list; explanation lines are added to it

    Returns a dictionary:
      "blocks"      : the chosen block lengths, in the order they are found
      "counts"      : dict {block_length: how many times used}
      "total_value" : maximum total benefit
      "used"        : minutes covered by blocks
      "unused"      : minutes left over (no block could use them profitably)
      "best"        : the DP array best[0..total_time]
      "last_block"  : last_block[j] = block ending the best plan for j minutes
                      (0 means "this minute is left unused")
    """
    if not isinstance(total_time, int) or total_time < 0:
        raise ValueError("Total time must be a whole number of minutes, 0 or more")
    for length, benefit in blocks.items():
        if not isinstance(length, int) or length <= 0:
            raise ValueError("Block lengths must be whole numbers above zero")
        if benefit < 0:
            raise ValueError("Block benefit cannot be negative")

    lengths = sorted(blocks)  # a tiny list of block sizes, ascending

    best = [0] * (total_time + 1)
    last_block = [0] * (total_time + 1)

    # Fill the table from 1 minute up to total_time (bottom-up).
    for j in range(1, total_time + 1):
        best_value = -1
        chosen = 0
        for length in lengths:
            if length <= j:
                candidate = best[j - length] + blocks[length]
                if candidate > best_value:
                    best_value = candidate
                    chosen = length
        # Option: leave the last minute unused (only if it is strictly better).
        if best[j - 1] > best_value:
            best_value = best[j - 1]
            chosen = 0
        best[j] = best_value
        last_block[j] = chosen

        if log is not None:
            if chosen == 0:
                text = "last minute unused"
            else:
                text = ("last block = " + str(chosen) + " min, "
                        + "best[" + str(j - chosen) + "] + benefit "
                        + str(blocks[chosen]) + " = " + str(best_value))
            log.append("best[" + str(j) + "] = " + str(best_value) + "   (" + text + ")")

    # Walk back from total_time to rebuild the chosen blocks.
    chosen_blocks = []
    unused = 0
    j = total_time
    while j > 0:
        if last_block[j] == 0:
            unused += 1
            j -= 1
        else:
            chosen_blocks.append(last_block[j])
            if log is not None:
                log.append("Backtrack: at " + str(j) + " min use a " + str(last_block[j])
                           + "-min block, go to " + str(j - last_block[j]))
            j -= last_block[j]

    counts = {}
    for length in chosen_blocks:
        counts[length] = counts.get(length, 0) + 1

    return {
        "blocks": chosen_blocks,
        "counts": counts,
        "total_value": best[total_time],
        "used": total_time - unused,
        "unused": unused,
        "best": best,
        "last_block": last_block,
    }


def format_dp_table(best, last_block):
    """Return the DP array as a small text table."""
    lines = ["time  best  last block"]
    for j in range(len(best)):
        last = "-" if j == 0 else ("unused" if last_block[j] == 0 else str(last_block[j]))
        lines.append(str(j).rjust(4) + str(best[j]).rjust(6) + "  " + last)
    return "\n".join(lines)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.rod_cutting
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Textbook example: lengths 1..8 (think of 1 unit = 15 study minutes).
    prices = {1: 1, 2: 5, 3: 8, 4: 9, 5: 10, 6: 17, 7: 17, 8: 20}
    print("=== Textbook example: total length 8 ===")
    print("Block benefits:", prices)
    steps = []
    result = rod_cutting(8, prices, log=steps)
    print()
    print(format_dp_table(result["best"], result["last_block"]))
    print("\nStep-by-step:")
    for line in steps:
        print(" ", line)
    print("\nChosen blocks:", result["blocks"], "| counts:", result["counts"])
    print("Total benefit:", result["total_value"], "| used:", result["used"],
          "| unused:", result["unused"])

    # Study-time example in real minutes.
    study_blocks = {25: 4, 45: 8, 60: 11, 90: 18}
    print("\n=== Study example: 120 minutes, blocks", study_blocks, "===")
    result = rod_cutting(120, study_blocks)
    print("Chosen blocks:", result["blocks"], "| total benefit:", result["total_value"],
          "| used:", result["used"], "| unused:", result["unused"])

    result = rod_cutting(40, study_blocks)
    print("40 minutes      :", result["blocks"], "| benefit", result["total_value"],
          "| unused:", result["unused"])

    print("\n=== Edge cases ===")
    print("Zero time       :", rod_cutting(0, study_blocks)["total_value"])
    print("No blocks       :", rod_cutting(50, {})["total_value"])
    print("Time < smallest :", rod_cutting(10, study_blocks)["blocks"],
          "unused =", rod_cutting(10, study_blocks)["unused"])
    print("Single block    :", rod_cutting(30, {10: 3})["blocks"])
    try:
        rod_cutting(10, {0: 5})
    except ValueError as error:
        print("Zero-length blk :", error)