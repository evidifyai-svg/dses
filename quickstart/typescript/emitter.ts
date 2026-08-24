import { randomUUID } from "node:crypto";

type ExposureClass =
  | "PRIORITY" | "PRESENCE" | "CATEGORICAL" | "LOCALIZATION"
  | "QUANTITATIVE" | "NARRATIVE" | "DIRECTIVE" | "AGENTIC";

type PassivePresentation = {
  caseRef: string;
  actorRef: string;
  occurredAt: string;
  sequence: number;
  aiName: string;
  modelId: string;
  modelVersion: string;
  exposureClasses: ExposureClass[];
  modality: string;
};

/** Emit an I1 presentation record. This does not claim a pre-AI state or I2. */
export function passivePresentation(input: PassivePresentation) {
  return {
    event_id: `evt-${randomUUID()}`,
    event_type: "ai_result_presented",
    sequence: input.sequence,
    ordering: "determinate",
    occurred_at: input.occurredAt,
    recorded_at: input.occurredAt,
    case_ref: input.caseRef,
    actor: { actor_ref: input.actorRef, actor_type: "human" },
    ai_system: {
      name: input.aiName,
      model_id: input.modelId,
      model_version: input.modelVersion,
    },
    exposure: {
      classes: input.exposureClasses,
      modality: input.modality,
    },
    integrity: { class: "I1" },
    source_system: { system_type: "viewer" },
  } as const;
}

// For I2, use an RFC 8785 library and the verifier fixtures. JSON.stringify
// alone is not a canonicalization implementation.
