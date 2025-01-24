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
import {
  BehaviorSubject,
  combineLatest,
  Observable,
  Subscription,
  switchMap,
} from 'rxjs';

import { HasFailedPipe } from '../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../../../shared/results/results';
import { mapResultRxJs } from '../../../shared/results/rxjs/mapResultRxJs';
import { Album } from '../../services/webapi.service';
import { albumsActions, albumsState } from '../../store/albums';
import { ImagesListComponent } from './images-list/images-list.component';

@Component({
  standalone: true,
  selector: 'app-content-images-section',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe, ImagesListComponent],
  templateUrl: './images-section.component.html',
})
export class ImagesSectionComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private subscription = new Subscription();

  readonly albumId = input.required<string>();
  private readonly albumId$ = toObservable(this.albumId);

  private readonly pageSize = 5;
  private currentPage$ = new BehaviorSubject(1);

  private readonly mediaItemIdsResult$: Observable<Result<string[]>> =
    combineLatest([this.albumId$, this.currentPage$]).pipe(
      switchMap(([albumId, currentPage]) =>
        this.store.select(albumsState.selectAlbumDetailsById(albumId)).pipe(
          mapResultRxJs((album: Album) => {
            const startIndex = (currentPage - 1) * this.pageSize;
            const endIndex = startIndex + this.pageSize;
            return album.mediaItemIds.slice(startIndex, endIndex);
          }),
        ),
      ),
    );

  readonly mediaItemIdsResult: Signal<Result<string[]>> = toSignal(
    this.mediaItemIdsResult$,
    {
      initialValue: toPending<string[]>(),
    },
  );

  ngOnInit(): void {
    // Fetch the album details
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
