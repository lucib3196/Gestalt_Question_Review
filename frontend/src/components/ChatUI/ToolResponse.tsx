import type { ToolMessage } from "@langchain/langgraph-sdk";
import { useState } from "react";
import { FaArrowDown, FaArrowUp } from "react-icons/fa";
import { ToolShowContainer } from "./ToolCall";

type DisplayToolResponseProps = {
  message: ToolMessage;
};

export default function DisplayToolResponse({ message }: DisplayToolResponseProps) {
  const [showToolCall, setShowToolCall] = useState(false);

  return (
    <div className="top-0">
      {/* Toggle Button */}
      <button
        onClick={() => setShowToolCall((prev) => !prev)}
        className="w-full px-3 py-1 mb-3 text-sm font-semibold text-black transition hover:cursor-pointer"
      >
        {showToolCall ? (
          <ToolShowContainer>
            Hide Tool Response <FaArrowUp />
          </ToolShowContainer>
        ) : (
          <ToolShowContainer>
            Show Tool Response <FaArrowDown />
          </ToolShowContainer>
        )}
      </button>

      {/* Conditional Render */}
      {showToolCall && (
        <div className="border-t-2 border-b-2 border-gray-300 p-3 rounded-md bg-gray-50">
          <div key={message.id} className="p-2 border-b last:border-none">
            <div className="font-semibold text-gray-800">
              Tool Response: {String(message.content)}
              <br />
              Status: {message.status ?? "unknown"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
