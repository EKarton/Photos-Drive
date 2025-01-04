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

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../../shared/results/results';
import { Album } from '../../../services/webapi.service';
import { albumsActions, albumsState } from '../../../store/albums';

@Component({
  selector: 'app-content-album-card',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './album-card.component.html',
  styleUrl: './album-card.component.scss',
})
export class AlbumCardComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly albumDetails$ = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly albumDetails: Signal<Result<Album>> = toSignal(this.albumDetails$, {
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
