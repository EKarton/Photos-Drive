import { inject, Injectable } from '@angular/core';
import { Store } from '@ngrx/store';
import { DynamicStructuredTool } from 'langchain/tools';
import { firstValueFrom } from 'rxjs';
import { z } from 'zod';

import { selectAuthToken } from '../../../../auth/store/auth.state';
import { fromResult } from '../../../../shared/results/rxjs/fromResult';
import { WebApiService } from '../../web-api/web-api.service';
import {
  domainToToolMediaItem,
  MediaItemModelSchema,
} from './models/media-items';

export const SearchPhotosByTextToolInputSchema = z.object({
  query: z
    .string()
    .describe(
      'A text string describing what to find. This is required text that must be non-empty',
    ),
  earliest_date_taken: z
    .string()
    .default('')
    .describe('Earliest photo date (YYYY-MM-DD). Empty = no lower bound.'),
  latest_date_taken: z
    .string()
    .default('')
    .describe('Latest photo date (YYYY-MM-DD). Empty = no upper bound.'),
  within_media_item_ids: z
    .string()
    .default('')
    .describe(
      'Comma-separated list of media item IDs to include in search. Empty = all.',
    ),
  top_k: z
    .number()
    .default(5)
    .describe('Maximum number of similar photos to retrieve'),
});

export type SearchPhotosByTextToolInputType = z.infer<
  typeof SearchPhotosByTextToolInputSchema
>;

export const SearchPhotosByTextToolOutputSchema = z.object({
  media_items: z.array(MediaItemModelSchema).describe('List of similar photos'),
});

export type SearchPhotosByTextToolOutputType = z.infer<
  typeof SearchPhotosByTextToolOutputSchema
>;

@Injectable({ providedIn: 'root' })
export class SearchMediaItemsByTextTool extends DynamicStructuredTool {
  private readonly store = inject(Store);
  private readonly webApiService = inject(WebApiService);

  constructor() {
    super({
      name: 'SearchMediaItemsForText',
      description: `Use this tool to search for photos based on a natural language description. 
        This is ideal when the user describes what they want to see in photos — 
        for example, "sunsets on the beach", "photos with dogs", or "Christmas morning".
        The tool embeds the user's text query and retrieves visually similar media items
        from the photo library based on semantic similarity.`,
      schema: SearchPhotosByTextToolInputSchema,
      func: async (
        input: SearchPhotosByTextToolInputType,
      ): Promise<SearchPhotosByTextToolOutputType> => {
        const accessToken = await firstValueFrom(
          this.store.select(selectAuthToken),
        );

        const searchMediaItemsByTextResponse = await firstValueFrom(
          this.webApiService
            .searchMediaItemsByText(accessToken, {
              text: input.query,
              earliestDateTaken: input.earliest_date_taken
                ? new Date(input.earliest_date_taken)
                : undefined,
              latestDateTaken: input.latest_date_taken
                ? new Date(input.latest_date_taken)
                : undefined,
              withinMediaItemIds: input.within_media_item_ids
                ? input.within_media_item_ids.split(',')
                : undefined,
            })
            .pipe(fromResult()),
        );

        const mediaItems = searchMediaItemsByTextResponse.mediaItems;

        return {
          media_items: mediaItems.map(domainToToolMediaItem),
        };
      },
    });
  }
}
