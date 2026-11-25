"""
insertion_sort.py - Insertion Sort.

Idea (like sorting playing cards in your hand):
  - The left part of the list is always sorted.
  - Take the next item (the "current" item).
  - Compare it with the items to its left, moving bigger ones one step right.
  - Drop the current item into the gap. Repeat until the list ends.

Time  : Best O(n) (already sorted), Average O(n^2), Worst O(n^2)
Space : O(1) extra memory (sorts inside one copy of the list)
Stable: yes
Good for small lists - which is exactly how the planner uses it.
"""

from algorithms import make_key


def insertion_sort(items, key=None, log=None):
    """
    Return a NEW sorted list. The original list is not changed.

    items : list to sort
    key   : function that returns the value to compare (default: the item itself)
    log   : optional list; if given, every comparison and insertion is added to it
    """
    if key is None:
        key = lambda item: item

    data = list(items)

    # Start at index 1: a single item (index 0) is already "sorted".
    for i in range(1, len(data)):
        current = data[i]
        current_value = key(current)
        j = i - 1  # look at the item just left of current

        if log is not None:
            log.append("Pass " + str(i) + ": take " + str(current_value)
                       + "   sorted part = " + _show(data[:i], key))

        # Move bigger items one step to the right.
        while j >= 0:
            if log is not None:
                log.append("   compare " + str(key(data[j])) + " > "
                           + str(current_value) + " ? " + str(key(data[j]) > current_value))
            if key(data[j]) > current_value:
                data[j + 1] = data[j]
                j -= 1
            else:
                break  # found the right place

        data[j + 1] = current  # insert into the gap

        if log is not None:
            log.append("   insert at position " + str(j + 1)
                       + "  -> " + _show(data[:i + 1], key))
    return data


def _show(data, key):
    """Short text for the log: the values being compared."""
    return str([key(item) for item in data])


def insertion_sort_topics(topics, criterion, log=None):
    """Sort topic dictionaries by 'deadline', 'priority', 'duration' or 'name'."""
    return insertion_sort(topics, make_key(criterion), log)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.insertion_sort
# ----------------------------------------------------------------------
if __name__ == "__main__":
    numbers = [5, 2, 4, 6, 1, 3]
    steps = []
    print("Input :", numbers)
    print("Output:", insertion_sort(numbers, log=steps))
    print("\nStep-by-step:")
    for line in steps:
        print(line)

    print("\n--- Sorting topics by priority (High first) ---")
    topics = [
        {"topic_name": "Arrays", "estimated_duration": 30, "priority": "Low",    "deadline": None},
        {"topic_name": "Trees",  "estimated_duration": 60, "priority": "High",   "deadline": "2026-12-05"},
        {"topic_name": "SQL",    "estimated_duration": 45, "priority": "Medium", "deadline": "2026-12-01"},
        {"topic_name": "Graphs", "estimated_duration": 50, "priority": "High",   "deadline": "2026-12-03"},
    ]
    for t in insertion_sort_topics(topics, "priority"):
        print(t["topic_name"], t["priority"])

    print("\n--- Sorting topics by deadline (no deadline goes last) ---")
    for t in insertion_sort_topics(topics, "deadline"):
        print(t["topic_name"], t["deadline"])

    print("\n--- Edge cases ---")
    print("Empty         :", insertion_sort([]))
    print("Single        :", insertion_sort([5]))
    print("Duplicates    :", insertion_sort([3, 1, 3, 2, 1]))
    print("Already sorted:", insertion_sort([1, 2, 3, 4]))
    print("Reversed      :", insertion_sort([4, 3, 2, 1]))