# Post-Milestone Confirmation Plan

Fixed on November 23, 2026, before any Confirm dialogue was run through a model.

## Questions

1. **Action-hint parity.** Does LADL still beat the baselines when every memory condition can express the same action guidance?
2. **Approval extraction.** Does a clearer definition of an explicit approval improve LADL?
3. **New language.** Do the main results hold on actions, templates, probes, and filler that were not used in the original benchmark?

## Data

- **Confirm set:** 52 new timelines, 4 for each of the 13 primary families, rendered into 208 dialogues with seed 20261123.
- **New surface text:** a separate action library, event templates, acknowledgements, probes, teammate names, tool errors, and filler.
- **No paraphrases.** Gold labels come from the same deterministic rules as the rest of the benchmark.
- **Settings:** B=384, hard memory cap, compaction spread over each dialogue.
- **Authorship limit:** the new surface text was written by Claude, so it tests new wording but is not human-written language.

## Conditions

The hint-parity baselines use the status vocabulary rendered by LADL:

- `summary_hint`: the summarizer records each instruction's status and permitted action.
- `pinning_hint`: pinned rules record each instruction's status and permitted action.
- `chrono_hint`: each extracted event carries the action implication of that event alone, without a reducer.
- `typed_llm`: this baseline already renders action hints.

Extraction prompt v2 is developed on the dev split only and frozen before the Confirm run. Conditions that use extraction are run once with v1 and once with v2.

## Tests

All tests use paired timeline-cluster bootstrap with 2,000 resamples. The primary metric is four-way decision accuracy. Execute versus do-not-execute accuracy is a sensitivity analysis.

**Primary family, Holm-corrected over 8 tests:** for each model, LADL v1 minus `summary_hint`, `pinning_hint`, `chrono_hint`, and `typed_llm`.

**Secondary family, Holm-corrected over 12 tests:** for each model, LADL v1 minus ordinary compaction, pinning, the chronological ledger, and LADL without hints; LADL v2 minus LADL v1; and strict hedging minus LADL v1.

An effect is confirmed only if the difference is positive and its corrected p-value is below 0.05. The one exception is LADL minus LADL without hints, where a positive difference means action hints help.

## Stopping rule

The Confirm set is run once for extraction v1 and once for v2. Negative and null results are reported. Any prompt or method change made after seeing Confirm results is post hoc and cannot be reported as confirmed on this set.
