import SectionContainer from "../components/Base/SectionContainer";
import profilePic from "../assets/react.svg"
import AccountPageHeader from "../components/Account/AccountPageHeader";
import AccountProfilePic from "../components/Account/AccountProfilePic";
import AccountInformation from "../components/Account/AccountInformation";
import AccountOptions from "../components/Account/AccountOptions";
import { useAuth } from "../context/AuthContext";

export default function AccountPage() {
  const { user } = useAuth();

  return (
    <SectionContainer
      id="AccountPage"
      className="flex flex-col gap-y-8 py-8 max-w-4xl mx-auto min-h-screen"
    >
      {/* If user is not logged in */}
      {!user && (
        <div className="w-full p-6 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg text-center">
          <p className="text-red-600 dark:text-red-400 font-medium text-lg">
            You need to be logged in to view this page.
          </p>
        </div>
      )}

      {/* Actual Account Page */}
      {user && (
        <>
          <AccountPageHeader />
          <div className=" bg-white dark:bg-neutral-900 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-neutral-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-baseline">
              <AccountProfilePic src={profilePic} />
              <AccountInformation />
            </div>
            <AccountOptions />
          </div>
        </>
      )}
    </SectionContainer>
  );
}
