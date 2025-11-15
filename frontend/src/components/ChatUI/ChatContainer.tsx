import type { ReactNode } from "react";

export default function ChatContainer({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col w-[800px] h-[600px] bg-gray-100 border rounded-lg shadow-md overflow-hidden">
      {children}
    </div>
  );
}
