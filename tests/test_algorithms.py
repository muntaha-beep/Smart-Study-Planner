"""
Tests for all nine algorithms.
Run from the project root:   python -m unittest tests.test_algorithms -v

(Python's built-in sorted() and itertools are used HERE ONLY, as an independent
"answer key" to check our hand-written algorithms. The algorithms themselves
never use them.)
"""

import itertools
import random
import unittest

from algorithms import make_key
from algorithms.merge_sort import merge_sort, merge_sort_topics
from algorithms.insertion_sort import insertion_sort, insertion_sort_topics
from algorithms.quick_sort import quick_sort, quick_sort_topics
from algorithms.heap_sort import heap_sort, heap_sort_topics
from algorithms.activity_selection import (
    activity_selection, make_activity, time_to_minutes, minutes_to_time)
from algorithms.fractional_knapsack import fractional_knapsack
from algorithms.zero_one_knapsack import zero_one_knapsack, topics_to_items
from algorithms.rod_cutting import rod_cutting
from algorithms.lcs import lcs

SORTS = {
    "merge": merge_sort,
    "insertion": insertion_sort,
    "quick": quick_sort,
    "heap": heap_sort,
}
TOPIC_SORTS = {
    "merge": merge_sort_topics,
    "insertion": insertion_sort_topics,
    "quick": quick_sort_topics,
    "heap": heap_sort_topics,
}


def sample_topics():
    return [
        {"topic_name": "Trees",  "estimated_duration": 60, "priority": "High",   "deadline": "2026-12-05"},
        {"topic_name": "arrays", "estimated_duration": 30, "priority": "Low",    "deadline": None},
        {"topic_name": "SQL",    "estimated_duration": 45, "priority": "Medium", "deadline": "2026-12-01"},
        {"topic_name": "Graphs", "estimated_duration": 50, "priority": "High",   "deadline": "2026-12-03"},
    ]


