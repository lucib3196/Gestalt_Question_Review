import clsx from "clsx";
import type { Message } from "@langchain/langgraph-sdk";
import DisplayToolCall from "./ToolCall";
import DisplayToolResponse from "./ToolResponse";
import ReactMarkdown from "react-markdown";
import { MathJax } from "better-react-mathjax";
import { markdownPlugins } from "./chatConfig";
import { markdownComponents } from "./chatConfig";

type MessageType = Message["type"];

const ChatMessageStyle: Partial<Record<MessageType, string>> = {
    human: "bg-blue-500 text-white self-end ml-auto",
    ai: "bg-gray-200 text-gray-800 self-start",
    tool: "bg-green-200 text-gray-800 self-start",
};

type ChatMessageProps = {
    message: Message;
};
export default function ChatMessageContainer({ message }: ChatMessageProps) {
    const isAI = message.type === "ai";
    const isTool = message.type === "tool";

    const renderContent = () => {
        if (isAI && message.tool_calls?.length) {
            return <DisplayToolCall toolCalls={message.tool_calls} />;
        }

        if (isTool) {
            return <DisplayToolResponse message={message} />;
        }

        // Default: regular text message
        return (
            <MathJax>
                <ReactMarkdown
                    remarkPlugins={markdownPlugins.remarkPlugins}
                    components={markdownComponents}
                >
                    {String(message.content ?? "")}
                </ReactMarkdown>
            </MathJax>
        );
    };

    return (
        <div
            key={message.id}
            className={clsx(
                "flex-1 relative overflow-y-auto p-4 space-y-3 text-sm rounded-md",
                ChatMessageStyle[message.type]
            )}
        >
            {renderContent()}
        </div>
    );
}
