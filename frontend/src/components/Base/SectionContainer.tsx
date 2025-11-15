import clsx from "clsx";

type SectionType = "hero" | "primary"

const SectionTheme: Record<SectionType, string> = {
    hero: "min-h-screen flex items-center justify-center bg-blue-100 dark:bg-background transition-colors duration-300",
    primary: "min-h-screen border px-5 py-20 rounded-md",
}
type SectionProps = {
    id: string,
    children: React.ReactNode;
    className?: string,
    style?: SectionType
}


export default function SectionContainer({ id, children, className, style }: SectionProps) {
    return <section id={id} className={clsx(style ? SectionTheme[style] : "", className)}
    > {children}</section >
}