# ======================================================================
# Sorting algorithms (1-4)
# ======================================================================
class TestSortingAlgorithms(unittest.TestCase):
    def test_empty_list(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([]), [])

    def test_single_item(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([7]), [7])

    def test_normal_list(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([38, 27, 43, 3, 9, 82, 10]),
                                 [3, 9, 10, 27, 38, 43, 82])

    def test_duplicates(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([3, 1, 3, 2, 1, 3]), [1, 1, 2, 3, 3, 3])

    def test_all_equal(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([4, 4, 4, 4]), [4, 4, 4, 4])

    def test_already_sorted(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([1, 2, 3, 4, 5]), [1, 2, 3, 4, 5])

    def test_reverse_sorted(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])

    def test_negative_numbers_and_strings(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                self.assertEqual(sort([0, -5, 3, -1]), [-5, -1, 0, 3])
                self.assertEqual(sort(["pear", "apple", "fig"]), ["apple", "fig", "pear"])

    def test_random_lists_match_answer_key(self):
        generator = random.Random(42)
        for _ in range(200):
            data = [generator.randint(-20, 20) for _ in range(generator.randint(0, 25))]
            for name, sort in SORTS.items():
                with self.subTest(algorithm=name, data=data):
                    self.assertEqual(sort(data), sorted(data))

    def test_input_list_is_not_changed(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                original = [3, 1, 2]
                sort(original)
                self.assertEqual(original, [3, 1, 2])

    def test_log_is_filled(self):
        for name, sort in SORTS.items():
            with self.subTest(algorithm=name):
                steps = []
                sort([3, 1, 2], log=steps)
                self.assertGreater(len(steps), 0)

    def test_topics_by_duration(self):
        for name, sort in TOPIC_SORTS.items():
            with self.subTest(algorithm=name):
                result = [t["estimated_duration"] for t in sort(sample_topics(), "duration")]
                self.assertEqual(result, [30, 45, 50, 60])

    def test_topics_by_priority_high_first(self):
        for name, sort in TOPIC_SORTS.items():
            with self.subTest(algorithm=name):
                result = [t["priority"] for t in sort(sample_topics(), "priority")]
                self.assertEqual(result, ["High", "High", "Medium", "Low"])

    def test_topics_by_deadline_none_last(self):
        for name, sort in TOPIC_SORTS.items():
            with self.subTest(algorithm=name):
                result = [t["deadline"] for t in sort(sample_topics(), "deadline")]
                self.assertEqual(result, ["2026-12-01", "2026-12-03", "2026-12-05", None])

    def test_topics_by_name_ignores_case(self):
        for name, sort in TOPIC_SORTS.items():
            with self.subTest(algorithm=name):
                result = [t["topic_name"] for t in sort(sample_topics(), "name")]
                self.assertEqual(result, ["arrays", "Graphs", "SQL", "Trees"])

    def test_unknown_criterion_rejected(self):
        with self.assertRaises(ValueError):
            make_key("color")

    def test_merge_and_insertion_are_stable(self):
        # Trees and Graphs are both High; Trees came first so it must stay first.
        for sort in (merge_sort_topics, insertion_sort_topics):
            names = [t["topic_name"] for t in sort(sample_topics(), "priority")]
            self.assertLess(names.index("Trees"), names.index("Graphs"))


# ======================================================================
# Activity Selection (5)
# ======================================================================
class TestActivitySelection(unittest.TestCase):
    def names(self, activities):
        return [a["name"] for a in activities]

    def test_time_helpers(self):
        self.assertEqual(time_to_minutes("09:30"), 570)
        self.assertEqual(minutes_to_time(570), "09:30")
        with self.assertRaises(ValueError):
            time_to_minutes("25:00")
        with self.assertRaises(ValueError):
            time_to_minutes("9am")

    def test_example(self):
        sessions = [
            make_activity("Arrays",   "09:00", "10:30"),
            make_activity("Trees",    "09:30", "10:00"),
            make_activity("Graphs",   "10:00", "11:00"),
            make_activity("SQL",      "10:30", "12:00"),
            make_activity("OS",       "11:00", "11:30"),
            make_activity("Networks", "11:30", "12:30"),
        ]
        selected, rejected = activity_selection(sessions)
        self.assertEqual(self.names(selected), ["Trees", "Graphs", "OS", "Networks"])
        self.assertEqual(sorted(self.names(rejected)), ["Arrays", "SQL"])

    def test_empty(self):
        self.assertEqual(activity_selection([]), ([], []))

    def test_single(self):
        selected, rejected = activity_selection([make_activity("A", "09:00", "10:00")])
        self.assertEqual(self.names(selected), ["A"])
        self.assertEqual(rejected, [])

    def test_all_overlap_picks_one(self):
        sessions = [make_activity("A", "09:00", "11:00"),
                    make_activity("B", "10:00", "12:00"),
                    make_activity("C", "10:30", "11:30")]
        selected, rejected = activity_selection(sessions)
        self.assertEqual(len(selected), 1)
        self.assertEqual(len(rejected), 2)

    def test_back_to_back_is_allowed(self):
        sessions = [make_activity("A", "09:00", "10:00"),
                    make_activity("B", "10:00", "11:00"),
                    make_activity("C", "11:00", "12:00")]
        selected, _ = activity_selection(sessions)
        self.assertEqual(self.names(selected), ["A", "B", "C"])

    def test_selected_never_overlap(self):
        generator = random.Random(1)
        for _ in range(100):
            sessions = []
            for i in range(generator.randint(0, 10)):
                start = generator.randint(0, 100)
                sessions.append({"name": str(i), "start": start,
                                 "finish": start + generator.randint(1, 30)})
            selected, rejected = activity_selection(sessions)
            self.assertEqual(len(selected) + len(rejected), len(sessions))
            for first, second in zip(selected, selected[1:]):
                self.assertLessEqual(first["finish"], second["start"])

    def test_result_is_maximum(self):
        generator = random.Random(2)
        for _ in range(100):
            sessions = []
            for i in range(generator.randint(0, 8)):
                start = generator.randint(0, 20)
                sessions.append({"name": str(i), "start": start,
                                 "finish": start + generator.randint(1, 6)})
            best = 0
            for size in range(len(sessions) + 1):
                for combo in itertools.combinations(sessions, size):
                    ordered = sorted(combo, key=lambda a: a["start"])
                    if all(a["finish"] <= b["start"] for a, b in zip(ordered, ordered[1:])):
                        best = max(best, size)
            self.assertEqual(len(activity_selection(sessions)[0]), best)

    def test_reasons_are_given(self):
        selected, rejected = activity_selection(
            [make_activity("A", "09:00", "10:00"), make_activity("B", "09:30", "10:30")])
        self.assertIn("reason", selected[0])
        self.assertIn("overlap", rejected[0]["reason"])

    def test_invalid_times_rejected(self):
        with self.assertRaises(ValueError):
            activity_selection([make_activity("Bad", "10:00", "09:00")])
        with self.assertRaises(ValueError):
            activity_selection([make_activity("Zero", "10:00", "10:00")])

    def test_input_not_changed(self):
        sessions = [make_activity("A", "09:00", "10:00")]
        activity_selection(sessions)
        self.assertNotIn("reason", sessions[0])


# ======================================================================
# Fractional Knapsack (6)
# ======================================================================
class TestFractionalKnapsack(unittest.TestCase):
    ITEMS = [
        {"name": "Arrays",   "value": 5, "weight": 30},
        {"name": "Trees",    "value": 5, "weight": 60},
        {"name": "SQL",      "value": 3, "weight": 45},
        {"name": "Graphs",   "value": 5, "weight": 20},
        {"name": "Networks", "value": 1, "weight": 40},
    ]

    def test_example(self):
        result = fractional_knapsack(self.ITEMS, 100)
        names = [i["name"] for i in result["selected"]]
        self.assertEqual(names, ["Graphs", "Arrays", "Trees"])
        self.assertAlmostEqual(result["selected"][2]["fraction"], 50 / 60)
        self.assertAlmostEqual(result["total_value"], 5 + 5 + 5 * 50 / 60)
        self.assertEqual(result["total_weight"], 100)
        self.assertEqual(result["remaining"], 0)
        self.assertEqual(sorted(i["name"] for i in result["rejected"]), ["Networks", "SQL"])

    def test_empty_items(self):
        result = fractional_knapsack([], 50)
        self.assertEqual(result["total_value"], 0)
        self.assertEqual(result["remaining"], 50)

    def test_zero_capacity(self):
        result = fractional_knapsack(self.ITEMS, 0)
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["total_value"], 0)

    def test_capacity_larger_than_everything(self):
        result = fractional_knapsack(self.ITEMS, 1000)
        self.assertEqual(len(result["selected"]), 5)
        self.assertTrue(all(i["fraction"] == 1.0 for i in result["selected"]))
        self.assertEqual(result["remaining"], 1000 - 195)

    def test_single_item_partial(self):
        result = fractional_knapsack([{"name": "A", "value": 10, "weight": 20}], 5)
        self.assertAlmostEqual(result["selected"][0]["fraction"], 0.25)
        self.assertAlmostEqual(result["total_value"], 2.5)

    def test_never_exceeds_capacity_and_matches_answer_key(self):
        generator = random.Random(3)
        for _ in range(200):
            items = [{"name": str(i), "value": generator.randint(0, 9),
                      "weight": generator.randint(1, 20)}
                     for i in range(generator.randint(0, 7))]
            capacity = generator.randint(0, 60)
            result = fractional_knapsack(items, capacity)
            self.assertLessEqual(result["total_weight"], capacity)
            # answer key using Python's own sort
            ranked = sorted(items, key=lambda x: -x["value"] / x["weight"])
            left, expected = capacity, 0.0
            for item in ranked:
                take = min(left, item["weight"])
                expected += item["value"] * take / item["weight"]
                left -= take
            self.assertAlmostEqual(result["total_value"], expected)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            fractional_knapsack([{"name": "Bad", "value": 1, "weight": 0}], 10)
        with self.assertRaises(ValueError):
            fractional_knapsack([{"name": "Bad", "value": -1, "weight": 5}], 10)
        with self.assertRaises(ValueError):
            fractional_knapsack(self.ITEMS, -1)

    def test_input_not_changed(self):
        items = [{"name": "A", "value": 5, "weight": 10}]
        fractional_knapsack(items, 5)
        self.assertNotIn("ratio", items[0])


# ======================================================================
# 0/1 Knapsack (7)
# ======================================================================
class TestZeroOneKnapsack(unittest.TestCase):
    def test_small_example(self):
        items = [
            {"name": "Arrays", "value": 3, "weight": 2},
            {"name": "Trees",  "value": 4, "weight": 3},
            {"name": "SQL",    "value": 5, "weight": 4},
            {"name": "Graphs", "value": 6, "weight": 5},
        ]
        result = zero_one_knapsack(items, 5)
        self.assertEqual(result["total_value"], 7)
        self.assertEqual([i["name"] for i in result["selected"]], ["Arrays", "Trees"])
        self.assertEqual(result["total_weight"], 5)
        self.assertEqual(result["remaining"], 0)
        self.assertEqual(result["table"][4][5], 7)

    def test_realistic_example(self):
        items = [
            {"name": "Arrays",   "value": 5, "weight": 30},
            {"name": "Trees",    "value": 5, "weight": 60},
            {"name": "SQL",      "value": 3, "weight": 45},
            {"name": "Graphs",   "value": 5, "weight": 20},
            {"name": "Networks", "value": 1, "weight": 40},
        ]
        result = zero_one_knapsack(items, 100)
        self.assertEqual(result["total_value"], 13)
        self.assertEqual([i["name"] for i in result["selected"]], ["Arrays", "SQL", "Graphs"])
        self.assertEqual(result["total_weight"], 95)
        self.assertEqual(result["remaining"], 5)

    def test_better_than_greedy_by_value_density(self):
        # Taking the single best-ratio item (A) is worse than taking B + C.
        items = [{"name": "A", "value": 6, "weight": 5},
                 {"name": "B", "value": 4, "weight": 3},
                 {"name": "C", "value": 4, "weight": 3}]
        self.assertEqual(zero_one_knapsack(items, 6)["total_value"], 8)

    def test_empty_and_zero_capacity(self):
        self.assertEqual(zero_one_knapsack([], 50)["total_value"], 0)
        items = [{"name": "A", "value": 5, "weight": 10}]
        result = zero_one_knapsack(items, 0)
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["total_value"], 0)

    def test_single_item_fits_or_not(self):
        item = [{"name": "A", "value": 4, "weight": 10}]
        self.assertEqual(len(zero_one_knapsack(item, 10)["selected"]), 1)
        too_small = zero_one_knapsack(item, 9)
        self.assertEqual(too_small["selected"], [])
        self.assertIn("reason", too_small["rejected"][0])

    def test_everything_fits(self):
        items = [{"name": "A", "value": 1, "weight": 5}, {"name": "B", "value": 2, "weight": 5}]
        result = zero_one_knapsack(items, 100)
        self.assertEqual(len(result["selected"]), 2)
        self.assertEqual(result["total_value"], 3)

    def test_duplicate_items(self):
        items = [{"name": "X", "value": 5, "weight": 10}, {"name": "Y", "value": 5, "weight": 10}]
        result = zero_one_knapsack(items, 10)
        self.assertEqual(len(result["selected"]), 1)
        self.assertEqual(result["total_value"], 5)

    def test_matches_brute_force_and_respects_capacity(self):
        generator = random.Random(4)
        for _ in range(300):
            items = [{"name": str(i), "value": generator.randint(0, 9),
                      "weight": generator.randint(1, 12)}
                     for i in range(generator.randint(0, 8))]
            capacity = generator.randint(0, 40)
            result = zero_one_knapsack(items, capacity)
            best = 0
            for size in range(len(items) + 1):
                for combo in itertools.combinations(items, size):
                    if sum(x["weight"] for x in combo) <= capacity:
                        best = max(best, sum(x["value"] for x in combo))
            self.assertEqual(result["total_value"], best)
            self.assertEqual(sum(x["value"] for x in result["selected"]), best)
            self.assertLessEqual(result["total_weight"], capacity)
            self.assertEqual(len(result["selected"]) + len(result["rejected"]), len(items))

    def test_topics_to_items_uses_priority_values(self):
        items = topics_to_items(sample_topics())
        values = {i["name"]: i["value"] for i in items}
        self.assertEqual(values, {"Trees": 5, "arrays": 1, "SQL": 3, "Graphs": 5})
        self.assertEqual(items[0]["weight"], 60)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            zero_one_knapsack([{"name": "Bad", "value": 1, "weight": 0}], 10)
        with self.assertRaises(ValueError):
            zero_one_knapsack([{"name": "Bad", "value": 1, "weight": 2.5}], 10)
        with self.assertRaises(ValueError):
            zero_one_knapsack([], -5)


