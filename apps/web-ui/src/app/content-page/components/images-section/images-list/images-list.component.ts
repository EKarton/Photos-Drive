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
import { ImageComponent } from './image/image.component';

@Component({
  standalone: true,
  selector: 'app-content-images-list',
  imports: [CommonModule, NgxMasonryModule, ImageComponent],
  templateUrl: './images-list.component.html',
  styleUrl: './images-list.component.scss',
})
export class ImagesListComponent implements AfterViewInit, OnDestroy {
  private readonly resizeObserverFactory = inject(
    RESIZE_OBSERVER_FACTORY_TOKEN,
  );
  readonly mediaItemIds = input.required<string[]>();

  @ViewChild(NgxMasonryComponent) ngxMasonryComponent?: NgxMasonryComponent;
  @ViewChild('masonryContainer') masonryContainer?: ElementRef;

  private observer?: ResizeObserver;
  private readonly gutterSizePx = 10;
  private readonly numColumns = signal(3);

  readonly columnWidth = signal(200);

  readonly masonryOptions = computed(() => {
    return {
      itemSelector: '.masonry-item',
      percentPosition: true,
      gutter: this.gutterSizePx,
    };
  });

  private readonly pageSize = 5;
  private currentPage = signal(1);

  readonly paginatedMediaItemIds = computed(() => {
    const startIndex = (this.currentPage() - 1) * this.pageSize;
    const endIndex = startIndex + this.pageSize;
    return this.mediaItemIds().slice(startIndex, endIndex);
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

  imageSizesChanged() {
    this.ngxMasonryComponent?.layout();
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
