import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';

import { ImagesListComponent } from './images-list/images-list.component';

@Component({
  standalone: true,
  selector: 'app-content-images-section',
  imports: [CommonModule, ImagesListComponent],
  templateUrl: './images-section.component.html',
})
export class ImagesSectionComponent {
  readonly albumId = input.required<string>();
}
