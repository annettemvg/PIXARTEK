export type Difficulty = "beginner" | "intermediate" | "advanced";

export interface Stage {
  number: number;
  title: string;
  description: string;
  duration_min: number;
  image?: string;   // static path for thumbnail, e.g. /artworks/mujer-azul-divisions/etapa-01.png
  objective?: string;
  colors?: string[];
  materials?: string[];
  brushes?: string[];
}

export interface Artwork {
  id: string;
  title: string;
  artist: string;
  year: number;
  difficulty: Difficulty;
  stages: Stage[];
  duration_min: number;   // total
  color: string;          // fallback background color
  image: string;          // URL de la obra (Wikimedia Commons)
  tags: string[];
}