# ======================================================================
# Rod Cutting (8)
# ======================================================================
class TestRodCutting(unittest.TestCase):
    TEXTBOOK = {1: 1, 2: 5, 3: 8, 4: 9, 5: 10, 6: 17, 7: 17, 8: 20}

    def test_textbook_example(self):
        result = rod_cutting(8, self.TEXTBOOK)
        self.assertEqual(result["total_value"], 22)
        self.assertEqual(sorted(result["blocks"]), [2, 6])
        self.assertEqual(result["unused"], 0)
        self.assertEqual(result["best"], [0, 1, 5, 8, 10, 13, 17, 18, 22])

    def test_unused_time_when_blocks_do_not_fit(self):
        blocks = {25: 4, 45: 8, 60: 11, 90: 18}
        result = rod_cutting(40, blocks)
        self.assertEqual(result["blocks"], [25])
        self.assertEqual(result["unused"], 15)
        self.assertEqual(result["used"], 25)

    def test_study_example(self):
        result = rod_cutting(120, {25: 4, 45: 8, 60: 11, 90: 18})
        self.assertEqual(result["total_value"], 22)
        self.assertLessEqual(sum(result["blocks"]), 120)

    def test_zero_time_and_no_blocks(self):
        self.assertEqual(rod_cutting(0, self.TEXTBOOK)["total_value"], 0)
        result = rod_cutting(50, {})
        self.assertEqual(result["total_value"], 0)
        self.assertEqual(result["unused"], 50)

    def test_time_smaller_than_every_block(self):
        result = rod_cutting(10, {25: 4})
        self.assertEqual(result["blocks"], [])
        self.assertEqual(result["unused"], 10)

    def test_block_can_repeat(self):
        result = rod_cutting(30, {10: 3})
        self.assertEqual(result["blocks"], [10, 10, 10])
        self.assertEqual(result["counts"], {10: 3})

    def test_matches_answer_key(self):
        generator = random.Random(5)
        for _ in range(300):
            total = generator.randint(0, 40)
            blocks = {generator.randint(1, 15): generator.randint(0, 12)
                      for _ in range(generator.randint(0, 5))}
            best = [0] * (total + 1)
            for j in range(1, total + 1):
                best[j] = best[j - 1]
                for length, benefit in blocks.items():
                    if length <= j:
                        best[j] = max(best[j], best[j - length] + benefit)
            result = rod_cutting(total, blocks)
            self.assertEqual(result["total_value"], best[total])
            self.assertEqual(sum(blocks[b] for b in result["blocks"]), result["total_value"])
            self.assertEqual(sum(result["blocks"]) + result["unused"], total)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            rod_cutting(10, {0: 5})
        with self.assertRaises(ValueError):
            rod_cutting(10, {5: -1})
        with self.assertRaises(ValueError):
            rod_cutting(-1, {5: 1})


