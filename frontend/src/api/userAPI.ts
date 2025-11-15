import type { User } from "firebase/auth";
import { getIdToken } from "firebase/auth";
import api from "./client";

export type UserRole = "admin" | "teacher" | "developer" | "student";
export type AllowedRoles = readonly UserRole[];

export type UserDB = {
  id?: string;
  username?: string;
  email?: string;
  role?: UserRole;
  fb_id?: string;
  storage_path?: string;
};

export class UserAPI {
  private static readonly base = "/users";

  static async getCurrentUser(token: string): Promise<UserDB> {
    const response = await api.get<UserDB>(this.base, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    console.log("[Frontend] User fetched:");
    return response.data;
  }

  static async createUser(
    username: string,
    email: string,
    user: User
  ): Promise<UserDB> {
    const token = await getIdToken(user);

    const data: UserDB = {
      email,
      username,
    };

    const response = await api.post<UserDB>(this.base, data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  }

  static async getUser(user: User): Promise<UserDB> {
    const token = await getIdToken(user);

    const response = await api.get<UserDB>(this.base, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  }

  static async deleteUser(user: User): Promise<UserDB> {
    const token = await getIdToken(user);

    const response = await api.delete<UserDB>(this.base, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  }

  static async updateUser(user: User, data: UserDB): Promise<UserDB> {
    const token = await getIdToken(user);

    const response = await api.put<UserDB>(`${this.base}/`, data, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    return response.data;
  }
}
