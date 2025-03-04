import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { RouterModule } from '@angular/router';

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import { Result } from '../../../../shared/results/results';
import { Album } from '../../../services/webapi.service';

@Component({
  selector: 'app-content-albums-list-cards',
  imports: [CommonModule, RouterModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './albums-list-cards.component.html',
})
export class AlbumsListCardsComponent {
  readonly albums = input.required<Result<Album>[]>();
}
