from validation_primitives import (
    BoxRecord, match_detections, rates)

# Constructed boxes, not outputs from a trained detector.
truth = [BoxRecord("target", (0, 0, 2, 2))]
predictions = [
    BoxRecord("target", (0, 0, 2, 2), 0.9),
    BoxRecord("target", (0, 0, 2, 2), 0.8)]
counts = match_detections(truth, predictions, 0.5, 0.5)
assert counts == {"tp": 1, "fp": 1, "fn": 0}
assert rates(counts)["precision"] == 0.5
empty = match_detections([], [])
assert empty == {"tp": 0, "fp": 0, "fn": 0}
assert rates(empty)["precision"] is None
print({"fixture_counts": counts})
