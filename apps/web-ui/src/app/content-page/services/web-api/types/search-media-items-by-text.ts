import { MediaItem, RawMediaItem } from './media-item';

export interface SearchMediaItemsByTextRequest {
  text: string;
  earliestDateTaken?: Date;
  latestDateTaken?: Date;
  withinMediaItemIds?: string[];
}

export interface RawSearchMediaItemsByTextResponse {
  mediaItems: RawMediaItem[];
}

export interface SearchMediaItemsByTextResponse {
  mediaItems: MediaItem[];
}
