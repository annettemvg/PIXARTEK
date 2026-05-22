"use client";
import { useState, useEffect } from "react";
import type { Artwork } from "@/types/artwork";
import { ARTWORKS } from "@/lib/mock-artworks";
import { fetchArtworks } from "@/lib/api-client";

export type DataSource = "api" | "mock";

export function useArtworks() {
  const [artworks, setArtworks] = useState<Artwork[]>(ARTWORKS);
  const [source, setSource] = useState<DataSource>("mock");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchArtworks()
      .then((data) => {
        setArtworks(data as Artwork[]);
        setSource("api");
      })
      .catch(() => {
        // API unavailable — keep mock data silently
        setSource("mock");
      })
      .finally(() => setLoading(false));
  }, []);

  return { artworks, source, loading };
}
