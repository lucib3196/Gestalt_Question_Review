import type { AIMessage } from "@langchain/langgraph-sdk";
import { useState } from "react";
import { FaArrowDown } from "react-icons/fa";
import { FaArrowUp } from "react-icons/fa";

type ToolCall = NonNullable<AIMessage["tool_calls"]>[number];

type DisplayToolCallProps = {
  toolCalls?: ToolCall[]; // optional or possibly undefined
};

export function ToolShowContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-row items-center justify-baseline gap-x-2">
      {children}
    </div>
  );
}

export default function DisplayToolCall({
  toolCalls = [],
}: DisplayToolCallProps) {
  const [showToolCall, setShowToolCall] = useState<boolean>(false);

  // Prevent render if there are no tool calls
  if (!toolCalls?.length) return null;

  return (
    <div className="top-0">
      {/* Toggle Button */}
      <button
        onClick={() => setShowToolCall((prev) => !prev)}
        className="w-full px-3 py-1 mb-3 text-sm font-semibold text-black transition hover:cursor-pointer"
      >
        {showToolCall ? (
          <ToolShowContainer>
            Hide Tool Calls <FaArrowUp />
          </ToolShowContainer>
        ) : (
          <ToolShowContainer>
            Show Tool Calls <FaArrowDown />
          </ToolShowContainer>
        )}
      </button>

      {/* Conditional Render */}
      {showToolCall && (
        <div className="border-t-2 border-b-2 border-gray-300 p-3 rounded-md bg-gray-50">
          {toolCalls.map((v) => (
            <div key={v.id || v.name} className="p-2 border-b last:border-none">
              <div className="font-semibold text-gray-800">
                Tool Call: {v.name}
              </div>
              <pre className="bg-gray-100 rounded p-2 text-sm text-gray-700 overflow-x-auto">
                {JSON.stringify(v.args, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}



