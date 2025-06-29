import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  inject,
  input,
  Signal,
} from '@angular/core';
import { RouterModule } from '@angular/router';

import { HasFailedPipe } from '../../../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../../../shared/results/pipes/is-pending.pipe';
import { Result } from '../../../../shared/results/results';
import { Album } from '../../../services/types/album';
import { AlbumsListTableStore } from './albums-list-table.store';

@Component({
  standalone: true,
  selector: 'app-content-albums-list-table',
  imports: [CommonModule, RouterModule, HasFailedPipe, IsPendingPipe],
  templateUrl: './albums-list-table.component.html',
  providers: [AlbumsListTableStore],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlbumsListTableComponent {
  readonly albumId = input.required<string>();

  private readonly albumsListTableStore = inject(AlbumsListTableStore);

  readonly childAlbumsResult: Signal<Result<Album[]>> =
    this.albumsListTableStore.albumsResult;
}
