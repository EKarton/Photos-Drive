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
import { Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../shared/results/results';
import { Album } from '../../services/webapi.service';
import { albumsActions, albumsState } from '../../store/albums';
import { AlbumCardComponent } from './album-card/album-card.component';

@Component({
  standalone: true,
  selector: 'app-content-albums-list',
  imports: [
    CommonModule,
    RouterModule,
    IsPendingPipe,
    HasFailedPipe,
    AlbumCardComponent,
  ],
  templateUrl: './albums-list.component.html',
})
export class AlbumsListComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly albumResults$ = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly albumResults: Signal<Result<Album>> = toSignal(this.albumResults$, {
    initialValue: toPending<Album>(),
  });

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
