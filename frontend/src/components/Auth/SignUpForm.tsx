import AuthBase from "./AuthBase";
import { toast } from "react-toastify";
import { FirebaseError } from "firebase/app";
import { UserAPI } from "../../api/userAPI";

import {
    createUserWithEmailAndPassword,
    sendEmailVerification,
} from "firebase/auth";
import { auth } from "../../config/firebaseClient";

export function SignUpForm() {
    const handleSubmit = async (email: string, password: string, username?: string) => {
        try {
            const userCredential = await createUserWithEmailAndPassword(
                auth,
                email,
                password
            );
            const user = userCredential.user;

            if (user && !user.emailVerified) {
                await sendEmailVerification(user);
                toast.info(`A verification email has been sent to ${email}  `);
            }
            // Add the user to the database
            await UserAPI.createUser(username ?? "", email, user)
        } catch (error) {
            let errorMsg = "";
            if (error instanceof FirebaseError) {
                errorMsg = error.message;
            } else {
                errorMsg = error as string
            }
            toast.error(`Could not create account ${errorMsg ?? ""}`);
        }
    };

    return <AuthBase onSubmit={handleSubmit} />;
}
