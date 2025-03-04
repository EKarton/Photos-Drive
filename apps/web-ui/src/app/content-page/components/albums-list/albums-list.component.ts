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
import { FormsModule } from '@angular/forms';
import { Store } from '@ngrx/store';
import { combineLatest, Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../shared/results/results';
import { filterOnlySuccess } from '../../../shared/results/rxjs/filterOnlySuccess';
import { Album } from '../../services/webapi.service';
import { albumsActions, albumsState } from '../../store/albums';
import { AlbumsListCardsComponent } from './albums-list-cards/albums-list-cards.component';
import { AlbumsListTableComponent } from './albums-list-table/albums-list-table.component';

@Component({
  standalone: true,
  selector: 'app-content-albums-list',
  imports: [
    CommonModule,
    FormsModule,
    IsPendingPipe,
    HasFailedPipe,
    AlbumsListCardsComponent,
    AlbumsListTableComponent,
  ],
  templateUrl: './albums-list.component.html',
})
export class AlbumsListComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly album$ = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly album: Signal<Result<Album>> = toSignal(this.album$, {
    initialValue: toPending<Album>(),
  });

  isTableViewChecked = false;

  private readonly childAlbums$ = this.album$.pipe(
    filterOnlySuccess(),
    switchMap((curAlbum: Album) => {
      return combineLatest(
        curAlbum.childAlbumIds.map((childAlbumId: string) => {
          return this.store.select(
            albumsState.selectAlbumDetailsById(childAlbumId),
          );
        }),
      );
    }),
  );

  readonly childAlbums: Signal<Result<Album>[]> = toSignal(this.childAlbums$, {
    initialValue: [],
  });

  ngOnInit(): void {
    this.subscription.add(
      this.albumId$.subscribe((albumId) => {
        this.store.dispatch(albumsActions.loadAlbumDetails({ albumId }));
      }),
    );

    this.subscription.add(
      this.album$.pipe(filterOnlySuccess()).subscribe((album: Album) => {
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
