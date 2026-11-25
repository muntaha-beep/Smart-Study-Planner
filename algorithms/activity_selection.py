"""
activity_selection.py - Activity Selection (greedy algorithm).

Problem: given study sessions that each have a START time and a FINISH time,
pick the MAXIMUM number of sessions that do not overlap.

Greedy idea:
  1. Sort all sessions by FINISH time (earliest finish first).
  2. Pick the first session.
  3. Go through the rest: pick a session only if it STARTS at or after the
     finish time of the last picked session. Otherwise reject it (overlap).
Finishing early leaves the most room for the sessions that come after.

Time  : O(n log n) for sorting + O(n) for the selection = O(n log n)
Space : O(n)

NOTE: this is for choosing between sessions that already have fixed times.
It does NOT choose topics by priority (0/1 Knapsack does that).
Times are stored as minutes since midnight (09:30 -> 570).
"""

from algorithms.merge_sort import merge_sort


# ----------------------------------------------------------------------
# Time helpers
# ----------------------------------------------------------------------
def time_to_minutes(text):
    """'09:30' -> 570. Raises ValueError for a bad time."""
    parts = text.strip().split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError("Time must look like HH:MM, for example 09:30")
    hours, minutes = int(parts[0]), int(parts[1])
    if hours > 23 or minutes > 59:
        raise ValueError("Time must be between 00:00 and 23:59")
    return hours * 60 + minutes


def minutes_to_time(total):
    """570 -> '09:30'."""
    return str(total // 60).zfill(2) + ":" + str(total % 60).zfill(2)


def make_activity(name, start_text, finish_text):
    """Build one activity dictionary from 'HH:MM' texts."""
    return {
        "name": name,
        "start": time_to_minutes(start_text),
        "finish": time_to_minutes(finish_text),
    }


def _label(activity):
    return (activity["name"] + " (" + minutes_to_time(activity["start"])
            + "-" + minutes_to_time(activity["finish"]) + ")")


# ----------------------------------------------------------------------
# The algorithm
# ----------------------------------------------------------------------
def activity_selection(activities, log=None):
    """
    Choose the maximum number of non-overlapping activities.

    activities : list of dicts with "name", "start", "finish" (minutes)
    log        : optional list; explanation lines are added to it

    Returns (selected, rejected). Each item is a copy of the activity with an
    extra "reason" text explaining the decision.
    """
    for activity in activities:
        if activity["finish"] <= activity["start"]:
            raise ValueError(activity["name"] + ": finish time must be after start time")

    # Step 1: sort by finish time using our own Merge Sort.
    ordered = merge_sort(activities, key=lambda a: a["finish"])
    if log is not None:
        log.append("Sorted by finish time: " + ", ".join(_label(a) for a in ordered))

    selected = []
    rejected = []
    last_finish = None

    # Step 2 and 3: greedy choice.
    for activity in ordered:
        item = dict(activity)  # copy, so the input is never changed

        if last_finish is None:
            item["reason"] = "first activity (earliest finish)"
            selected.append(item)
            last_finish = activity["finish"]
            if log is not None:
                log.append("SELECT " + _label(activity) + " - " + item["reason"])

        elif activity["start"] >= last_finish:
            item["reason"] = ("starts at " + minutes_to_time(activity["start"])
                              + ", at or after the previous finish at "
                              + minutes_to_time(last_finish) + " (compatible)")
            selected.append(item)
            last_finish = activity["finish"]
            if log is not None:
                log.append("SELECT " + _label(activity) + " - " + item["reason"])

        else:
            item["reason"] = ("starts at " + minutes_to_time(activity["start"])
                              + ", before the previous finish at "
                              + minutes_to_time(last_finish) + " (overlap)")
            rejected.append(item)
            if log is not None:
                log.append("REJECT " + _label(activity) + " - " + item["reason"])

    return selected, rejected


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.activity_selection
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sessions = [
        make_activity("Arrays",   "09:00", "10:30"),
        make_activity("Trees",    "09:30", "10:00"),
        make_activity("Graphs",   "10:00", "11:00"),
        make_activity("SQL",      "10:30", "12:00"),
        make_activity("OS",       "11:00", "11:30"),
        make_activity("Networks", "11:30", "12:30"),
    ]
    print("Input sessions:")
    for s in sessions:
        print("  ", _label(s))

    steps = []
    chosen, skipped = activity_selection(sessions, log=steps)

    print("\nStep-by-step:")
    for line in steps:
        print(" ", line)

    print("\nSelected (" + str(len(chosen)) + "):", [a["name"] for a in chosen])
    print("Rejected (" + str(len(skipped)) + "):", [a["name"] for a in skipped])

    print("\n--- Edge cases ---")
    print("Empty            :", activity_selection([]))
    one = [make_activity("A", "09:00", "10:00")]
    print("Single           :", [a["name"] for a in activity_selection(one)[0]])
    overlap = [make_activity("A", "09:00", "11:00"), make_activity("B", "10:00", "12:00"),
               make_activity("C", "10:30", "11:30")]
    print("All overlap      :", [a["name"] for a in activity_selection(overlap)[0]])
    apart = [make_activity("A", "09:00", "10:00"), make_activity("B", "10:00", "11:00"),
             make_activity("C", "11:00", "12:00")]
    print("Back-to-back     :", [a["name"] for a in activity_selection(apart)[0]])
    try:
        activity_selection([make_activity("Bad", "10:00", "09:00")])
    except ValueError as error:
        print("Bad times        :", error)