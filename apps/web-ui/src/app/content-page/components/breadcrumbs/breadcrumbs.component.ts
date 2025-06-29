import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  inject,
  input,
  OnDestroy,
  OnInit,
  ViewChild,
} from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { Store } from '@ngrx/store';
import { filter, map, Observable, of, Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { hasSucceed, Result, toPending } from '../../../shared/results/results';
import { filterOnlySuccess } from '../../../shared/results/rxjs/filterOnlySuccess';
import { mapResult } from '../../../shared/results/utils/mapResult';
import { Album } from '../../services/types/album';
import { albumsActions, albumsState } from '../../store/albums';

export interface BreadcrumbItem {
  id: string;
  text: string;
  routerLink: string | undefined;
}

@Component({
  standalone: true,
  selector: 'app-content-page-breadcrumbs',
  imports: [CommonModule, RouterModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './breadcrumbs.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BreadcrumbsComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly subscriptions = new Subscription();

  readonly albumId = input.required<string>();

  @ViewChild('breadcrumbContainer')
  breadcrumbContainer?: ElementRef<HTMLDivElement>;

  private readonly albums$: Observable<Result<Album>[]> = toObservable(
    this.albumId,
  ).pipe(switchMap((albumId) => this.getParentAlbums(albumId)));

  readonly breadcrumbItems$: Observable<Result<BreadcrumbItem>[]> =
    this.albums$.pipe(
      map((albumsResults) =>
        albumsResults.map((albumResult) =>
          mapResult(albumResult, (album) => ({
            id: album.id,
            text: album.albumName || 'Home',
            routerLink: `/content/${album.id}`,
          })),
        ),
      ),
    );

  private getParentAlbums(albumId: string): Observable<Result<Album>[]> {
    const curAlbumResult$ = this.store.select(
      albumsState.selectAlbumDetailsById(albumId),
    );

    return curAlbumResult$.pipe(
      switchMap((curAlbumResult: Result<Album>) => {
        if (!hasSucceed(curAlbumResult)) {
          return of([curAlbumResult]);
        }

        const curAlbum = curAlbumResult.data!;
        if (!curAlbum.parentAlbumId) {
          return of([curAlbumResult]);
        }

        return this.getParentAlbums(curAlbum.parentAlbumId).pipe(
          map((parentAlbums: Result<Album>[]) => [
            ...parentAlbums,
            curAlbumResult,
          ]),
        );
      }),
    );
  }

  ngOnInit(): void {
    this.subscriptions.add(
      this.breadcrumbItems$
        .pipe(filter((breadcrumbItems) => breadcrumbItems.every(hasSucceed)))
        .subscribe(() => {
          setTimeout(() => {
            const el = this.breadcrumbContainer?.nativeElement;
            if (el) {
              el.scrollLeft = el.scrollWidth;
            }
          }, 0);
        }),
    );

    this.subscriptions.add(
      this.albums$
        .pipe(
          switchMap((albumsResults) => {
            for (const albumsResult of albumsResults) {
              if (hasSucceed(albumsResult)) {
                return of(albumsResult);
              }
            }
            return of(toPending<Album>());
          }),
          filterOnlySuccess(),
        )
        .subscribe((firstAlbum: Album) => {
          if (firstAlbum.parentAlbumId) {
            this.store.dispatch(
              albumsActions.loadAlbumDetails({
                albumId: firstAlbum.parentAlbumId,
              }),
            );
          }
        }),
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}
