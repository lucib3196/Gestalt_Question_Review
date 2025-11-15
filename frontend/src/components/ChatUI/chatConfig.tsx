import remarkGfm from "remark-gfm";

export const markdownPlugins = {
    remarkPlugins: [remarkGfm],
};

export const markdownComponents = {
    p: ({ children }: any) => (
        <p className="my-2 leading-relaxed text-white-800">
            {children}
        </p>
    ),

    // h1: ({ children }: any) => (
    //     <h1 className="text-2xl font-bold text-white mb-3 mt-4 leading-tight">
    //         {children}
    //     </h1>
    // ),

    // h2: ({ children }: any) => (
    //     <h2 className="text-xl font-semibold text-white mb-2 mt-3 leading-snug border-b border-gray-700 pb-1">
    //         {children}
    //     </h2>
    // ),

    // h3: ({ children }: any) => (
    //     <h3 className="text-lg font-semibold text-gray-200 mt-3 mb-2 leading-snug">
    //         {children}
    //     </h3>
    // ),

    // h4: ({ children }: any) => (
    //     <h4 className="text-base font-semibold text-gray-300 mt-2 mb-1 leading-snug">
    //         {children}
    //     </h4>
    // ),

    // strong: ({ children }: any) => (
    //     <strong className="font-semibold text-blue-600">
    //         {children}
    //     </strong>
    // ),

    // em: ({ children }: any) => (
    //     <em className="italic text-gray-700">
    //         {children}
    //     </em>
    // ),

    // blockquote: ({ children }: any) => (
    //     <blockquote className="border-l-4 border-blue-400 bg-gray-800/40 pl-4 pr-2 py-1 italic text-gray-300 rounded-r-md my-3">
    //         {children}
    //     </blockquote>
    // ),

    // ul: ({ children }: any) => (
    //     <ul className="list-disc list-inside my-2 space-y-1 text-gray-200">
    //         {children}
    //     </ul>
    // ),

    // ol: ({ children }: any) => (
    //     <ol className="list-decimal list-inside my-2 space-y-1 text-gray-200">
    //         {children}
    //     </ol>
    // ),

    // a: ({ href, children }: any) => (
    //     <a
    //         href={href}
    //         target="_blank"
    //         rel="noopener noreferrer"
    //         className="text-blue-500 hover:underline"
    //     >
    //         {children}
    //     </a>
    // ),

    // code: ({ inline, children }: any) =>
    //     inline ? (
    //         <code className="px-1 py-0.5 rounded bg-gray-200 text-gray-800 text-sm">
    //             {children}
    //         </code>
    //     ) : (
    //         <pre className="p-2 my-2 bg-gray-100 rounded text-sm text-gray-900 overflow-x-auto">
    //             <code>{children}</code>
    //         </pre>
    //     ),

    // table: ({ children }: any) => (
    //     <div className="overflow-x-auto my-3 rounded-md border border-gray-700">
    //         <table className="min-w-full text-sm text-gray-200 border-collapse">
    //             {children}
    //         </table>
    //     </div>
    // ),

    // th: ({ children }: any) => (
    //     <th className="bg-gray-800 border border-gray-700 px-3 py-2 font-semibold text-left">
    //         {children}
    //     </th>
    // ),

    // td: ({ children }: any) => (
    //     <td className="border border-gray-700 px-3 py-2 align-top">
    //         {children}
    //     </td>
    // ),
};
