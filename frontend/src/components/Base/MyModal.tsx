import { useEffect, useRef } from "react";
import { CloseButton } from "../CloseButton";
import clsx from "clsx";

const modalSizeVariants = {
  small: `
    w-11/12 max-w-sm   h-auto max-h-[80vh]   /* almost full width on mobile */
    sm:w-3/4 sm:max-w-md
    md:w-1/2 md:max-w-lg
  `,
  default: `
    w-11/12 max-w-md h-auto max-h-[85vh]
    sm:w-3/4 sm:max-w-lg
    md:w-2/3 md:max-w-2xl
    lg:w-1/2 lg:max-w-3xl
    min-h-1/2
  `,
  large: `
    w-11/12 h-8/10
    sm:w-4/5 sm:max-w-3xl
    md:w-3/4 md:max-w-4xl
    lg:w-2/3 lg:max-w-5xl
  `,
};

type ModalSizeVariants = keyof typeof modalSizeVariants;

type ModalProps = {
  variant?: ModalSizeVariants;
  setShowModal: (visible: boolean) => void;
  children: React.ReactNode;
  className?: string;
};

export function MyModal({
  variant = "default", // default applied here
  setShowModal,
  children,
  className,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        modalRef.current &&
        !modalRef.current.contains(event.target as Node)
      ) {
        setShowModal(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [setShowModal]);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center  bg-opacity-50 border-2 ">
      <div
        ref={modalRef}
        className={clsx(
          "flex flex-col bg-white  border-gray-300 rounded-lg shadow-xl/30 p-8 overflow-auto dark:bg-background",
          modalSizeVariants[variant],
          className
        )}
      >
        <div className="self-end">
          {" "}
          <CloseButton onClick={() => setShowModal(false)} />
        </div>
        {children}
      </div>
    </div>
  );
}
