import { useState } from "react";
import type { FormEvent } from "react";
import { MyButton } from "../Base/Button";
import { InputTextForm } from "./../Forms/InputComponents";
import { UseAuthMode } from "../../context/AuthMode";
import { getAuth, sendPasswordResetEmail } from "firebase/auth";
import { toast } from "react-toastify";

type AuthProps = {
    onSubmit: (
        email: string,
        password: string,
        username?: string
    ) => Promise<void>;
};
export default function AuthBase({ onSubmit }: AuthProps) {
    const { mode, setMode } = UseAuthMode();
    const auth = getAuth();

    const [name, setName] = useState<string>("");
    const [username, setUserName] = useState<string>("");
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (mode === "passwordReset") {
            await handlePasswordReset();
        } else {
            onSubmit(email, password, username);
        }
    };

    const handlePasswordReset = async () => {
        try {
            await sendPasswordResetEmail(auth, email);
            toast.success(`Password reset sent to ${email} (Check spam)`);
        } catch (error) {
            toast.error("Could not reset password");
        }
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="flex flex-wrap flex-col  gap-y-3 items-center justify-center w-full h-full"
            id={mode}
        >
            {/* Name and username field — only for signup */}

            {mode === "signup" && (
                <>
                    <InputTextForm
                        value={name}
                        id="name"
                        type="text"
                        name="name"
                        label="Name"
                        placeholder="Freddy"
                        onChange={(e) => setName(e.target.value)}
                    />
                    <InputTextForm
                        value={username}
                        id="username"
                        type="text"
                        name="username"
                        label="Username"
                        placeholder="FreeBodyFreddy"
                        onChange={(e) => setUserName(e.target.value)}
                    />
                </>
            )}
            {/* Email field always show */}

            <InputTextForm
                value={email}
                id="email"
                type="email"
                name="email"
                label="Email"
                placeholder="FBody@email.com"
                onChange={(e) => setEmail(e.target.value)}
            />
            {/* Password field — hidden only during password reset */}

            {mode !== "passwordReset" && (
                <InputTextForm
                    value={password}
                    id="password"
                    type="password"
                    name="password"
                    label="Password"
                    placeholder="*********"
                    onChange={(e) => setPassword(e.target.value)}
                >
                    {mode === "login" && (
                        <div
                            onClick={() => setMode("passwordReset")}
                            className="text-sm text-violet-300 cursor-pointer hover:underline mt-2"
                        >
                            Forgot Password?
                        </div>
                    )}
                </InputTextForm>
            )}

            <MyButton
                type="submit"
                name={
                    mode === "login"
                        ? "Log In"
                        : mode === "signup"
                            ? "Sign Up"
                            : mode === "passwordReset"
                                ? "Send Password Reset"
                                : "Continue"
                }
            />
            {mode === "passwordReset" && (
                <MyButton
                    type="button" // prevent form submission
                    name="Go Back to Login"
                    onClick={() => setMode("login")}
                    size="md"
                />
            )}
        </form>
    );
}
