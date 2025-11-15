import {
    createContext,
    useContext,
    useState,
    useEffect,
    useCallback,
    type Dispatch,
    type ReactNode,
} from "react";

import { QuestionAPI } from "../api/questionAPI";
import type { QuestionMeta } from "../types/questionTypes";

type QuestionContextType = {
    selectedQuestionID: string | null;
    setSelectedQuestionID: React.Dispatch<React.SetStateAction<string>>;
    questionMeta: QuestionMeta | null;
    setQuestionMeta: React.Dispatch<React.SetStateAction<QuestionMeta | null>>;
    questions: QuestionMeta[];
    setQuestions: Dispatch<React.SetStateAction<QuestionMeta[]>>;
};

export const QuestionContext = createContext<QuestionContextType | null>(null);

export function QuestionProvider({ children }: { children: ReactNode }) {
    const [questions, setQuestions] = useState<QuestionMeta[]>([]);
    const [questionMeta, setQuestionMeta] = useState<QuestionMeta | null>(null);
    const [selectedQuestionID, setSelectedQuestionID] = useState<string>("");

    const fetchQuestionMeta = useCallback(async () => {
        if (!selectedQuestionID) return;
        try {
            const retrieved = await QuestionAPI.getQuestionMeta(selectedQuestionID);
            setQuestionMeta(retrieved);
        } catch (error) {
            console.error("❌ Failed to fetch question:", error);
        }
    }, [selectedQuestionID]);

    useEffect(() => {
        fetchQuestionMeta();
    }, [fetchQuestionMeta]);

    return (
        <QuestionContext.Provider
            value={{
                questions,
                setQuestions,
                selectedQuestionID,
                setSelectedQuestionID,
                questionMeta,
                setQuestionMeta,
            }}
        >
            {children}
        </QuestionContext.Provider>
    );
}

export function useQuestionContext() {
    const context = useContext(QuestionContext);

    if (!context) {
        throw new Error(
            "useQuestionContext must be used within a <QuestionProvider>"
        );
    }

    return context;
}
