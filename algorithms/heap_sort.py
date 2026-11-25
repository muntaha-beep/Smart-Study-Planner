"""
heap_sort.py - Heap Sort (uses a max-heap stored inside the list itself).

A MAX-HEAP is a "tree" stored in a list where every parent is bigger than or
equal to its children. For an item at index i:
    left child  = 2*i + 1
    right child = 2*i + 2
    parent      = (i - 1) // 2
So the biggest item is always at index 0.

Idea:
  1. BUILD the max-heap from the list (heapify from the last parent up to 0).
  2. Swap the biggest item (index 0) with the last item of the heap.
     That biggest item is now in its final place; shrink the heap by one.
  3. HEAPIFY the new root down to restore the heap. Repeat step 2-3.

Time  : Best, Average and Worst O(n log n)
Space : O(1) extra memory (in place, on one copy of the list)
Stable: no
"""

from algorithms import make_key


def heap_sort(items, key=None, log=None):
    """
    Return a NEW list sorted from smallest to largest. Original is not changed.

    items : list to sort
    key   : function that returns the value to compare (default: the item itself)
    log   : optional list; if given, heap building and extraction steps are added
    """
    if key is None:
        key = lambda item: item

    data = list(items)
    n = len(data)

    # Step 1: build the max-heap. Leaves are already heaps, so start at the
    # last item that has a child: index n//2 - 1.
    if log is not None and n > 1:
        log.append("BUILD HEAP from " + _show(data, key))
    for start in range(n // 2 - 1, -1, -1):
        _heapify(data, n, start, key, log)
    if log is not None and n > 1:
        log.append("Max-heap built: " + _show(data, key))

    # Step 2 and 3: move the biggest item to the end, then repair the heap.
    for end in range(n - 1, 0, -1):
        data[0], data[end] = data[end], data[0]
        if log is not None:
            log.append("EXTRACT: swap root with position " + str(end) + " -> "
                       + _show(data, key) + "   (sorted tail starts at " + str(end) + ")")
        _heapify(data, end, 0, key, log)  # heap now has only 'end' items
    return data


def _heapify(data, heap_size, root, key, log):
    """
    Push data[root] down until the subtree below it is a valid max-heap.
    Only the first heap_size items count as part of the heap.
    """
    while True:
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2

        if left < heap_size and key(data[left]) > key(data[largest]):
            largest = left
        if right < heap_size and key(data[right]) > key(data[largest]):
            largest = right

        if largest == root:  # root is already bigger than both children
            return

        data[root], data[largest] = data[largest], data[root]
        if log is not None:
            log.append("   heapify: swap position " + str(root) + " and "
                       + str(largest) + " -> " + _show(data[:heap_size], key))
        root = largest  # continue checking the subtree we just changed


def _show(data, key):
    """Short text for the log: the values being compared."""
    return str([key(item) for item in data])


def heap_sort_topics(topics, criterion, log=None):
    """Sort topic dictionaries by 'deadline', 'priority', 'duration' or 'name'."""
    return heap_sort(topics, make_key(criterion), log)


# ----------------------------------------------------------------------
# Demo: run with   python -m algorithms.heap_sort
# ----------------------------------------------------------------------
if __name__ == "__main__":
    numbers = [12, 11, 13, 5, 6, 7]
    steps = []
    print("Input :", numbers)
    print("Output:", heap_sort(numbers, log=steps))
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
    for t in heap_sort_topics(topics, "duration"):
        print(t["topic_name"], t["estimated_duration"])

    print("\n--- Edge cases ---")
    print("Empty         :", heap_sort([]))
    print("Single        :", heap_sort([5]))
    print("Duplicates    :", heap_sort([3, 1, 3, 2, 1]))
    print("Already sorted:", heap_sort([1, 2, 3, 4, 5]))
    print("Reversed      :", heap_sort([5, 4, 3, 2, 1]))
    print("All equal     :", heap_sort([7, 7, 7, 7]))