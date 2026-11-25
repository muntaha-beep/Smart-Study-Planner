"""
merge_sort.py - Merge Sort (divide and conquer, uses recursion).

Idea:
  1. DIVIDE   : split the list into a left half and a right half.
  2. CONQUER  : sort each half by calling merge_sort again (recursion).
  3. COMBINE  : merge the two sorted halves into one sorted list.
A list with 0 or 1 items is already sorted - that is the stopping point.

Time  : O(n log n) in best, average and worst case
Space : O(n) extra memory (for the merged lists)
Stable: yes (equal items keep their original order)
"""

from algorithms import make_key


def merge_sort(items, key=None, log=None):
    """
    Return a NEW sorted list. The original list is not changed.

    items : list to sort (numbers, strings, or dictionaries)
    key   : function that returns the value to compare (default: the item itself)
    log   : optional list; if given, explanation lines are added to it
    """
    if key is None:
        key = lambda item: item
    return _split_and_merge(list(items), key, log, 0)


def _split_and_merge(data, key, log, depth):
    """Recursive part: divide, conquer, combine."""
    indent = "  " * depth

    # Base case: 0 or 1 item is already sorted.
    if len(data) <= 1:
        return data

    middle = len(data) // 2
    left = data[:middle]
    right = data[middle:]

    if log is not None:
        log.append(indent + "DIVIDE  " + _show(data, key)
                   + " -> " + _show(left, key) + " | " + _show(right, key))

    left_sorted = _split_and_merge(left, key, log, depth + 1)
    right_sorted = _split_and_merge(right, key, log, depth + 1)

    merged = _merge(left_sorted, right_sorted, key)

    if log is not None:
        log.append(indent + "MERGE   " + _show(left_sorted, key) + " + "
                   + _show(right_sorted, key) + " = " + _show(merged, key))
    return merged


def _merge(left, right, key):
    """Combine two already-sorted lists into one sorted list."""
    result = []
    i = 0  # position in left
    j = 0  # position in right

    while i < len(left) and j < len(right):
        # "<=" keeps the sort stable: on a tie, take from the left list first.
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # One list is finished; copy whatever remains of the other.
    while i < len(left):
        result.append(left[i])
        i += 1
    while j < len(right):
        result.append(right[j])
        j += 1
    return result


def _show(data, key):
    """Short text for the log: the values being compared."""
    return str([key(item) for item in data])


def merge_sort_topics(topics, criterion, log=None):
    """Sort topic dictionaries by 'deadline', 'priority', 'duration' or 'name'."""
    return merge_sort(topics, make_key(criterion), log)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.merge_sort
# ----------------------------------------------------------------------
if __name__ == "__main__":
    numbers = [38, 27, 43, 3, 9, 82, 10]
    steps = []
    print("Input :", numbers)
    print("Output:", merge_sort(numbers, log=steps))
    print("\nStep-by-step:")
    for line in steps:
        print(line)

    print("\n--- Sorting topics by duration ---")
    topics = [
        {"topic_name": "Trees",  "estimated_duration": 60, "priority": "High",   "deadline": "2026-12-05"},
        {"topic_name": "Arrays", "estimated_duration": 30, "priority": "Low",    "deadline": None},
        {"topic_name": "SQL",    "estimated_duration": 45, "priority": "Medium", "deadline": "2026-12-01"},
    ]
    for t in merge_sort_topics(topics, "duration"):
        print(t["topic_name"], t["estimated_duration"])

    print("\n--- Edge cases ---")
    print("Empty         :", merge_sort([]))
    print("Single        :", merge_sort([5]))
    print("Duplicates    :", merge_sort([3, 1, 3, 2, 1]))
    print("Already sorted:", merge_sort([1, 2, 3, 4]))
    print("Reversed      :", merge_sort([4, 3, 2, 1]))