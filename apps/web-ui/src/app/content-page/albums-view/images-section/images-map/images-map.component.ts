import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  computed,
  effect,
  ElementRef,
  HostListener,
  inject,
  input,
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
export class ImagesMapComponent implements AfterViewInit {
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

  constructor() {
    effect(() => {
      this.imagesMapViewStore.loadImages({
        albumId: this.albumId(),
      });
    });
  }

  @HostListener('document:keydown.escape', ['$event'])
  onEscapeKey() {
    console.log('Escape pressed');
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  }

  readonly isFullscreen = signal(false);

  ngAfterViewInit() {
    console.log('View initialized:', this.fullscreenContainer);
  }

  toggleFullscreen() {
    if (!this.isFullscreen()) {
      this.goFullscreen();
      this.isFullscreen.set(true);
    } else {
      this.exitFullscreen();
      this.isFullscreen.set(false);
    }
  }

  goFullscreen() {
    const elem = this.fullscreenContainer.nativeElement;
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if ((elem as any).webkitRequestFullscreen) {
      (elem as any).webkitRequestFullscreen(); // Safari
    } else if ((elem as any).msRequestFullscreen) {
      (elem as any).msRequestFullscreen(); // IE/Edge
    }
  }

  exitFullscreen() {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen();
    } else if ((document as any).msExitFullscreen) {
      (document as any).msExitFullscreen();
    }
  }
}
