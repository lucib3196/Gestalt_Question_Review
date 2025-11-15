import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
} from "@headlessui/react";

import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";
import { ChevronDownIcon } from "@heroicons/react/20/solid";

import { useState } from "react";
import { BrowserRouter as Router, Routes, Link } from "react-router-dom";

import { Navigation } from "./NavigationSettings";
import AuthenticationPage from "../../pages/AuthenticationPage";
import { useAuth } from "../../context/AuthContext";
import { handleRoutes } from "./Routes";
import { canAccessRoute } from "./utils";
import type { NavigationItem } from "../../types/navbarTypes";

function DropDownNav({ nav }: { nav: NavigationItem }) {
  if (nav.type !== "dropdown") return;
  return (
    <Menu key={nav.name} as="div" className="relative">
      <MenuButton className="flex items-center text-lg text-white hover:text-gray-200">
        <span>{nav.name}</span>
        <ChevronDownIcon className="ml-1 h-4 w-4" />
      </MenuButton>
      <MenuItems className="absolute left-0 mt-2 w-40 rounded-xl border border-white/20 bg-gray-800 text-white text-sm shadow-lg ring-1 ring-black/5 focus:outline-none">
        {nav.items.map((child) => (
          <MenuItem key={child.name}>
            <Link
              to={child.href}
              className="block px-3 py-2 rounded-md hover:bg-white/10"
            >
              {child.name}
            </Link>
          </MenuItem>
        ))}
      </MenuItems>
    </Menu>
  );
}

function SingleNav({ nav }: { nav: NavigationItem }) {
  if (nav.type !== "route") return;
  return (<Link
    key={nav.name}
    to={nav.href}
    className="px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
  >
    {nav.name}
  </Link>)
}

function NavBar() {
  const [showLogin, setShowLogin] = useState(false);
  const { user, logout, userData } = useAuth();

  const accountNav = Navigation.find((v) => v.name === "My Account");

  return (
    <Router>
      <Disclosure as="nav" className="bg-gray-800">
        <div className="mx-auto max-w-7xl px-2 sm:px-6 lg:px-8">
          <div className="relative flex h-16 items-center justify-between">
            {/* Mobile Hamburger */}
            <div className="absolute inset-y-0 left-0 flex items-center sm:hidden">
              <DisclosureButton className="group inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:bg-gray-700 hover:text-white">
                <Bars3Icon className="block h-6 w-6 group-data-open:hidden" />
                <XMarkIcon className="hidden h-6 w-6 group-data-open:block" />
              </DisclosureButton>
            </div>

            {/* Desktop Navigation */}
            <div className="flex flex-1 items-center justify-center sm:items-stretch sm:justify-start">
              <div className="hidden sm:block sm:ml-6">
                <div className="flex items-center space-x-4">
                  {/* Start the mapping of the navigation items */}
                  {Navigation.map((nav) =>
                    nav.includeNavBar &&
                    canAccessRoute(nav, user, userData?.role ?? "student") && (
                      nav.type === "dropdown" ? (
                        <DropDownNav key={nav.name} nav={nav} />
                      ) : (
                        <SingleNav key={nav.name} nav={nav} />
                      )
                    )
                  )}
                </div>
              </div>

              {/* Right-side buttons */}
              <div className="ml-auto flex items-center text-white space-x-4">
                {user ? (
                  <>
                    <button
                      onClick={logout}
                      className="px-4 py-2 font-semibold transition transform hover:scale-105 active:scale-95"
                    >
                      Logout
                    </button>

                    {accountNav && (
                      <Link
                        to={accountNav.type === "route" ? accountNav.href : ""}
                        className="px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                      >
                        {accountNav.name}
                      </Link>
                    )}
                  </>
                ) : (
                  <button
                    onClick={() => setShowLogin((prev) => !prev)}
                    className="px-4 py-2 font-semibold transition transform hover:scale-105 active:scale-95"
                  >
                    Sign Up / Log In
                  </button>
                )}

                {showLogin && (
                  <AuthenticationPage
                    show={showLogin}
                    setShow={() => setShowLogin((prev) => !prev)}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <DisclosurePanel className="sm:hidden">
          <div className="space-y-1 px-2 pt-2 pb-3">
            {Navigation.map(
              (item) =>
                item.type === "route" &&
                item.includeNavBar && (
                  <DisclosureButton
                    key={item.name}
                    as={Link}
                    to={item.href}
                    className="block rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
                  >
                    {item.name}
                  </DisclosureButton>
                )
            )}
          </div>
        </DisclosurePanel>
      </Disclosure>

      {/* Render Routes */}
      <Routes>{handleRoutes(Navigation)}</Routes>
    </Router>
  );
}

export default NavBar;
