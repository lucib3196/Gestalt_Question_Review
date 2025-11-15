import { useQuestionContext } from "../../context/QuestionContext";
import type { QuestionMeta } from "../../types/questionTypes";
import { InputTextForm } from "./InputComponents";
import { useState, type FormEvent } from "react";
import { MyButton } from "../Base/Button";
import { QuestionAPI } from "../../api/questionAPI";
import type { QuestionData } from "../../types/questionTypes";
import { toast } from "react-toastify";

function QuestionFormHeader({ questionMeta }: { questionMeta: QuestionMeta }) {
    return (
        <div>
            <h1 className="text-2xl py-2 font-bold text-center">
                Update Question: {questionMeta.title}
            </h1>
        </div>
    );
}
export default function QuestionUpdateForm() {
    const { questionMeta, selectedQuestionID } = useQuestionContext();

    const [title, setTitle] = useState<string>(questionMeta?.title ?? "");
    const [topics, setTopics] = useState<string>(
        (questionMeta?.topics ?? []).map((t) => t.name || t).join(", ")
    );
    const [qtypes, setQtypes] = useState<string>(
        (questionMeta?.qtypes ?? []).map((t) => t.name || t).join(", ")
    );
    const [language, setLanguage] = useState<string>(
        (questionMeta?.languages ?? []).map((t) => t.name || t).join(", ")
    );
    const [isAdaptive, setIsAdaptive] = useState<boolean>(
        questionMeta?.isAdaptive ?? false
    );
    const [aiGenerated, setAIGenerated] = useState<boolean>(
        questionMeta?.ai_generated ?? false
    );



    if (!questionMeta) return null;

    function buildQuestionData(): QuestionData {
        const splitValues = (val: string): string[] =>
            val
                .split(",")
                .map((s) => s.trim())
                .filter((s) => s.length > 0);

        return {
            title,
            ai_generated: aiGenerated,
            topics: splitValues(topics),
            languages: splitValues(language),
            qtypes: splitValues(qtypes),
        };
    }

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault()
        const questionData = buildQuestionData();
        try {
            await QuestionAPI.updateQuestion(selectedQuestionID ?? "", questionData);
        } catch (error) {
            console.log("Error");
            toast.error("Could not update question data");
        } finally {
            toast.success("Updated Question Data Success");
        }
    };

    return (
        <div className="gap-y-2 py-5">
            <QuestionFormHeader questionMeta={questionMeta} />

            <form
                onSubmit={handleSubmit}
                className="space-y-4 flex flex-col items-center"
            >
                {/* Title */}
                <InputTextForm
                    id="titleUpdate"
                    value={title}
                    type="text"
                    name="QuestionTitle"
                    label="Question Title"
                    onChange={(e) => setTitle(e.target.value)}
                />

                {/* Topics */}
                <InputTextForm
                    id="topicsUpdate"
                    value={topics}
                    type="text"
                    name="QuestionTopics"
                    label="Topics (comma separated)"
                    onChange={(e) => setTopics(e.target.value)}
                />

                {/* Question Types */}
                <InputTextForm
                    id="qtypesUpdate"
                    value={qtypes}
                    type="text"
                    name="QuestionTypes"
                    label="Question Types (comma separated)"
                    onChange={(e) => setQtypes(e.target.value)}
                />

                {/* Languages */}
                <InputTextForm
                    id="languageUpdate"
                    value={language}
                    type="text"
                    name="QuestionLanguage"
                    label="Languages (comma separated)"
                    onChange={(e) => setLanguage(e.target.value)}
                />

                {/* Adaptive & AI generated checkboxes (optional) */}
                <div className="flex flex-col gap-2">
                    <label>
                        <input
                            type="checkbox"
                            checked={isAdaptive}
                            onChange={(e) => setIsAdaptive(e.target.checked)}
                        />{" "}
                        Adaptive
                    </label>

                    <label>
                        <input
                            type="checkbox"
                            checked={aiGenerated}
                            onChange={(e) => setAIGenerated(e.target.checked)}
                        />{" "}
                        AI Generated
                    </label>
                </div>

                <MyButton name="Submit" type="submit" />
            </form>
        </div>
    );
}
