import { createContext, useContext, useState } from "react";

export type UserMode = "login" | "signup" | "authenticate" | "passwordReset"

type AuthModeContext = {
    mode: UserMode,
    setMode: (val: UserMode) => void
}

const AuthModeContext = createContext<AuthModeContext | undefined>(undefined)

export function AuthModeProvider({ children }: { children: React.ReactNode }) {
    const [mode, setMode] = useState<UserMode>("signup")

    return (
        <AuthModeContext.Provider value={{ mode, setMode }}>
            {children}
        </AuthModeContext.Provider>
    )
}

export function UseAuthMode() {
    const context = useContext(AuthModeContext);
    if (context === undefined) {
        throw new Error("Auth Mode must be used within an SpriteProvider")
    }
    return context;
}