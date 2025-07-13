import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  input,
  OnDestroy,
  Signal,
  signal,
  ViewChild,
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
export class ImagesMapComponent implements AfterViewInit, OnDestroy {
  readonly albumId = input.required<string>();

  private readonly store = inject(Store);
  private readonly imagesMapViewStore = inject(ImagesMapStore);

  @ViewChild('fullscreenContainer', { static: true })
  fullscreenContainer!: ElementRef;

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
  readonly isFullscreen = signal(false);

  constructor() {
    effect(() => {
      this.imagesMapViewStore.loadImages({
        albumId: this.albumId(),
      });
    });
  }

  ngAfterViewInit() {
    document.addEventListener('fullscreenchange', this.onFullscreenChange);
  }

  ngOnDestroy() {
    document.removeEventListener('fullscreenchange', this.onFullscreenChange);
  }

  // Use an arrow function to preserve "this"
  onFullscreenChange = () => {
    const isNowFullscreen = !!document.fullscreenElement;
    this.isFullscreen.set(isNowFullscreen);
  };

  toggleFullscreen() {
    if (!this.isFullscreen()) {
      this.goFullscreen();
    } else {
      this.exitFullscreen();
    }
  }

  private goFullscreen() {
    const element = this.fullscreenContainer.nativeElement;
    if (element.requestFullscreen) {
      element
        .requestFullscreen()
        .then(() => this.isFullscreen.set(true))
        .catch((err: Error) => {
          console.error('Failed to enter fullscreen:', err);
        });
    }
  }

  private exitFullscreen() {
    document.exitFullscreen();

    this.isFullscreen.set(false);
  }
}
