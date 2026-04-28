import { SkillSummary } from "../api/client";

type Props = {
  pendingSkill: string;
  skills: SkillSummary[];
  disabled: boolean;
  onConfirm: (yes: boolean) => void;
};

export function SkillConfirmBanner({ pendingSkill, skills, disabled, onConfirm }: Props) {
  const skill = skills.find((s) => s.id === pendingSkill);
  const name = skill?.name || pendingSkill;
  return (
    <div className="confirm-banner">
      <span className="label">
        Activate <strong>{name}</strong>? Reply yes to start, or pick a different focus.
      </span>
      <button className="primary" disabled={disabled} onClick={() => onConfirm(true)}>
        Yes, activate
      </button>
      <button disabled={disabled} onClick={() => onConfirm(false)}>
        No, change focus
      </button>
    </div>
  );
}
