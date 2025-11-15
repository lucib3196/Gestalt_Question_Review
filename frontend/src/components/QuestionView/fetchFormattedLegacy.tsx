import type { QuestionParams } from "../../types/questionTypes";
import applyPlaceHolders from "../../utils/flattenParams";
import { useState, useEffect, useCallback } from "react";
import { QuestionAPI } from "../../api/questionAPI";
import { useQuestionContext } from "../../context/QuestionContext";
import { useCodeEditorContext } from "../../context/CodeEditorContext";

// type FormattedResult = { qStr: string | null; sStr: string[] | null };


// function formatWithParams(
//     rawHtml: string | null,
//     rawSolution: string | null | string[],
//     params: QuestionParams | null,
//     questionTitle: string
// ): FormattedResult {
//     type ChoiceParams = { fracQuestions: [number, number] };
//     const CHOICE_PARAMS: ChoiceParams = { fracQuestions: [1.0, 1.0] };

//     if (!rawHtml && !rawSolution) return { qStr: null, sStr: null };

//     const replacedQ = rawHtml ? applyPlaceHolders(rawHtml, params) : null;
//     const replacedS = rawSolution ? applyPlaceHolders(rawSolution ?? "", params) : null;

//     // const qRes = replacedQ
//     //     ? processPrairielearnTags(replacedQ, params, questionTitle, CHOICE_PARAMS)
//     //     : undefined;

//     const qStr = qRes?.htmlString ?? null;

//     // const sRes = replacedS
//     //     ? processPrairielearnTags(replacedS, params, questionTitle, CHOICE_PARAMS)
//     //     : undefined;

//     const solutionsStrings = sRes?.solutionsStrings ?? null;
//     const sStr = solutionsStrings ? Object.values(solutionsStrings) : [];

//     return { qStr, sStr };
// }

// --- React hook ---
// export function useFormattedLegacy(params: QuestionParams | null, questionTitle: string) {
//     const { selectedQuestionID } = useQuestionContext();

//     const [questionHtml, setQuestionHtml] = useState<string | null>(null);
//     const [solutionHTML, setSolutionHTML] = useState<string[] | null | string>(null);
//     const [loading, setLoading] = useState(false);
//     const [error, setError] = useState<string | null>(null);



//     const fetchBaseFiles = useCallback(async () => {
//         if (!selectedQuestionID) return;
//         setLoading(true);
//         try {
//             const [rawHtmlRes, rawSolutionRes] = await Promise.all([
//                 QuestionAPI.getQuestionFile(selectedQuestionID, "question.html"),
//                 QuestionAPI.getQuestionFile(selectedQuestionID, "solution.html"),
//             ]);

//             setQuestionHtml(rawHtmlRes?.data ?? null);
//             setSolutionHTML(rawSolutionRes?.data ?? null);
//         } catch (err: any) {
//             console.error("❌ Failed to fetch base HTML files:", err);
//             setError(err.message || "Failed to fetch base HTML files");
//         } finally {
//             setLoading(false);
//         }
//     }, [selectedQuestionID]);

//     // Fetch HTML once when question changes
//     useEffect(() => {
//         fetchBaseFiles();
//     }, [fetchBaseFiles]);

//     // Re-render processed HTML when params arrive
//     useEffect(() => {
//         if (!params) return;

//         setLoading(true);
//         try {
//             const { qStr, sStr } = formatWithParams(
//                 questionHtml,
//                 solutionHTML ?? "",
//                 params,
//                 questionTitle
//             );
//             setQuestionHtml(qStr);
//             setSolutionHTML(sStr);
//         } catch (err: any) {
//             console.error("❌ Failed to process HTML:", err);
//             setError(err.message || "Failed to process question HTML");
//         } finally {
//             setLoading(false);
//         }
//     }, [params, questionTitle]);

//     return { questionHtml, solutionHTML, loading, error };
// }


// Fetches the question html and solution html
export function useRawQuestionHTML() {
    const { selectedQuestionID } = useQuestionContext();
    const {refreshKey} = useCodeEditorContext()
    const [questionHtml, setQuestionHtml] = useState<string | null>(null);
    const [solutionHTML, setSolutionHTML] = useState<| null | string>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null)


    const fetchBaseFiles = useCallback(async () => {
        if (!selectedQuestionID) return;
        setLoading(true)
        try {
            const [rawHTMLRes, rawSolutionRes] = await Promise.all([
                QuestionAPI.getQuestionFile(selectedQuestionID, "question.html"),
                QuestionAPI.getQuestionFile(selectedQuestionID, "solution.html")
            ])
            setQuestionHtml(rawHTMLRes.data)
            setSolutionHTML(rawSolutionRes.data)
        }
        catch (error: any) {
            console.log("Failed to fetch base html files", error);
            setError(error.message || "Failed to fetch base html files")
        }
        finally {
            setLoading(false)
        }
    }, [selectedQuestionID, refreshKey])

    useEffect(() => {
        fetchBaseFiles();
    }, [fetchBaseFiles]);

    return { questionHtml, solutionHTML, loading, error };
}



type ParsedHTMLResult = {
    qHTML: string;
    sHTML: string;
};
/**
 * Parses the given question and solution HTML, replacing placeholders using provided params.
 */
export function useParsedQuestionHTML(
    questionHTML: string,
    params: QuestionParams | null,
    solutionHTML?: string
): ParsedHTMLResult | undefined {
    const [qHTML, setQHTML] = useState<string>("");
    const [sHTML, setSHtml] = useState<string>("");

    useEffect(() => {
        if (!params) return;

        const qProcessed = applyPlaceHolders(questionHTML, params);
        const sProcessed = applyPlaceHolders(solutionHTML ?? "", params);

        setQHTML(qProcessed);
        setSHtml(sProcessed);
    }, [params, questionHTML, solutionHTML]);

    if (!params) return undefined;

    return { qHTML, sHTML };
}