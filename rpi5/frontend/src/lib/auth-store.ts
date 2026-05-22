import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface PixiUser {
  id: string;
  name: string;
  email?: string;
  picture?: string;
  level: "niño" | "principiante" | "intermedio" | "avanzado";
  guest?: boolean;
}

interface AuthState {
  user: PixiUser | null;
  setUser: (user: PixiUser) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (user) => set({ user }),
      logout: () => set({ user: null }),
    }),
    { name: "pixartek-auth" }
  )
);
