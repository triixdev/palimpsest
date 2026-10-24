import unittest

from palimpsest.gate import Passage, gate, judge_pair
from palimpsest.retrieve import load, top_k


def rev(**by_text):
    """Fake: probability of 'revises' picked by a marker found in the passage text."""
    def ask(state, questions, calls=by_text.get("calls")):
        if calls is not None:
            calls.append(1)
        for marker, p in by_text.items():
            if marker != "calls" and marker.replace("_", " ") in state:
                return {"revises": {"noul": p}}, 50.0
        return {"revises": {"noul": 0.1}}, 50.0
    return ask


P = {p.pid: p for p in load("corpus")}


class Gate(unittest.TestCase):
    def test_explicit_reference_skips_model(self):
        def boom(*x):
            raise AssertionError("model must not be called")
        v = judge_pair("", P["leave_2022"], P["leave_2025"], ask=boom)
        self.assertEqual((v.via, v.keep, v.dropped), ("code", ["leave_2025"], ["leave_2022"]))

    def test_older_passage_naming_newer_one_is_conflict(self):
        old = Passage.parse("x", "Ref: X-1\nAttendance Policy. Issued 2020-01-01. This policy supersedes X-2.\nLeave is 5 days.")
        new = Passage.parse("y", "Ref: X-2\nAttendance Policy. Issued 2025-01-01.\nLeave is 9 days.")
        v = judge_pair("", old, new, ask=rev())
        self.assertEqual(v.status, "conflict")

    def test_same_document_later_date_wins(self):
        v = judge_pair("", P["refund_2023"], P["refund_2026"], ask=rev())
        self.assertEqual((v.keep, v.dropped), (["refund_2026"], ["refund_2023"]))

    def test_untitled_passages_with_dates_are_conflict(self):
        a = Passage.parse("a", "Issued 2025-01-01. Parking costs 200 rupees.")
        b = Passage.parse("b", "Issued 2021-01-01. Parking costs 100 rupees.")
        self.assertEqual(judge_pair("", a, b, ask=rev()).status, "conflict")

    def test_different_documents_without_wording_is_conflict(self):
        v = judge_pair("", P["library_2024"], P["refund_2026"], ask=rev())
        self.assertEqual(v.status, "conflict")

    def test_older_passage_claiming_to_revise_is_conflict(self):
        v = judge_pair("", P["refund_2023"], P["refund_2026"], ask=rev(**{"30_days": 0.9}))
        self.assertEqual(v.reason, "the older passage claims to revise the newer one")

    def test_amendment_keeps_base_and_marks_roles(self):
        v = judge_pair("", P["library_2024"], P["library_2026"], ask=rev(**{"5_rupees": 0.8}))
        self.assertEqual((v.base, v.amends, len(v.keep)), ("library_2024", "library_2026", 2))

    def test_newer_revision_without_keep_wording_drops_older(self):
        v = judge_pair("", P["refund_2023"], P["refund_2026"], ask=rev(**{"14_days": 0.8}))
        self.assertEqual(v.dropped, ["refund_2023"])

    def test_no_dates_no_wording_is_conflict(self):
        v = judge_pair("", P["hostel_a"], P["hostel_b"], ask=rev())
        self.assertEqual(v.status, "conflict")

    def test_no_dates_but_clear_wording_decides(self):
        v = judge_pair("", P["hostel_a"], P["hostel_b"], ask=rev(**{"10_pm": 0.8}))
        self.assertEqual(v.keep, ["hostel_b"])

    def test_each_passage_is_asked_once(self):
        calls, cache = [], {}
        for _ in range(3):
            gate("", [P["refund_2023"], P["refund_2026"]], ask=rev(calls=calls), cache=cache)
        self.assertEqual(len(calls), 2)

    def test_retriever_ignores_weak_matches(self):
        got = [p.pid for p in top_k("casual leave days", list(P.values()))]
        self.assertEqual(sorted(got), ["leave_2022", "leave_2025"])


if __name__ == "__main__":
    unittest.main()
