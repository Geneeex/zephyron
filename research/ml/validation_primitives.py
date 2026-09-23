"""Deterministic validation primitives; no ML weights or measured rover data.

Boxes are xyxy continuous coordinates, not inclusive integer pixel indices.
Matching is for one ordinary image with no crowd/ignore annotations. It is not
COCO AP. A production evaluator must use the pinned official COCO implementation.
"""
from dataclasses import dataclass
import hashlib
import json
import math


@dataclass(frozen=True)
class BoxRecord:
    label: str
    box: tuple
    score: float = 1.0


def _checked_box(box):
    if len(box) != 4 or not all(math.isfinite(x) for x in box):
        raise ValueError("Box needs four finite xyxy coordinates")
    x1, y1, x2, y2 = box
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Box must have strictly positive area")
    return tuple(box)


def iou(a, b):
    a, b = _checked_box(a), _checked_box(b)
    w = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = w * h
    union = ((a[2]-a[0]) * (a[3]-a[1])
             + (b[2]-b[0]) * (b[3]-b[1]) - intersection)
    return intersection / union


def admit_frame(capture_s, now_s, offset_s, error_s,
                limit_s, identity_ok, quality_ok):
    """Accept only if the entire bounded age interval is in [0, limit].

    offset_s is host minus rover clock offset; error_s is a nonnegative
    bound, not an unconverted standard uncertainty. None means unknown.
    Identity must cover boot/session, sequence and displayed-image match.
    """
    values = (capture_s, now_s, offset_s, error_s, limit_s)
    if any(v is None or not math.isfinite(v) for v in values):
        return False
    if error_s < 0 or limit_s < 0:
        return False
    age = now_s - capture_s - offset_s
    return bool(identity_ok and quality_ok
                and 0 <= age - error_s
                and age + error_s <= limit_s)


def match_detections(reference, predictions, iou_threshold=0.5,
                     score_threshold=0.0):
    """Score-descending one-to-one matching; ties retain input order."""
    if not 0 < iou_threshold <= 1 or not 0 <= score_threshold <= 1:
        raise ValueError("Invalid matching threshold")
    for record in list(reference) + list(predictions):
        _checked_box(record.box)
        if not isinstance(record.label, str) or not record.label:
            raise ValueError("Class label must be a nonempty string")
        if not math.isfinite(record.score) or not 0 <= record.score <= 1:
            raise ValueError("Scores must be finite and in [0, 1]")
    kept = sorted((p for p in predictions if p.score >= score_threshold),
                  key=lambda p: -p.score)
    unmatched = set(range(len(reference)))
    tp = 0
    for p in kept:
        candidates = [(iou(p.box, reference[j].box), j)
                      for j in sorted(unmatched)
                      if reference[j].label == p.label]
        if candidates:
            overlap, j = max(candidates, key=lambda pair: pair[0])
            if overlap >= iou_threshold:
                tp += 1
                unmatched.remove(j)
    return {"tp": tp, "fp": len(kept)-tp, "fn": len(unmatched)}


def rates(counts):
    tp, fp, fn = (counts[k] for k in ("tp", "fp", "fn"))
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 0
           for v in (tp, fp, fn)):
        raise ValueError("Counts must be nonnegative integers")
    return {"precision": tp/(tp+fp) if tp+fp else None,
            "recall": tp/(tp+fn) if tp+fn else None,
            "f1": 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None}


def group_partition(group_id, seed="zephyron-v1"):
    """Deterministic 55/15/15/15 group assignment, not stratification.

    The caller defines dependency groups before this function is applied.
    Groups must unite related sites/runs/object identities as appropriate.
    Adding groups cannot move existing assignments. Empty or imbalanced
    partitions remain possible and must be reported, not silently reshuffled.
    """
    if not isinstance(group_id, str) or not group_id.strip():
        raise ValueError("A nonempty group identifier is required")
    payload = json.dumps([seed, group_id], ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    bucket = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    scale = 1 << 64
    for name, percent in (("train", 55), ("validation", 70),
                          ("calibration", 85), ("test", 100)):
        if bucket * 100 < percent * scale:
            return name
    raise AssertionError("Unreachable")


def split_manifest(records, seed="zephyron-v1"):
    """Return frame ID -> partition; reject duplicated identifiers."""
    result = {}
    for record in records:
        frame_id = record["frame_id"]
        if not isinstance(frame_id, str) or not frame_id:
            raise ValueError("Frame identifier must be a nonempty string")
        if frame_id in result:
            raise ValueError("Repeated frame identifier")
        result[frame_id] = group_partition(record["group_id"], seed)
    return result
