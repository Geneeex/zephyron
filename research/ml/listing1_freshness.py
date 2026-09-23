from validation_primitives import admit_frame

# Constructed fixture: all time quantities are seconds.
accepted = admit_frame(
    capture_s=10.0, now_s=10.5, offset_s=0.25,
    error_s=0.0625, limit_s=0.3125,
    identity_ok=True, quality_ok=True)
assert accepted  # Age interval: [0.1875, 0.3125] s.
assert not admit_frame(
    10.0, 10.5, 0.25, 0.0625, 0.30, True, True)
assert not admit_frame(
    10.0, 10.5, None, 0.0625, 0.3125, True, True)
assert not admit_frame(
    10.0, 10.5, 0.25, 0.0625, 0.3125, False, True)
print({"fixture_accepted": accepted})
