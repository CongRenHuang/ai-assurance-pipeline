# Baseline estimate for manual review time

`REVIEW_MINUTES_BASELINE_PER_ITEM = 2.4` in `assurance/metrics.py` is an
**ESTIMATE**, not a measurement. No timed pilot of manual review has been
run for this project.

## Where the number came from

2.4 minutes/item is a placeholder chosen as a plausible order-of-magnitude
figure for a reviewer skimming a short assessment (source check + numeric
sanity check + release/no-release call), not a value derived from
observing real reviewers.

## Scope

The estimate only covers the specific checks this pipeline's evaluators
perform: citation coverage, content integrity, source freshness, numeric
claim consistency. It does not cover broader editorial review, legal
review, or domain-expert sign-off that a real release process might also
require.

## Sensitivity range

Given the placeholder nature of the baseline, treat any "time saved" claim
as accurate to within roughly ±50% (i.e. the true baseline could plausibly
be anywhere from ~1.2 to ~3.6 min/item). The pipeline's structural
claim -- that AUTO/SAMPLE items skip a human touch entirely while
HUMAN_REVIEW/BLOCK items still get one -- does not depend on this number
and holds regardless of what the true per-item minutes turn out to be.

## Before citing a "time saved" number publicly

Run a real timed pilot: have a reviewer independently assess a sample of
queue items end-to-end, record the minutes, and replace the constant here
with the measured value.
