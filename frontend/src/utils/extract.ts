import React from "react";

export function getChildrenSafe(node: unknown): React.ReactNode | null {
    if (!React.isValidElement(node)) return null;

    const props = (node as Record<string, any>).props;

    if (!Object.prototype.hasOwnProperty.call(props, "children")) {
        return null;
    }
    return props.children ?? null;
}