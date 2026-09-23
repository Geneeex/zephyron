### Candidate detectors and training objective

The proposed model comparison makes the external-host inference task explicit. MobileNetV3-Small with an SSDLite head is the compact candidate; MobileNetV3-Large with the same head tests the cost of additional feature capacity. Both combinations have primary-paper precedents [@ENG_MOBILENETV3]. YOLOv4-tiny remains a third comparator [@ENG_SCALED]. None is claimed to be installed, trained or measured on Zephyron. Their role is to locate a useful accuracy, latency and energy tradeoff on the selected host, rather than infer suitability from a model name.

The selected comparison input is one RGB frame resampled to 320 by 320 pixels. This resolution is a proposed common starting point, not a recovered prototype setting. Preprocessing will record color order, intensity normalization, aspect-ratio handling and the inverse box transform. Outputs are class identifiers, scores and bounding boxes in the original image coordinates, with the capture identifier attached. An initial label guide will distinguish visible persons, designated retrieval objects and obstacle categories that annotators can define consistently. A two-dimensional box alone will not supply object distance or traversability.

[TABLE:Proposed model comparisons and required evidence]

| Candidate | Input and output | Comparison purpose | Required evidence |
|---|---|---|---|
| MobileNetV3-Small + SSDLite | RGB; boxes and class scores | Compact host detector | Held-out AP, event recall and latency |
| MobileNetV3-Large + SSDLite | Same image task | Additional feature capacity | Matched preprocessing and runtime |
| YOLOv4-tiny | Same image task | Different detector family | Same test encounters and host |
| Calibration curve / random forest | Voltage and measured temperature; conductivity | Simple versus nonlinear calibration | Independent reference samples and batch-held-out error |

For the SSD-family candidates, the declared reference objective combines class cross-entropy and smooth-L1 localization error over encoded anchor offsets [@ENG_SSD]:

$$
L_{\mathrm{det}}=\frac{L_{\mathrm{cls}}+\alpha L_{\mathrm{loc}}}{N_+},\qquad N_+>0.
$$

Here the losses, positive-anchor count \(N_+\) and weight \(\alpha\) are dimensionless. Anchor matching, negative mining and loss normalization will be retained from the pinned implementation. The original SSD convention assigns zero loss when no anchor is matched; the selected implementation's handling of negative-only images will therefore be checked explicitly. Background-only scenes remain essential in evaluation. A proposed initial training search uses pretrained weights with a replaced class head, SGD with momentum 0.9, learning rates 0.001 and 0.0003, and three recorded random seeds. These are search settings, not optimized values. Epoch limits, augmentation and early stopping will be fixed before test access; model selection will use validation encounters.

### Leakage control and calibrated interpretation

The dataset protocol below remains authoritative. Its dependency groups will be assigned to training, validation, calibration and test partitions before fitting. The supplied hash-based splitter uses selected proportions 55/15/15/15 and a saved seed; it preserves assignments when additional groups are appended. It does not discover correlated observations or guarantee balanced classes. Site, run and repeated-object dependencies must be resolved first, and empty or poorly represented partitions require more acquisition or a narrower claim. A final site-held-out evaluation is preferable when independent sites permit it. Test groups will never enter augmentation, threshold selection, probability calibration or quantization calibration.

If class logits are available, a scalar temperature may be fitted on a separate calibration subset, following classification-calibration practice [@ENG_TEMPERATURECAL]:

$$
p_{ik}(T)=\frac{\exp(z_{ik}/T)}{\sum_j\exp(z_{ij}/T)},\qquad
T^*=\operatorname{argmin}_{T>0}\left[-\sum_i\log p_{i,y_i}(T)\right].
$$

Logits \(z\), temperature \(T\) and probabilities are dimensionless. For an anchor detector, the calibration record must define the anchor labels, background sampling and matching procedure; these cannot change after observing test reliability. This operation concerns class probabilities and does not calibrate localization correctness. Emitted-detection reliability, duplicate penalties and missed-object recall will consequently remain separate outcomes under the subsequent evaluation protocol. Calibration will be omitted if sufficient independent calibration groups or compatible logits are unavailable.

Sensor learning has a narrower justification. A candidate random-forest regressor may map the water channel's raw voltage in volts and independently measured sample temperature in degrees Celsius to reference electrical conductivity at 25 degrees Celsius, in microsiemens per centimetre. This requires a calibrated reference meter, a separate temperature measurement and controlled sample handling; these instruments are proposed experimental requirements. Labels must not be generated from the same vendor voltage equation being assessed [@ENG_TDS_CODE; @ENG_USGS_EC]. The forest prediction is

$$
\widehat{\kappa}_{25}(\mathbf{x})=\frac{1}{B}\sum_{b=1}^{B}h_b(\mathbf{x}).
$$

Each tree predicts conductivity in the same units; \(B\) is the tree count [@ENG_RANDOMFOREST]. A selected 200-tree candidate will use squared-error splits, bootstrap sampling and validation-selected depth and leaf size. It will be compared with a fitted low-order calibration curve using the same inputs. Grouping by physical sample batch and acquisition day prevents repeated aliquots from leaking across partitions. Report bias, MAE and RMSE in conductivity units and residuals against temperature and reference level. Tree-to-tree spread will not be presented as a calibrated uncertainty interval. Without reference labels, the forest will not be fitted; a single MQ-2 signal will not be assigned gas identities or safety categories by analogy, and water conductivity will not become a potability label.

### Executable checks and deployment acceptance

The archive contains standard-library Python implementations for deterministic splitting, finite-box IoU, class-aware one-to-one matching and conservative frame admission. These execute without ML frameworks. They test data handling with explicitly constructed fixtures; their outputs are not detector performance. The matching helper covers ordinary boxes at one threshold, while reported COCO AP still requires the official evaluator and its ignore/crowd rules [@ENG_COCO].

Let \(\widehat A\) be estimated image age in seconds and \(e\) a nonnegative clock-error bound in seconds. The proposed admission check is

$$
\mathrm{admit}=I_{\mathrm{identity}}I_{\mathrm{quality}}
\mathbf{1}[\widehat A-e\geq0]\mathbf{1}[\widehat A+e\leq A_{\max}].
$$

The identity flag includes session, sequence and displayed-image agreement. An unknown offset fails admission. A standard uncertainty must be converted to a justified bound before use; passing this gate does not establish collision avoidance. Listing 1 demonstrates the boundary with chosen timestamps.

[LISTING:Conservative frame-age admission using explicit clock bounds]

```python
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
```

Listing 2 makes the duplicate penalty executable. Both listings use the included `validation_primitives.py`; complete runnable files are supplied alongside it.

[LISTING:One reference object cannot produce two true positives]

```python
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
```

Model deployment requires an additional verification stage. Archive weights and hashes, framework/export versions, host specifications and preprocessing. Compare floating-point and INT8 exports on identical saved frames; inspect operator fallback and output agreement before timing. Quantization inputs must come from representative development groups [@ENG_QUANT; @ENG_ONNX]. Measure warm-up separately, then inference distributions, peak memory, full-pipeline age, dropped frames and host energy under matched recording/network conditions. A model will be selected from validation evidence subject to declared resource limits, then assessed once on the held-out test protocol. No trained weights, accuracy improvement or runtime advantage is asserted here.
