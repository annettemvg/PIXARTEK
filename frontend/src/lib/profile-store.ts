"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserProfile } from "@/types/session";

export const AVATARS = ["🎨", "🖌️", "🖼️", "🎭", "✏️", "🦄", "🐉", "🌟"];

interface ProfileStore {
  profile: UserProfile | null;
  setProfile: (p: UserProfile) => void;
  clearProfile: () => void;
}

export const useProfileStore = create<ProfileStore>()(
  persist(
    (set) => ({
      profile: null,
      setProfile: (p) => set({ profile: p }),
      clearProfile: () => set({ profile: null }),
    }),
    { name: "pixartek-profile" }
  )
);
