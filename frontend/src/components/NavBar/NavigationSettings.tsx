
// Types
import type { NavigationItem } from "../../types/navbarTypes";

// Pages
import Home from "../../pages/Home";
import ChatPage from "../../pages/ChatPage";
import AccountPage from "../../pages/AccountPage";
import { QuestionViewPage } from "../../pages/QuestionsPage";

// Generators
import TextGenerator from "../CodeGenerators/TextGenerator";
import ImageGenerator from "../CodeGenerators/ImageGenerator";



export const Navigation: NavigationItem[] = [
    //
    // MAIN ROUTES
    //
    {
        type: "route",
        name: "Home",
        href: "/",
        element: <Home />,
        includeNavBar: true,
        requiresAuth: false,
        allowedRoles: ["student", "developer", "teacher", "admin"]
    },
    {
        type: "route",
        name: "Home",
        href: "/home",
        element: <Home />,
        includeNavBar: false,
        requiresAuth: false,
        allowedRoles: ["student", "developer", "teacher", "admin"]
    },
    {
        type: "route",
        name: "Questions",
        href: "/questions",
        element: <QuestionViewPage />,
        includeNavBar: true,
        requiresAuth: false,
        allowedRoles: ["student", "developer", "teacher", "admin"]
    },

    //
    // GENERATORS DROPDOWN
    //
    {
        type: "dropdown",
        name: "Generators",
        includeNavBar: true,
        requiresAuth: true,
        allowedRoles: ["developer", "teacher", "admin"],
        items: [
            {
                name: "Text",
                href: "/generators/text_generator",
                element: <TextGenerator />,
                allowedRoles: ["developer", "teacher", "admin"]
            },
            {
                name: "Image Upload",
                href: "/generators/image_generator",
                element: <ImageGenerator />,
                allowedRoles: ["developer", "teacher", "admin"]
            },
        ],
    },

    //
    // CHAT
    //
    {
        type: "route",
        name: "Chat",
        href: "/chat",
        element: <ChatPage />,
        includeNavBar: true,
        requiresAuth: false,
        allowedRoles: ["developer", "teacher", "admin"]
    },

    //
    // ACCOUNT PAGE
    //
    {
        type: "route",
        name: "My Account",
        href: "/account",
        element: <AccountPage />,
        includeNavBar: false,   // Hidden from Navbar
        requiresAuth: true,     // Protected route
        allowedRoles: ["developer", "teacher", "admin", "student"]
    }
];

