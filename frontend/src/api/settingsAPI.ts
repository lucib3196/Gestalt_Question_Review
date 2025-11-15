import api from "./client";

type Settings = {
    storage_type: "cloud" | "local";
};
export const getSettings = async () => {
    try {
        const response = await api.get<Settings>("/settings");
        return response.data.storage_type;
    } catch (error) {
        console.error("Could not fetch question settings", error);
    }
};