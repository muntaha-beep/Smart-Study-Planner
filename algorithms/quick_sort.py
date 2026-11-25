"""
quick_sort.py - Quick Sort (divide and conquer, uses partitioning).

Idea:
  1. Choose a PIVOT (here: the median of the first, middle and last items).
  2. PARTITION: rearrange the list so that every item smaller than or equal to
     the pivot is on its left and every bigger item is on its right.
     The pivot is now in its FINAL position.
  3. Repeat steps 1-2 for the left part and the right part (recursion).

Time  : Best and Average O(n log n), Worst O(n^2)
        (worst case = very unbalanced splits; median-of-three makes it unlikely
         on already-sorted or reverse-sorted input)
Space : O(log n) average for the recursion stack (sorts inside one copy)
Stable: no (equal items may change their relative order)
"""

from algorithms import make_key


def quick_sort(items, key=None, log=None):
    """
    Return a NEW sorted list. The original list is not changed.

    items : list to sort
    key   : function that returns the value to compare (default: the item itself)
    log   : optional list; if given, pivot and partition steps are added to it
    """
    if key is None:
        key = lambda item: item

    data = list(items)
    _quick_sort(data, 0, len(data) - 1, key, log, 0)
    return data


def _quick_sort(data, low, high, key, log, depth):
    """Sort data[low..high] (both ends included), working in place."""
    if low >= high:  # 0 or 1 item: nothing to do
        return

    if log is not None:
        log.append("  " * depth + "Sort positions " + str(low) + ".." + str(high)
                   + ": " + _show(data[low:high + 1], key))

    pivot_position = _partition(data, low, high, key, log, depth)

    _quick_sort(data, low, pivot_position - 1, key, log, depth + 1)   # left part
    _quick_sort(data, pivot_position + 1, high, key, log, depth + 1)  # right part


def _choose_pivot(data, low, high, key):
    """Median-of-three: return the index of the middle value of first/middle/last."""
    middle = (low + high) // 2
    a = key(data[low])
    b = key(data[middle])
    c = key(data[high])

    if (a <= b <= c) or (c <= b <= a):
        return middle
    if (b <= a <= c) or (c <= a <= b):
        return low
    return high


def _partition(data, low, high, key, log, depth):
    """
    Partition data[low..high] around a pivot and return the pivot's final index.
    """
    # Step 1: pick the pivot and move it to the end, out of the way.
    pivot_index = _choose_pivot(data, low, high, key)
    data[pivot_index], data[high] = data[high], data[pivot_index]
    pivot_value = key(data[high])

    if log is not None:
        log.append("  " * depth + "  pivot = " + str(pivot_value))

    # Step 2: i marks the end of the "smaller or equal" zone.
    i = low - 1
    for j in range(low, high):
        if key(data[j]) <= pivot_value:
            i += 1
            data[i], data[j] = data[j], data[i]  # grow the small zone

    # Step 3: put the pivot right after the small zone (its final position).
    data[i + 1], data[high] = data[high], data[i + 1]

    if log is not None:
        log.append("  " * depth + "  after partition: "
                   + _show(data[low:high + 1], key)
                   + "  (pivot now at position " + str(i + 1) + ")")
    return i + 1


def _show(data, key):
    """Short text for the log: the values being compared."""
    return str([key(item) for item in data])


def quick_sort_topics(topics, criterion, log=None):
    """Sort topic dictionaries by 'deadline', 'priority', 'duration' or 'name'."""
    return quick_sort(topics, make_key(criterion), log)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.quick_sort
# ----------------------------------------------------------------------
if __name__ == "__main__":
    numbers = [10, 80, 30, 90, 40, 50, 70]
    steps = []
    print("Input :", numbers)
    print("Output:", quick_sort(numbers, log=steps))
    print("\nStep-by-step:")
    for line in steps:
        print(line)

    print("\n--- Sorting topics by duration ---")
    topics = [
        {"topic_name": "Trees",  "estimated_duration": 60, "priority": "High",   "deadline": "2026-12-05"},
        {"topic_name": "Arrays", "estimated_duration": 30, "priority": "Low",    "deadline": None},
        {"topic_name": "SQL",    "estimated_duration": 45, "priority": "Medium", "deadline": "2026-12-01"},
        {"topic_name": "Graphs", "estimated_duration": 50, "priority": "High",   "deadline": "2026-12-03"},
    ]
    for t in quick_sort_topics(topics, "duration"):
        print(t["topic_name"], t["estimated_duration"])

    print("\n--- Edge cases ---")
    print("Empty         :", quick_sort([]))
    print("Single        :", quick_sort([5]))
    print("Duplicates    :", quick_sort([3, 1, 3, 2, 1]))
    print("Already sorted:", quick_sort([1, 2, 3, 4, 5]))
    print("Reversed      :", quick_sort([5, 4, 3, 2, 1]))
    print("All equal     :", quick_sort([7, 7, 7, 7]))