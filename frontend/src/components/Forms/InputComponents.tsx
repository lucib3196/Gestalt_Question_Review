import clsx from "clsx";

export type InputStyleVariant = "default" | "outline" | "filled" | "hidden";

export const inputStyle: Record<InputStyleVariant, string> = {
  default:
    "rounded-md bg-white/5 px-3 py-1.5 outline outline-1 outline-black placeholder:text-gray-500",

  outline:
    "rounded-md bg-transparent px-3 py-1.5 border border-gray-400 text-black placeholder:text-gray-500 focus:border-indigo-500",

  filled:
    "rounded-md bg-gray-200 px-3 py-1.5 text-black placeholder:text-gray-600 focus:bg-white",
  hidden: "placeholder:text-gray-600 focus:bg-white"
};

export type InputComponentProps =
  React.InputHTMLAttributes<HTMLInputElement> & {
    label: string;
    style?: InputStyleVariant;
  };

export function InputTextForm({
  label,
  children,
  style = "default",
  className,
  ...props
}: InputComponentProps) {
  return (
    <div className="mt-2 w-1/2 min-w-[200px]">
      <label
        className="block text-sm font-medium text-black"
        htmlFor={props.id}
      >
        {label}
      </label>

      <input
        {...props}
        className={clsx(
          inputStyle[style as InputStyleVariant],
          "block w-full text-black ",
          className
        )}
      />

      {children}
    </div>
  );
}
