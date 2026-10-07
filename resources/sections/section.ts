export interface ISectionItem {
  id: number;
  en: string;
  gu: string;
  transliteration?: string;
  category?: string;
  emoji?: string;
  audio_ios?: string;
  audio_android?: string;
  image?: string;
}

export interface ISectionFile {
  sectionId: number;
  sectionSlug: string;
  sectionName: string;
  totalItems: number;
  items: ISectionItem[];
}

export interface ISectionDefinition {
  id: string;
  sectionNumber: number;
  title_en: string;
  title_gu: string;
  icon?: string;
  totalItems: number;
  items: ISectionItem[];
}
