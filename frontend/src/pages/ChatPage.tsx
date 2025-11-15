import { useState } from "react";
import ChatUI from "../components/ChatUI/ChatUI";


export const availableChats = [
  "math_helper",
  "topic_classification",
  "ucr_mechanical_courses",
] as const;

export type AvailableChats = (typeof availableChats)[number];

const Chats: Record<AvailableChats, string> = {
  math_helper:
    "A basic chatbot equipped with tools for performing arithmetic operations such as addition and multiplication.",

  topic_classification:
    "A chatbot that classifies questions based on a document store using embedding similarity or metadata lookup.",
  ucr_mechanical_courses:
    "A chatbot that answer questions based on the UCR mechanical engineering Catalog using embedding similarity or metadata lookup. ",
};

function ChatDropDown({
  selectedChat,
  setSelectedChat,
}: {
  selectedChat: AvailableChats;
  setSelectedChat: (val: AvailableChats) => void;
}) {
  const handleSelectionChange = (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    setSelectedChat(event.target.value as AvailableChats);
  };

  const cleaned = selectedChat.trim();
  return (
    <div className="w-full">
      {" "}
      <label
        htmlFor="ChatSelection"
        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
      >
        Select Chat
      </label>
      <select
        id="ChatSelection"
        name="ChatSelection"
        value={cleaned}
        onChange={handleSelectionChange}
        className="w-full rounded-lg border border-gray-300 bg-white dark:bg-gray-800
                   text-gray-900 dark:text-gray-100 text-sm px-3 py-2
                   focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent
                   transition-colors duration-200 ease-in-out"
      >
        {availableChats.map((v) => (
          <option key={v} value={v.trim()}>
            {v.trim()}
          </option>
        ))}
      </select>
    </div>
  );
}

export default function ChatPage() {
  const [selectedChat, setSelectedChat] =
    useState<AvailableChats>("math_helper");
  return (
    <div className="min-h-screen w-full text-black flex flex-col items-center px-6 py-12 space-y-10">
      {/* Header */}
      <header className="flex flex-col items-center">
        <h1 className="text-4xl font-bold mb-3">Interactive Chatbots</h1>
        <p className="text-center max-w-2xl text-gray-700">
          These chatbots are designed for specific tasks within the system. They
          are used for testing, debugging, and previewing how the agent
          architecture behaves in real time.
        </p>
      </header>

      {/* Chat selection */}
      <section className="w-full max-w-2xl bg-gray-100 rounded-xl p-6 border border-gray-300 shadow-sm">
        <div className="flex flex-col space-y-4">
          <div className="flex flex-col items-center space-y-3">
            <h2 className="text-xl font-semibold text-gray-800">
              Select a Chatbot
            </h2>

            <ChatDropDown
              setSelectedChat={(value) => setSelectedChat(value)}
              selectedChat={selectedChat}
            />
          </div>

          <div className="bg-white p-4 rounded-md border border-gray-200">
            <h3 className="font-semibold text-gray-800 mb-1">Description</h3>
            <p className="text-gray-600 text-sm">{Chats[selectedChat]}</p>
          </div>
        </div>
      </section>

      {/* Chat UI */}
      <div className="w-full flex justify-center items-center max-w-3xl">
        <ChatUI assistantID={selectedChat} />
      </div>
    </div>
  );
}
