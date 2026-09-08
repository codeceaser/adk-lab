# Observations — thought_self_conditioning

**Scope of this document.** These are mechanical observations on the evidence
in `0bb1fc3`, written at the experiment owners' request. They are not the
adjudication. Nothing here says whether thought replay is good or bad, nothing
here recommends a production change, and no causal claim is made beyond the one
controlled variable (presence of readable `model_exposed_thought` text in the
continuation request). Where a number could be read as a finding, the limits
that weaken it are stated alongside it.

Two-arm evidence: `0bb1fc36787324ef9d0e0217524e9f9ee2094c2d`
Three-arm evidence: `5bbfd84b5248c892d1058fbf3379b509d49e487a`
Harness: `b1bc92a593647e68a047bf343ec557310eeeb707`, filler arm `17a35abe927be17ee985cc3ae421a21739600b60`

The equal-token filler arm named at the end of this document as a way to
sharpen the measurement has since been built and run; the three-arm section
below supersedes the two-arm reading of the prompt-length confound.

## What was held constant, and what was not

The arm diff proved identical: `function_call` id and args, `thought_signature`
bytes, `function_response` and id, system instruction, tool declarations, model,
backend, generation config. Across all 150 continuations in both runs the send
invariant held and the Gemini adapter changed no contents.

In the original two-arm design one difference could not be removed: the replay
arm's prompt is longer (primary 2889 vs 1666 tokens; secondary 1254 vs 990), so
any difference was attributable to "readable thought text present" as a package
— content *and* length together.

**ARM F removes that ambiguity.** It carries task-inert filler of the same token
length as the real thought text, so R vs F isolates content with length held
equal, and F vs S isolates length. The filler matched exactly at 613 tokens in
isolation for the primary specimen; measured in full request context the filler
arm came out at 2890 prompt tokens against replay's 2889 — a one-token residual,
recorded rather than smoothed over. The secondary matched exactly at 1254.

## Behavioral counts

**Primary — `COT-03-ON-01#2`** (ambiguous lookup, `status=not_found`), N=20/arm:

| | REPLAY | STRIP |
| --- | --- | --- |
| ASK_CLARIFICATION | 17/20 | 19/20 |
| DIRECT_ANSWER | 3/20 | 1/20 |

**Secondary — `COT-02-ON-01#2`** (successful explicit lookup), N=10/arm:

| | REPLAY | STRIP |
| --- | --- | --- |
| CALL_OTHER_TOOL | 10/10 | 4/10 |
| DIRECT_ANSWER | 0/10 | 6/10 |

Observation: the two specimens separate differently. The primary's arms differ
by 2 of 20 in the dominant category — a margin that N=20 cannot distinguish from
sampling noise. The secondary's arms differ by 6 of 10, with the replay arm
unanimous. No significance test is offered for either, and the secondary's N is
smaller, not larger, than the primary's.

Note also that the *dominant* behavior differs by specimen rather than by arm:
the primary asks for clarification in both arms, the secondary calls another
tool in the replay arm. Whatever is being measured is not uniform across the
two paths.

## Response-side measurements

| Specimen | Arm | thinking tokens (mean) | completion tokens (mean) | responses exposing thoughts | finish reason |
| --- | --- | --- | --- | --- | --- |
| primary | replay | 255.2 | 61.4 | 0/20 | STOP ×20 |
| primary | strip | 171.6 | 60.8 | 0/20 | STOP ×20 |
| secondary | replay | 160.3 | 22.0 | 0/10 | STOP ×10 |
| secondary | strip | 91.9 | 39.9 | 0/10 | STOP ×10 |

Three things worth recording:

1. **Thinking-token counts are higher in the replay arm in both specimens**
   (255 vs 172; 160 vs 92). This is a measured difference on the response side,
   under an input that differs only in the controlled variable. It is not
   evidence about reasoning quality, and the prompt-length confound above
   applies to it as much as to the behavioral counts.

2. **Completion length behaves differently across specimens.** Primary: near
   identical (61.4 vs 60.8). Secondary: replay is shorter (22.0 vs 39.9), which
   is consistent with the secondary replay arm emitting a tool call in 10/10
   runs while the strip arm emitted prose in 6/10. Length here largely tracks
   the category, not the arm.

3. **No continuation response exposed a thought summary, in any arm.** The
   reconstructed requests carry no `thinking_config`, so `include_thoughts` was
   unset for the continuation step. This is held constant across arms and does
   not affect the control, but it scopes the result: this measures the effect of
   *being conditioned on* replayed thought text, not the effect of also
   re-exposing new thought text on the next step.

