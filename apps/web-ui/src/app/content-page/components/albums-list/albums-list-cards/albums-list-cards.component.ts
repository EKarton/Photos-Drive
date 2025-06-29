import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterModule } from '@angular/router';

import { Album } from '../../../services/types/album';

@Component({
  selector: 'app-content-albums-list-cards',
  imports: [CommonModule, RouterModule],
  templateUrl: './albums-list-cards.component.html',
})
export class AlbumsListCardsComponent {
  readonly albums = input.required<Album[]>();
}
