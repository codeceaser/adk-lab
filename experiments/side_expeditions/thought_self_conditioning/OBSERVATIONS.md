# Observations — thought_self_conditioning

**Scope of this document.** These are mechanical observations on the evidence
in `0bb1fc3`, written at the experiment owners' request. They are not the
adjudication. Nothing here says whether thought replay is good or bad, nothing
here recommends a production change, and no causal claim is made beyond the one
controlled variable (presence of readable `model_exposed_thought` text in the
continuation request). Where a number could be read as a finding, the limits
that weaken it are stated alongside it.

Evidence: `0bb1fc36787324ef9d0e0217524e9f9ee2094c2d`
Harness: `b1bc92a593647e68a047bf343ec557310eeeb707`

## What was held constant, and what was not

The arm diff proved identical: `function_call` id and args, `thought_signature`
bytes, `function_response` and id, system instruction, tool declarations, model,
backend, generation config. Across all 60 continuations the send invariant held
and the Gemini adapter changed no contents.

One difference is **inherent to the variable and cannot be removed**: the replay
arm's prompt is longer (primary 2889 vs 1666 tokens; secondary 1254 vs 990).
Any observed difference is therefore attributable to "readable thought text
present" as a package — its content *and* its length — not to content alone.
Separating those two would need a different control (for example, replacing the
thought text with filler of equal token length), which this experiment does not
have.

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
- **The prompt-length confound** described above is not separable in this design.
- **The `ASK_CLARIFICATION` / `DIRECT_ANSWER` boundary is a lexical rule**
  (presence of `?`), not a semantic judgement. It affects the primary's counts
  directly. Every raw response is preserved in the evidence, so re-classifying
  under a different rule requires no new model calls.
- **`thinking_budget` was never set**, here or in the source trajectories, so
  thinking depth is model-chosen per call.

## What would sharpen the measurement

Methodological only, offered as options rather than recommendations:

- An equal-token filler arm, to separate thought *content* from prompt *length*.
- More frozen specimens, especially other ambiguity and failure shapes.
- Larger N on the secondary specimen, where the observed separation is widest
  and the sample is smallest.
- A second classification rule applied to the preserved raw text, to test how
  much the primary's counts depend on the `?` boundary.

The adjudication remains with the experiment owners.
