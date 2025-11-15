// questionHooks.ts
import { useState, useCallback, useEffect, } from "react";
import type { QuestionParams } from "../types/questionTypes";
import { useCodeEditorContext } from "../context/CodeEditorContext";
import { QuestionAPI } from "../api/questionAPI";
import type { QuestionData } from "../types/questionTypes";
import { useQuestionContext } from "../context/QuestionContext";

export function useRetrievedQuestions({
  questionFilter,
  showAllQuestions,
}: {
  questionFilter: QuestionData;
  showAllQuestions: boolean;
}) {
  const { setQuestions } = useQuestionContext();
  const fetchQuestions = useCallback(async () => {
    try {
      const filter = showAllQuestions ? {} : questionFilter;
      const retrieved = await QuestionAPI.filterQuestions(filter);
      setQuestions(retrieved);
    } catch (error) {
      console.error("Failed to fetch questions:", error);
    }
  }, [showAllQuestions, questionFilter, setQuestions]);

  useEffect(() => {
    fetchQuestions();
  }, [fetchQuestions]);
}

export function useAdaptiveParams(isAdaptive: boolean) {
  const { codeRunningSettings, setLogs } = useCodeEditorContext();
  const { selectedQuestionID } = useQuestionContext();

  const [params, setParams] = useState<QuestionParams | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchParams = useCallback(async () => {
    if (!isAdaptive || !selectedQuestionID) return;
    try {
      setLoading(true);
      setError(null);
      const res = await QuestionAPI.runServer(selectedQuestionID, codeRunningSettings);
      setParams(res);
      if (res?.logs) setLogs(res.logs);
    } catch (err: any) {
      console.error("Error fetching adaptive params:", err);
      setError(err?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [isAdaptive, selectedQuestionID, codeRunningSettings]);

  useEffect(() => {
    if (isAdaptive) fetchParams();
  }, [fetchParams, isAdaptive]);

  return { params, loading, error, refetch: fetchParams };
}
