import { CommonModule } from '@angular/common';
import { Component, input, signal, WritableSignal } from '@angular/core';

import {
  ListMediaItemsSortBy,
  ListMediaItemsSortByFields,
  ListMediaItemsSortDirection,
} from '../../services/types/list-media-items';
import { ImagesListComponent } from './images-list/images-list.component';
import { ImagesSortDropdownComponent } from './images-sort-dropdown/images-sort-dropdown.component';

@Component({
  standalone: true,
  selector: 'app-content-images-section',
  imports: [CommonModule, ImagesListComponent, ImagesSortDropdownComponent],
  templateUrl: './images-section.component.html',
})
export class ImagesSectionComponent {
  readonly albumId = input.required<string>();

  readonly imagesSortBy: WritableSignal<ListMediaItemsSortBy> = signal({
    field: ListMediaItemsSortByFields.DATE_TAKEN,
    direction: ListMediaItemsSortDirection.ASCENDING,
  });
}
