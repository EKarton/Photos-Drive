import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AlbumsListCardsComponent } from './albums-list-cards/albums-list-cards.component';
import { AlbumsListTableComponent } from './albums-list-table/albums-list-table.component';

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
})
export class AlbumsListComponent {
  readonly albumId = input.required<string>();

  isTableViewChecked = false;
}