## Limits on reading this evidence

- **N is small.** 20+20 and 10+10, one frozen specimen per path. No statistical
  significance claim is made or supported.
- **One specimen per path.** Results are specific to these two frozen states and
  may not generalize to other prompts, tools, or failure modes.
- **No seed.** Neither arm sets one, deliberately — sampling variation is what
  the repetitions measure. So each arm is a small sample from a distribution,
  not a fixed point.
- **The prompt-length confound** was not separable in the two-arm design. ARM F
  addresses it; see the three-arm section.
- **The `ASK_CLARIFICATION` / `DIRECT_ANSWER` boundary is a lexical rule**
  (presence of `?`), not a semantic judgement. It affects the primary's counts
  directly. Every raw response is preserved in the evidence, so re-classifying
  under a different rule requires no new model calls.
- **`thinking_budget` was never set**, here or in the source trajectories, so
  thinking depth is model-chosen per call.

## What would sharpen the measurement

Methodological only, offered as options rather than recommendations:

- ~~An equal-token filler arm~~ — built and run; see the three-arm section.
- More frozen specimens, especially other ambiguity and failure shapes.
- Larger N on the secondary specimen, where the observed separation is widest
  and the sample is smallest.
- A second classification rule applied to the preserved raw text, to test how
  much the primary's counts depend on the `?` boundary.

The adjudication remains with the experiment owners.


## Three-arm results

Run fresh so all three arms are compared within one session
(`5bbfd84`). The two-arm evidence in `0bb1fc3` is retained, not replaced.

**Primary — `COT-03-ON-01#2`**, N=20/arm:

| | REPLAY | FILLER | STRIP |
| --- | --- | --- | --- |
| ASK_CLARIFICATION | 18/20 | 17/20 | 17/20 |
| DIRECT_ANSWER | 1/20 | 3/20 | 2/20 |
| CALL_OTHER_TOOL | 1/20 | 0/20 | 1/20 |

**Secondary — `COT-02-ON-01#2`**, N=10/arm:

| | REPLAY | FILLER | STRIP |
| --- | --- | --- | --- |
| CALL_OTHER_TOOL | 10/10 | 8/10 | 3/10 |
| DIRECT_ANSWER | 0/10 | 2/10 | 7/10 |

Token measurements:

| Specimen | Arm | prompt | thinking (mean) | completion (mean) |
| --- | --- | --- | --- | --- |
| primary | replay | 2889 | 221.5 | 56.2 |
| primary | filler | 2890 | 185.3 | 59.2 |
| primary | strip | 1666 | 193.9 | 52.0 |
| secondary | replay | 1254 | 139.5 | 22.0 |
| secondary | filler | 1254 | 137.8 | 27.6 |
| secondary | strip | 990 | 78.0 | 44.5 |

### Observations on the three arms

1. **On the secondary specimen, FILLER sits close to REPLAY and far from
   STRIP** (8/10 vs 10/10 vs 3/10 CALL_OTHER_TOOL). Under this design that
   pattern is what "length, not content" would look like, since F and R share
   length while F and R differ in content. It is one specimen at N=10 and the
   filler's distributional oddity (below) is not controlled, so it is a pattern
   to weigh, not a demonstration.

2. **On the primary specimen the three arms are within 1 of each other** in the
   dominant category (18/17/17 of 20). At this N the primary separates nothing,
   in either the original R-vs-S comparison or the new ones.

3. **The primary's earlier and later REPLAY-vs-STRIP readings disagree.** The
   two-arm run gave 17/20 vs 19/20; the three-arm run gave 18/20 vs 17/20 — the
   direction flips between sessions on identical frozen input. That is direct
   evidence that a 2-of-20 margin on this specimen is not distinguishable from
   sampling noise, and it is the strongest reason not to read the primary's
   counts as a result.

4. **Thinking tokens no longer separate cleanly by arm.** Primary: 221.5 replay
   / 185.3 filler / 193.9 strip — filler is *below* strip, so the two-arm
   observation that replay ran higher does not survive as a simple ordering.
   Secondary keeps a gap between the length-matched pair (139.5, 137.8) and
   strip (78.0), which under this design tracks length rather than content.

### Added limitation from the filler arm

The filler is length-matched and task-inert, but **not distributionally
neutral**: 613 tokens of a repeated word is not what a real model turn looks
like. R vs F therefore separates real thought content from prompt length; it
does not separate real thought content from *any coherent text* of that length.
A fluent-but-unrelated prose filler would be needed for that, and does not exist
in this expedition. Where the three-arm results point at length, that reading
carries this caveat.
