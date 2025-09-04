import type { FileData } from "../types/types";
import { toStringSafe } from "./generalUtils";

export const getLanguage = (selectedFile: string) =>
  selectedFile?.split(/[_\.]/).pop() || "";

export function getFileNames(data: FileData[]) {
  const names = (data ?? [])
    .map((f) => (typeof f?.filename === "string" ? f.filename : null))
    .filter(Boolean) as string[];
  return names;
}

export function fetchFileContent(filename: string, data: FileData[]) {
  try {
    const match = (data ?? []).find((f) => f.filename === filename);
    console.log(data, "this is filesa data");
    return match ? toStringSafe(match.content ?? "") : "";
  } catch (error) {
    console.log(error);
  }
}
