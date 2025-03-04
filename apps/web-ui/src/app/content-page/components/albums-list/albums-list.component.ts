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
import { Store } from '@ngrx/store';
import { Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../shared/results/results';
import { Album } from '../../services/webapi.service';
import { albumsActions, albumsState } from '../../store/albums';
import { AlbumsListCardsComponent } from './albums-list-cards/albums-list-cards.component';
import { AlbumsListTableComponent } from './albums-list-table/albums-list-table.component';

@Component({
  standalone: true,
  selector: 'app-content-albums-list',
  imports: [
    CommonModule,
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

  private readonly curAlbumResults$ = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly albumResults: Signal<Result<Album>> = toSignal(
    this.curAlbumResults$,
    {
      initialValue: toPending<Album>(),
    },
  );

  ngOnInit(): void {
    this.subscription.add(
      this.albumId$.subscribe((albumId) => {
        this.store.dispatch(albumsActions.loadAlbumDetails({ albumId }));
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
