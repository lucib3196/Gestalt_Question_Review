import { UseAuthMode, type UserMode } from "../context/AuthMode";
import SectionContainer from "../components/Base/SectionContainer";
import { MyModal } from "../components/Base/MyModal";
import { useAuth } from "../context/AuthContext";
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import { LogInForm } from "../components/Auth/LogInForm";
import { SignUpForm } from "../components/Auth/SignUpForm";
import VerifyAccount from "../components/Auth/VerifyAccount";
import { TitleHeader } from "../components/Base/TitleHeader";


// Handles wether the page is show
type AuthenticationPageModel = {
    show: boolean;
    setShow: () => void;
};

export default function AuthenticationPage({
    show,
    setShow,
}: AuthenticationPageModel) {
    const { mode, setMode } = UseAuthMode();
    const { user } = useAuth();

    const handleAlignment = (
        _: React.MouseEvent<HTMLElement>,
        state: UserMode | null
    ) => {
        if (state !== null) setMode(state);
    };

    const shouldShowToggle = !user; // Only show toggle if not logged in
    const showLogin = mode === "login" && (!user);
    const showSignup = mode === "signup";
    const showVerify = mode === "authenticate" || (user && !user.emailVerified);

    return (
        <SectionContainer id="AuthenticationPage">
            {show && (
                <MyModal setShowModal={setShow} className="flex flex-col items-center justify-center gap-y-5">
                    {shouldShowToggle && (
                        <ToggleButtonGroup
                            value={mode}
                            exclusive
                            onChange={handleAlignment}
                            aria-label="auth toggle"
                            className="flex justify-center space-x-3"
                        >
                            <ToggleButton value="login" aria-label="login">
                                Log In
                            </ToggleButton>
                            <ToggleButton value="signup" aria-label="signup">
                                Sign Up
                            </ToggleButton>
                        </ToggleButtonGroup>
                    )}
                    <TitleHeader
                        value={
                            showLogin
                                ? "Log In"
                                : showSignup
                                    ? "Sign Up"
                                    : showVerify
                                        ? "Verify Account"
                                        : ""
                        }
                    />
                    {showLogin && <LogInForm />}
                    {showSignup && <SignUpForm />}
                    {showVerify && <VerifyAccount />}
                </MyModal>
            )}
        </SectionContainer>
    );
}
