import { CommonModule } from '@angular/common';
import { Component, inject, OnDestroy, OnInit, Signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { Store } from '@ngrx/store';
import { map, Observable, Subscription, switchMap } from 'rxjs';

import { HasFailedPipe } from '../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../shared/results/pipes/is-pending.pipe';
import { Result, toPending } from '../shared/results/results';
import { AlbumsListComponent } from './components/albums-list/albums-list.component';
import { BreadcrumbsComponent } from './components/breadcrumbs/breadcrumbs.component';
import { HeaderComponent } from './components/header/header.component';
import { ImagesSectionComponent } from './components/images-section/images-section.component';
import { MediaViewerComponent } from './components/media-viewer/media-viewer.component';
import { Album } from './services/albums';
import { albumsActions, albumsState } from './store/albums';

@Component({
  standalone: true,
  selector: 'app-content-page',
  imports: [
    CommonModule,
    HeaderComponent,
    IsPendingPipe,
    HasFailedPipe,
    AlbumsListComponent,
    ImagesSectionComponent,
    BreadcrumbsComponent,
    MediaViewerComponent,
  ],
  templateUrl: './content-page.component.html',
})
export class ContentPageComponent implements OnInit, OnDestroy {
  private readonly store = inject(Store);
  private readonly route = inject(ActivatedRoute);
  private readonly subscription = new Subscription();

  readonly albumId$ = this.route.paramMap.pipe(
    map((params) => params.get('albumId')!),
  );
  readonly albumId: Signal<string> = toSignal(this.albumId$, {
    initialValue: 'root',
  });

  readonly albumResult$: Observable<Result<Album>> = this.albumId$.pipe(
    switchMap((albumId) =>
      this.store.select(albumsState.selectAlbumDetailsById(albumId)),
    ),
  );
  readonly albumResult: Signal<Result<Album>> = toSignal(this.albumResult$, {
    initialValue: toPending<Album>(),
  });

  ngOnInit() {
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
