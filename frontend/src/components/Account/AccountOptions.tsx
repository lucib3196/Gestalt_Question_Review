import { useAuth } from "../../context/AuthContext";
import { MyButton } from "../Base/Button";
import { deleteUser } from "firebase/auth";
import { toast } from "react-toastify";

export default function AccountOptions() {
    const { user, logout } = useAuth();

    const deleteAccount = async () => {
        if (!user) return;

        const confirmed = window.confirm(
            "Are you sure you want to permanently delete your account?"
        );
        if (!confirmed) return;

        try {
            await deleteUser(user);
            toast.success("Account deleted successfully.");
            window.location.reload();
        } catch (error: any) {
            toast.error(`Could not delete account: ${error.message}`);
        }
    };

    return (
        <div className="flex flex-col items-center p-6  bg-white dark:bg-neutral-900   max-w-md mx-auto">
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-200 mb-4">
                Account Options
            </h2>

            <div className="flex flex-col space-y-3 w-full">
                <MyButton name="Logout" onClick={logout} color="secondary" size="md" />

                <MyButton
                    name="Delete Account"
                    onClick={deleteAccount}
                    color="danger"
                    size="md"
                />
            </div>
        </div>
    );
}
