export default function AccountFieldContainer({
    name,
    children,
}: {
    name: string;
    children: React.ReactNode;
}) {
    return (
        <div className="flex flex-row items-baseline gap-x-4">
            <p className="font-medium text-gray-800 dark:text-gray-400">{name}</p>
            {children}
        </div>
    );
}