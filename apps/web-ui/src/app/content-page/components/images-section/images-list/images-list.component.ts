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
import { InfiniteScrollDirective } from 'ngx-infinite-scroll';
import { NgxMasonryComponent, NgxMasonryModule } from 'ngx-masonry';

import { RESIZE_OBSERVER_FACTORY_TOKEN } from '../../../../app.tokens';
import { ImageComponent } from './image/image.component';

const PAGE_SIZE = 50;

@Component({
  standalone: true,
  selector: 'app-content-images-list',
  imports: [
    CommonModule,
    NgxMasonryModule,
    InfiniteScrollDirective,
    ImageComponent,
  ],
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

  private maxMediaItemIds = signal(PAGE_SIZE);

  readonly paginatedMediaItemIds = computed(() => {
    return this.mediaItemIds().slice(0, this.maxMediaItemIds());
  });

  ngAfterViewInit() {
    this.observer = this.resizeObserverFactory.build((entries) => {
      entries.forEach((entry) => {
        const componentWidth = entry.contentRect.width;
        const numColumns = determineNumColumns(componentWidth);

        const availableSpace =
          componentWidth - (numColumns - 1) * this.gutterSizePx;
        const newColumnWidth = Math.floor(availableSpace / numColumns);

        this.columnWidth.set(newColumnWidth);
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

  getMoreMediaItemIds() {
    this.maxMediaItemIds.set(this.maxMediaItemIds() + PAGE_SIZE);
    this.ngxMasonryComponent?.reloadItems();
    this.ngxMasonryComponent?.layout();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }
}

function determineNumColumns(componentWidth: number) {
  if (componentWidth < 400) {
    return 2;
  }

  if (componentWidth < 1000) {
    return 3;
  }

  if (componentWidth < 1400) {
    return 4;
  }

  return 5;
}
