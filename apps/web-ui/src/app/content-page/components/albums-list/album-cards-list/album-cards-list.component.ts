import { CommonModule } from '@angular/common';
import {
  Component,
  inject,
  input,
  OnDestroy,
  OnInit,
  Signal,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { RouterModule } from '@angular/router';
import { Store } from '@ngrx/store';
import { combineLatest, map, Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../../shared/results/results';
import { combineResults } from '../../../../shared/results/utils/combineResults';
import { Album } from '../../../services/webapi.service';
import { albumsActions, albumsState } from '../../../store/albums';

@Component({
  selector: 'app-content-album-cards-list',
  imports: [CommonModule, RouterModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './album-cards-list.component.html',
  styleUrl: './album-cards-list.component.scss',
})
export class AlbumCardComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly subscription = new Subscription();

  readonly album = input.required<Album>();
  private readonly album$ = toObservable(this.album);

  private readonly childAlbumResults$ = this.album$.pipe(
    switchMap((curAlbum: Album) => {
      return combineLatest(
        curAlbum.childAlbumIds.map((childAlbumId: string) => {
          return this.store.select(
            albumsState.selectAlbumDetailsById(childAlbumId),
          );
        }),
      ).pipe(
        map((childAlbumResults: Result<Album>[]) => {
          return combineResults(childAlbumResults, (childAlbums: Album[]) => {
            return childAlbums;
          });
        }),
      );
    }),
  );

  readonly childAlbumResults: Signal<Result<Album[]>> = toSignal(
    this.childAlbumResults$,
    {
      initialValue: toPending<Album[]>(),
    },
  );

  ngOnInit(): void {
    this.subscription.add(
      this.album$.subscribe((album: Album) => {
        album.childAlbumIds.forEach((childAlbumId: string) => {
          this.store.dispatch(
            albumsActions.loadAlbumDetails({ albumId: childAlbumId }),
          );
        });
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
