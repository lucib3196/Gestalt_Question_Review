export default function AccountProfilePic({ src }: { src?: string }) {
    return <div className="flex flex-col items-center text-center">
        <p className="font-semibold text-gray-700 mb-3 dark:text-gray-300">
            Profile Picture
        </p>

        <img
            src={src ?? ""}
            alt="Profile pic"
            className="w-32 h-32 object-cover rounded-full border shadow"
        />
    </div>

}
