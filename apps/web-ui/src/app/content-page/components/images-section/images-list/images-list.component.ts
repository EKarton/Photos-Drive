import { CommonModule } from '@angular/common';
import {
  AfterViewInit,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  OnDestroy,
  signal,
  ViewChild,
} from '@angular/core';
import { NgxMasonryComponent, NgxMasonryModule } from 'ngx-masonry';

import { RESIZE_OBSERVER_FACTORY_TOKEN } from '../../../../app.tokens';

export interface ImageData {
  id: string;
  baseUrl: string;
  width: number;
  height: number;
  fileName: string;
  onClick: (event: MouseEvent) => void;
  onKeyDown: (event: KeyboardEvent) => void;
}

@Component({
  standalone: true,
  selector: 'app-content-images-list',
  imports: [CommonModule, NgxMasonryModule],
  templateUrl: './images-list.component.html',
  styleUrl: './images-list.component.scss',
})
export class ImagesListComponent implements AfterViewInit, OnDestroy {
  private readonly resizeObserverFactory = inject(
    RESIZE_OBSERVER_FACTORY_TOKEN,
  );
  readonly images = input.required<ImageData[]>();

  @ViewChild(NgxMasonryComponent) ngxMasonryComponent?: NgxMasonryComponent;
  @ViewChild('masonryContainer') masonryContainer?: ElementRef;

  private observer?: ResizeObserver;
  private readonly gutterSizePx = 10;
  private readonly numColumns = signal(3);
  private readonly columnWidth = signal(200);

  readonly masonryOptions = computed(() => {
    return {
      itemSelector: '.masonry-item',
      percentPosition: true,
      gutter: this.gutterSizePx,
    };
  });

  readonly processedImages = computed(() => {
    return this.images().map((image: ImageData) => {
      const height = (image.height / image.width) * this.columnWidth();

      return {
        ...image,
        width: this.columnWidth(),
        height,
      };
    });
  });

  ngAfterViewInit() {
    this.observer = this.resizeObserverFactory.build((entries) => {
      entries.forEach((entry) => {
        const componentWidth = entry.contentRect.width;
        const numColumns = determineNumColumns(componentWidth);

        const availableSpace =
          componentWidth - (numColumns - 1) * this.gutterSizePx;
        this.columnWidth.set(Math.floor(availableSpace / numColumns));
        this.numColumns.set(numColumns);

        this.ngxMasonryComponent?.reloadItems();
        this.ngxMasonryComponent?.layout();
      });
    });

    // Start observing the target element
    if (this.masonryContainer) {
      this.observer.observe(this.masonryContainer.nativeElement);
    }
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}

function determineNumColumns(componentWidth: number) {
  if (componentWidth < 400) {
    return 1;
  }

  if (componentWidth < 1000) {
    return 2;
  }

  if (componentWidth < 1400) {
    return 3;
  }

  return 4;
}
