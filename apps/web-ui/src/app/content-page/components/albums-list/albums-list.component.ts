import { CommonModule } from '@angular/common';
import { Component, effect, inject, input, Signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { Album } from '../../services/types/album';
import { AlbumsListStore } from './albums-list.store';
import { AlbumsListCardsComponent } from './albums-list-cards/albums-list-cards.component';
import { AlbumsListTableComponent } from './albums-list-table/albums-list-table.component';

const DEFAULT_PAGE_SIZE = 500;

@Component({
  standalone: true,
  selector: 'app-content-albums-list',
  imports: [
    CommonModule,
    FormsModule,
    AlbumsListCardsComponent,
    AlbumsListTableComponent,
  ],
  templateUrl: './albums-list.component.html',
  providers: [AlbumsListStore],
})
export class AlbumsListComponent {
  readonly albumId = input.required<string>();
  isTableViewChecked = false;

  private readonly albumsListStore = inject(AlbumsListStore);

  readonly childAlbums: Signal<Album[]> = this.albumsListStore.albums;

  constructor() {
    effect(() => {
      this.albumsListStore.loadInitialPage({
        albumId: this.albumId(),
        pageSize: DEFAULT_PAGE_SIZE,
      });
    });
  }
}
