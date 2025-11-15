import { useState } from "react";
import { DisplayFiles } from "../components/Generic/DisplayFiles";
import UploadFiles from "../components/Forms/UploadFileComponent";
import SectionContainer from "../components/Base/SectionContainer";


function CreateQuestionHeader() {

    const downloadTemplate = async () => {
        console.log("Downloading")
    };

    return (
        <div className="flex flex-col items-center text-center space-y-6">
            <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">
                Create a Question
            </h1>

            <p className="text-gray-600 dark:text-gray-300 max-w-xl">
                Manually create a new question or download a starter template to begin.
            </p>

            <div className="text-left max-w-xl w-full">
                <h2 className="font-semibold text-lg mb-2">Guidelines:</h2>
                <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    <li>
                        Include a{" "}
                        <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                            question.html
                        </code>{" "}
                        file
                    </li>
                    <li>
                        Include a{" "}
                        <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                            solution.html
                        </code>{" "}
                        file
                    </li>
                    <li>
                        For computation questions, upload a{" "}
                        <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                            server.js
                        </code>{" "}
                        or{" "}
                        <code className="px-1 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                            server.py
                        </code>{" "}
                        file
                    </li>
                </ul>
            </div>

            <p className="text-gray-600 dark:text-gray-300">
                Not sure where to start?{" "}
                <button
                    onClick={downloadTemplate}
                    className="text-blue-600 font-medium hover:underline focus:outline-none"
                >
                    Download the starter
                </button>
            </p>
        </div>
    );
}
// TODO: Add the actual logic for uploading the question 
function UploadQuestion() {
    const [files, setFiles] = useState<File[]>([]);
    const onFilesSelected = (files: File[]) => {
        setFiles(files);
    };
    return (
        <div className="mt-12 w-full flex flex-col items-center tet-center">
            <div className="w-11/12 md:w-2/3 lg:w-1/2 border border-gray-300 dark:border-gray-700 rounded-lg p-8 bg-white dark:bg-gray-800 shadow">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    Upload Your Question
                </h2>
                <p className="text-gray-600 dark:text-gray-300 mb-6">
                    Once you’ve finished creating your question files using the starter
                    template, upload them here.
                </p>

                <UploadFiles onFilesSelected={onFilesSelected} />
                <DisplayFiles files={files} />
            </div>
        </div>
    );
}

export default function CreateQuestionPage() {
    return (
        <SectionContainer id={"create-question"} style="hero">
            <div className="flex flex-col">
                {/* Step 1: Header + Guidelines */}
                <CreateQuestionHeader />

                {/* Step 2: Upload */}
                <UploadQuestion />
            </div>
        </SectionContainer>
    );
}
