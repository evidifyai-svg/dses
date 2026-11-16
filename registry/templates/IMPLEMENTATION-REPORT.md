# Implementation report: [implementation name]

- Kind: implementation report
- Organization:
- Accountable technical lead:
- Date:
- DSES version and archive SHA-256:
- Capture level and integrity class:
- Registry entry: `implementations/<slug>/entry.json`

This report describes one implementation of the DSES specification. It is not
a conformance statement unless a conformance transcript is listed for it, and
it makes no claim about clinical performance, fault, or legal position.

## 1. Workflow and evidence question

What decision the workflow supports, who the actor is, and what question the
records are meant to answer.

## 2. Architecture

Components, where the emitter runs, and where records are stored. Say what was
written by your team, what was reused from the reference implementation, and
how AI tools were used in writing it.

## 3. Event boundaries

For each event you emit: the moment in your workflow that triggers it and the
component that emits it. Say plainly where a boundary named in the
specification does not exist as a distinct moment in your workflow.

## 4. Capture level and integrity class

What you claim, and what you do not. If output can reach the actor by a path
your emitter does not observe, say so here.

## 5. Interoperability mappings

Mappings to anything else you use (FHIR Provenance, DICOM, audit logs, study
exports), and where a mapping lost information.

## 6. Workflow burden

Added clicks, time, or steps for the actor, and how you measured them.

## 7. Privacy controls

How `case_ref` and `actor_ref` are derived, who can resolve them, and what the
public evidence package contains.

## 8. Verification

The command you ran, the result, and where the transcript is. Report failures.
A documented failure is a result.

## 9. Specification ambiguities

Every place you had to guess. For each: the section, what was unclear, what you
chose, and what you would change in the text. This section is the most useful
part of the report to other implementers.

## 10. Limitations

What this implementation and this report do not establish.
