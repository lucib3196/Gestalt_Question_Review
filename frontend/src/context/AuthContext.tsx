import { onAuthStateChanged } from "firebase/auth";
import type { User } from "firebase/auth";
import { auth } from "../config/firebaseClient";
import { useState, useEffect } from "react";
import { createContext, useContext } from "react";
import { UserAPI, type UserDB } from "../api/userAPI";

export function useStateAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [userData, setUserData] = useState<UserDB | null>(null)
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const unSubscribe = onAuthStateChanged(auth, (fbUser) => {
            async function handleUser() {
                if (fbUser) {
                    console.log("User Signed In", fbUser.uid);
                    setUser(fbUser);
                    setLoading(false);

                    try {
                        const data = await UserAPI.getUser(fbUser);
                        setUserData(data)
                    } catch (error) {
                        console.error("Error fetching user data:", error);
                    }
                } else {
                    console.log("No User Logged In");
                    setUser(null);
                    setLoading(false);
                }
            }

            handleUser();
        });

        return () => unSubscribe();
    }, []);

    return { user, userData, loading };
}

type AuthContextType = {
    user: User | null;
    userData: UserDB | null
    loading: boolean;
    logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const { user, userData, loading } = useStateAuth();

    const logout = async () => {
        await auth.signOut();
        window.location.reload();
    };
    return (
        <AuthContext.Provider value={{ user, loading, logout, userData }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
