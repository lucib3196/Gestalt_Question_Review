import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useRef, useEffect } from "react";
import ChatContainer from "./ChatContainer";
import ChatMessageContainer from "./ChatMessage";
import { useState } from "react";

type ChatUIProps = {
    assistantID: string;
};

export default function ChatUI({ assistantID }: ChatUIProps) {
    const thread = useStream<{ messages: Message[] }>({
        apiUrl: "http://localhost:2024",
        assistantId: assistantID,
        messagesKey: "messages",
    });

    const endRef = useRef<HTMLDivElement | null>(null);
    const [stableMessages, setStableMessages] = useState(thread.messages);

    // Auto-scroll to bottom
    useEffect(() => {
        const handle = setTimeout(() => {
            setStableMessages(thread.messages);
        }, 150); // 150ms debounce delay

        return () => clearTimeout(handle);
    }, [thread.messages]);

    return (
        <ChatContainer>
            {/* Messages container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 text-sm">
                {stableMessages.map((message) => (
                    <ChatMessageContainer message={message}></ChatMessageContainer>
                ))}
                <div ref={endRef} />
            </div>

            {/* Input form */}
            <form
                onSubmit={(e) => {
                    e.preventDefault();
                    const form = e.target as HTMLFormElement;
                    const message = new FormData(form).get("message") as string;
                    form.reset();
                    thread.submit({ messages: [{ type: "human", content: message }] });
                }}
                className="flex border-t bg-white p-2 gap-2"
            >
                <input
                    type="text"
                    name="message"
                    placeholder="Type a message..."
                    className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    disabled={thread.isLoading}
                />
                {thread.isLoading ? (
                    <button
                        type="button"
                        onClick={() => thread.stop()}
                        className="px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 text-sm"
                    >
                        Stop
                    </button>
                ) : (
                    <button
                        type="submit"
                        className="px-3 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 text-sm"
                    >
                        Send
                    </button>
                )}
            </form>
        </ChatContainer>
    );
}
