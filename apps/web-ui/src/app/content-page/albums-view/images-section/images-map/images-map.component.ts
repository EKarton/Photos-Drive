import { CommonModule } from '@angular/common';
import {
  Component,
  computed,
  effect,
  inject,
  input,
  Signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';

import * as results from '../../../../shared/results/results';
import * as themeState from '../../../../themes/store/theme.state';
import { MediaItem } from '../../../services/types/media-item';
import { ImagesMapStore } from './images-map.store';
import { ImagesMapViewerComponent } from './images-map-viewer/images-map-viewer.component';

@Component({
  standalone: true,
  selector: 'app-content-images-map',
  imports: [CommonModule, FormsModule, ImagesMapViewerComponent],
  templateUrl: './images-map.component.html',
  providers: [ImagesMapStore],
})
export class ImagesMapComponent {
  readonly albumId = input.required<string>();

  private readonly store = inject(Store);
  private readonly imagesMapViewStore = inject(ImagesMapStore);

  readonly isFetchingImages: Signal<boolean> =
    this.imagesMapViewStore.isFetchingImages;

  readonly images: Signal<MediaItem[]> = computed(() => {
    const imagesResult = this.imagesMapViewStore.images();
    if (!results.hasSucceed(imagesResult)) {
      return [];
    }

    return imagesResult.data!;
  });

  readonly isDarkMode = this.store.selectSignal(themeState.selectIsDarkMode);

  constructor() {
    effect(() => {
      this.imagesMapViewStore.loadImages({
        albumId: this.albumId(),
      });
    });
  }
}
