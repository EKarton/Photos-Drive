import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  inject,
  input,
  Signal,
  signal,
} from '@angular/core';
import { Pipe, PipeTransform } from '@angular/core';
import { RouterModule } from '@angular/router';

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import { hasSucceed, Result } from '../../../../shared/results/results';
import { mapResult } from '../../../../shared/results/utils/mapResult';
import { Album } from '../../../services/types/album';
import { AlbumsListTableStore } from './albums-list-table.store';

@Pipe({ name: 'range' })
export class RangePipe implements PipeTransform {
  transform(value: number): number[] {
    return Array.from({ length: value }, (_, i) => i + 1);
  }
}

@Component({
  standalone: true,
  selector: 'app-content-albums-list-table',
  imports: [
    CommonModule,
    RouterModule,
    HasFailedPipe,
    IsPendingPipe,
    RangePipe,
  ],
  templateUrl: './albums-list-table.component.html',
  providers: [AlbumsListTableStore],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlbumsListTableComponent {
  readonly albumId = input.required<string>();

  private readonly albumsListTableStore = inject(AlbumsListTableStore);

  readonly childAlbumsResult: Signal<Result<Album[]>> = computed(() => {
    const currentPageResult = this.albumsListTableStore.currentPage();
    return mapResult(currentPageResult, (currentPage) => currentPage.albums);
  });

  readonly pageNumber: Signal<number> = this.albumsListTableStore.pageNumber;

  readonly hasNextPage: Signal<boolean> = computed(() => {
    const currentPageResult = this.albumsListTableStore.currentPage();
    if (!hasSucceed(currentPageResult)) {
      return false;
    }

    return currentPageResult.data?.nextPageToken !== undefined;
  });

  readonly pageSizeOptions = [5, 10, 15];
  readonly currentPageSize = signal(5);

  constructor() {
    effect(() => {
      this.albumsListTableStore.loadInitialPage({
        albumId: this.albumId(),
        pageSize: this.currentPageSize(),
      });
    });
  }

  onPageSizeChange(event: Event) {
    const value = Number((event.target as HTMLSelectElement).value);
    this.currentPageSize.set(value);
  }

  goToFirstPage() {
    this.albumsListTableStore.goToFirstPage();
  }

  goToPreviousPage() {
    this.albumsListTableStore.goToPreviousPage();
  }

  goToNextPage() {
    this.albumsListTableStore.goToNextPage();
  }
}