# ======================================================================
# Longest Common Subsequence (9)
# ======================================================================
class TestLCS(unittest.TestCase):
    def test_example(self):
        a = ["Introduction", "Arrays", "Linked Lists", "Trees", "Graphs"]
        b = ["Introduction", "Arrays", "Stacks", "Trees", "Graphs"]
        result = lcs(a, b)
        self.assertEqual(result["length"], 4)
        self.assertEqual(result["common"], ["Introduction", "Arrays", "Trees", "Graphs"])
        self.assertEqual(result["positions"], [(0, 0), (1, 1), (3, 3), (4, 4)])
        self.assertEqual(result["table"][5][5], 4)

    def test_empty_lists(self):
        self.assertEqual(lcs([], [])["common"], [])
        self.assertEqual(lcs(["A", "B"], [])["length"], 0)
        self.assertEqual(lcs([], ["A"])["length"], 0)

    def test_nothing_in_common(self):
        self.assertEqual(lcs(["A", "B"], ["C", "D"])["length"], 0)

    def test_identical_lists(self):
        self.assertEqual(lcs(["A", "B", "C"], ["A", "B", "C"])["common"], ["A", "B", "C"])

    def test_single_items(self):
        self.assertEqual(lcs(["Trees"], ["Trees"])["common"], ["Trees"])
        self.assertEqual(lcs(["Trees"], ["Graphs"])["common"], [])

    def test_reverse_order_only_one_matches(self):
        self.assertEqual(lcs(["A", "B", "C"], ["C", "B", "A"])["length"], 1)

    def test_ignores_case_and_spaces(self):
        result = lcs(["Arrays", "TREES "], [" arrays", "trees"])
        self.assertEqual(result["common"], ["Arrays", "TREES "])

    def test_duplicates(self):
        self.assertEqual(lcs(["A", "A", "B"], ["A", "B", "A"])["length"], 2)

    def test_random_lists_match_answer_key(self):
        def is_subsequence(small, big):
            iterator = iter(big)
            return all(item in iterator for item in small)

        def reference_length(a, b):
            grid = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
            for i in range(1, len(a) + 1):
                for j in range(1, len(b) + 1):
                    if a[i - 1] == b[j - 1]:
                        grid[i][j] = grid[i - 1][j - 1] + 1
                    else:
                        grid[i][j] = max(grid[i - 1][j], grid[i][j - 1])
            return grid[-1][-1]

        generator = random.Random(6)
        for _ in range(300):
            a = [generator.choice("abcd") for _ in range(generator.randint(0, 9))]
            b = [generator.choice("abcd") for _ in range(generator.randint(0, 9))]
            result = lcs(a, b)
            self.assertEqual(result["length"], reference_length(a, b))
            self.assertEqual(len(result["common"]), result["length"])
            self.assertTrue(is_subsequence(result["common"], a))
            self.assertTrue(is_subsequence(result["common"], b))


if __name__ == "__main__":
    unittest.main()