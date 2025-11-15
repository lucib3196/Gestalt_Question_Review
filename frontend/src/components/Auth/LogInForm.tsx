import AuthBase from "./AuthBase";
import {
  signInWithEmailAndPassword,
} from "firebase/auth";

import { toast } from "react-toastify";
import { auth } from "../../config/firebaseClient";

export function LogInForm() {
  const handleSubmit = async (email: string, password: string) => {
    try {
      await signInWithEmailAndPassword(
        auth,
        email,
        password
      );
      toast.success("Log In Successful");
    } catch (error: any) {
      toast.error(`Could not Log In ${error as string}`);
    }
  };
  return <AuthBase onSubmit={handleSubmit} />;
}
