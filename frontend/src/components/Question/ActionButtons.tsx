
import type { FormEvent } from "react";
import { MyButton } from "../Base/Button";

type ButtonActionsProps = {
  isSubmitted: boolean;
  showSolution: () => void;
  handleSubmit: (e: FormEvent) => void;
  generateVarient: () => void;
};
export function ButtonActions({
  isSubmitted,
  showSolution,
  handleSubmit,
  generateVarient,
}: ButtonActionsProps) {
  return (
    <div className="grid sm:grid-cols-3 gap-10 mb-10">
      <MyButton
        name={"Generate Variation"}
        onClick={generateVarient}
        color="generateVariant"
      />
      <MyButton name={"Show Solution"} color="showSolution" onClick={showSolution} />
      <MyButton
        name={"Submit"}
        btype="submit"
        onClick={handleSubmit}
        disabled={isSubmitted}
        color="submitQuestion"
      />
    </div>
  );
}
