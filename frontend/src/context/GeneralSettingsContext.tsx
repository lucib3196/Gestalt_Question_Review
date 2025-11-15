import React, { createContext, useState, useEffect } from "react";
import { getSettings } from "../api/settingsAPI";
import type { QuestionStorage } from "../types/settingsType";

type GeneralSettingsContextType = {
    questionStorage: QuestionStorage,
};

// Create context with default values
export const QuestionSettingsContext = createContext<GeneralSettingsContextType>({
    questionStorage: "local"

});

const QuestionSettingsProvider = ({ children }: { children: React.ReactNode }) => {
    const [questionStorage, setQuestionStorage] = useState<QuestionStorage>("local")

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const data = await getSettings();
                if (!data) {
                    throw "Error could not determine settings"
                }
                setQuestionStorage(data);
            } catch (err) {
                console.error("Failed to fetch settings", err);
            }
        };

        fetchSettings();
    }, []); // run once 
    return (
        <QuestionSettingsContext.Provider
            value={{
                questionStorage
            }}
        >
            {children}
        </QuestionSettingsContext.Provider>
    );
};

export default QuestionSettingsProvider;
