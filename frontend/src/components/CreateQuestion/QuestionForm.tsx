import React, { useState } from "react";
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import UploadFilesButton from "../Forms/UploadFileComponent";
import { MyButton } from "../Base/Button";
import type { QuestionData } from "../../types/questionTypes";
import { QuestionAPI } from "../../api/questionAPI";

function handleLanguages(languages: string[]) {
    return [
        ...new Set(
            languages.flatMap((val) =>
                val == "both" ? ["javascript", "python"] : val
            )
        ),
    ];
}

function handleTopics(topics: string[] | string) {
    const isArray = Array.isArray(topics);
    if (isArray) {
        return topics;
    } else {
        const topicArray = topics
            .split(",")
            .map((val) => val.trim())
            .filter(Boolean);
        return topicArray;
    }
}

function handleQtypes(qtypes: string[] | string) {
    return Array.isArray(qtypes)
        ? qtypes
        : qtypes
            .split(",")
            .map((val) => val.trim())
            .filter(Boolean);
}

type FormProps = {
    onFinish: () => void
}
function QuestionCreationForm({ onFinish }: FormProps) {
    const [files, setFiles] = useState<File[]>([]);
    const [alignment, setAlignment] = useState("files");
    const [formData, setFormData] = useState<QuestionData>({
        title: "",
        isAdaptive: false,
        ai_generated: false,
        topics: [],
        languages: [],
        qtypes: [],
    });

    const handleFormChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;

        // handle multi-select for languages
        if (e.target instanceof HTMLSelectElement && e.target.multiple) {
            const selected = Array.from(e.target.selectedOptions, (opt) => opt.value);
            setFormData((prev) => ({ ...prev, [name]: selected }));
        } else {
            setFormData((prev) => ({ ...prev, [name]: value }));
        }
    };

    const handleToggleChange = (
        _: React.MouseEvent<HTMLElement>,
        newAlignment: string | null
    ) => {
        if (newAlignment !== null) {
            setAlignment(newAlignment);
            if (newAlignment !== "files") setFiles([]);
        }
    };

    const handleForm = async (e: React.FormEvent) => {
        e.preventDefault();

        // convert topics string into array (split by comma)
        const languageArray = handleLanguages(formData.languages ?? []);
        const topicArray = handleTopics(formData.topics ?? []);
        const qTypeArray = handleQtypes(formData.qtypes ?? []);

        const submission = {
            ...formData,
            languages: languageArray,
            topics: topicArray,
            qtype: qTypeArray,
            files,
        };
        console.log("Submitting form:", submission);
        try {
            const result = await QuestionAPI.create(submission);
            onFinish()
            console.log(result)

        } catch (error) {
            console.log(error)
        }

    };

    return (
        <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md">
            <form className="space-y-6" onSubmit={handleForm}>
                {/* Question Title */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Question Title
                    </label>
                    <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleFormChange}
                        required
                        placeholder="Enter question title"
                        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    />
                </div>

                {/* Created By */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Created By
                    </label>

                </div>

                {/* Flags */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Is Adaptive
                        </label>
                        <select
                            name="isAdaptive"
                            value={formData.isAdaptive ? "true" : "false"}
                            onChange={handleFormChange}
                            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                        >
                            <option value="true">True (contains JS/Python code)</option>
                            <option value="false">False</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Is AI Generated
                        </label>
                        <select
                            name="ai_generated"
                            value={formData.ai_generated ? "true" : "false"}
                            onChange={handleFormChange}
                            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                        >
                            <option value="true">True</option>
                            <option value="false">False</option>
                        </select>
                    </div>
                </div>

                {/* Topics */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Topics (comma separated)
                    </label>
                    <input
                        type="text"
                        name="topics"
                        value={formData.topics}
                        onChange={handleFormChange}
                        placeholder="e.g. mechanics, thermodynamics, controls"
                        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    />
                </div>

                {/* Languages (only if Adaptive) */}
                {formData.isAdaptive && (
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Languages
                        </label>
                        <select
                            name="languages"
                            multiple
                            value={formData.languages}
                            onChange={handleFormChange}
                            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                        >
                            <option value="python">Python</option>
                            <option value="javascript">JavaScript</option>
                            <option value="both">Both</option>
                        </select>
                        <p className="text-xs text-gray-500 mt-1">
                            Hold <kbd>Ctrl</kbd> or <kbd>Cmd</kbd> to select multiple.
                        </p>
                    </div>
                )}

                {/* Qtype */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        Question Type
                    </label>
                    <select
                        name="qtypes"
                        value={formData.qtypes}
                        onChange={handleFormChange}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring focus:ring-blue-200"
                    >
                        <option value="">Select a type</option>
                        <option value="numerical">Numerical</option>
                        <option value="multiple-choice">Multiple Choice</option>
                        <option value="other">Other</option>
                    </select>
                </div>

                {/* Toggle Buttons */}
                <div className="flex justify-center">
                    <ToggleButtonGroup
                        color="primary"
                        value={alignment}
                        exclusive
                        onChange={handleToggleChange}
                        aria-label="question source"
                    >
                        <ToggleButton value="files">Files</ToggleButton>
                        <ToggleButton value="empty">Manual</ToggleButton>
                    </ToggleButtonGroup>
                </div>

                {/* File Upload */}
                {alignment === "files" && (
                    <div>
                        <UploadFilesButton onFilesSelected={setFiles} />
                        {files.length > 0 && (
                            <ul className="mt-4 space-y-2 text-sm text-gray-700">
                                {files.map((file, idx) => (
                                    <li
                                        key={idx}
                                        className="flex justify-between items-center bg-gray-100 px-3 py-2 rounded-md"
                                    >
                                        <span className="font-medium">{file.name}</span>
                                        <span className="text-xs text-gray-500">
                                            {Math.round(file.size / 1024)} KB
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </div>
                )}

                {/* Submit */}
                <div className="flex justify-center">
                    <MyButton name="Create Question" type="submit" />
                </div>
            </form>
        </div>
    );
}

export default QuestionCreationForm;
