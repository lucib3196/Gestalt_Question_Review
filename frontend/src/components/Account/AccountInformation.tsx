import { useAuth } from "../../context/AuthContext";
import { useEffect, useState } from "react";
import { FaEdit } from "react-icons/fa";
import { InputTextForm } from "../Forms/InputComponents";
import { MyButton } from "../Base/Button";
import AccountFieldContainer from "./AccountFieldContainer";
import { updateEmail, updatePassword } from "firebase/auth";
import { UserAPI } from "../../api/userAPI";
import type { UserDB } from "../../api/userAPI";
import { toast } from "react-toastify"

export default function AccountInformation() {
    const { user, userData } = useAuth();
    const [editMode, setEditMode] = useState<boolean>(false);

    // Form Props
    const [username, setUsername] = useState<string>("");
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("")

    useEffect(() => {
        if (!userData) return;
        setUsername(userData.username ?? "");
        setEmail(userData.email ?? "");
    }, [userData]);


    const handleUserUpdate = async () => {
        if (!user || !userData) return;
        try {
            // Update Firebase Email only if changed
            if (email !== userData.email) {
                await updateEmail(user, email);
            }

            // Update Firebase Password only if field is not empty
            if (password.trim().length > 0) {
                await updatePassword(user, password);
            }

            // Update your database only if username or email changed
            if (username !== userData.username || email !== userData.email) {
                const data: UserDB = { email, username };
                await UserAPI.updateUser(user, data);
            }

            toast.success("Successfully updated account.");
        } catch (error: any) {
            console.error(error);
            toast.error(
                error?.message ?? "Could not update account. Please try again."
            );
        }
    };

    if (!user || !userData) return;

    return (
        <div className="flex flex-col gap-y-4 p-4  bg-white  dark:bg-gray-900">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300">
                    Account Information
                </h2>

                <button
                    onClick={() => setEditMode((prev) => !prev)}
                    className="flex items-center gap-x-2 text-sm font-medium text-indigo-600 hover:text-indigo-700
                 dark:text-indigo-400 dark:hover:text-indigo-300 transition"
                >
                    <FaEdit className="w-4 h-4" />
                    <span>{editMode ? "Cancel" : "Edit"}</span>
                </button>
            </div>

            {/* Account Info Container */}
            <div className="flex flex-col gap-y-3 text-gray-800 dark:text-gray-200">

                {/* Username Field */}
                <AccountFieldContainer name="Username">
                    <InputTextForm
                        value={username ?? ""}
                        onChange={(e) => setUsername(e.target.value)}
                        disabled={!editMode}
                        className="w-full"
                        style={editMode ? "default" : "hidden"}
                        label=""
                    />
                </AccountFieldContainer>

                {/* Email Field */}
                <AccountFieldContainer name="Email">
                    <InputTextForm
                        value={email ?? ""}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={!editMode}
                        className="w-full"
                        style={editMode ? "default" : "hidden"}
                        label=""
                    />
                </AccountFieldContainer>
                <AccountFieldContainer name="Password">
                    <InputTextForm
                        value={password ?? ""}
                        onChange={(e) => setPassword(e.target.value)}
                        disabled={!editMode}
                        className="w-full"
                        style={editMode ? "default" : "hidden"}
                        label=""
                        type="password"
                        placeholder="**************"
                    />
                </AccountFieldContainer>

                {/* Role */}
                <div className="text-sm">
                    <span className="font-medium text-gray-600 dark:text-gray-400">
                        Role:
                    </span>
                    <span className="ml-1">{userData.role?.toUpperCase()}</span>
                </div>

                {/* Save Button */}
                {editMode && (
                    <div className="flex items-center justify-start pt-2">
                        <MyButton name="Save Changes" onClick={handleUserUpdate} />
                    </div>
                )}
            </div>
        </div>
    );
}
