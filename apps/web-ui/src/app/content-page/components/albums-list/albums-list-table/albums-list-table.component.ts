import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterModule } from '@angular/router';

import { Album } from '../../../services/types/album';

@Component({
  selector: 'app-content-albums-list-table',
  imports: [CommonModule, RouterModule],
  templateUrl: './albums-list-table.component.html',
})
export class AlbumsListTableComponent {
  readonly albums = input.required<Album[]>();
}
