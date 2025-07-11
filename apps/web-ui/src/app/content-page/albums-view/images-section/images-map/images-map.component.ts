import { CommonModule } from '@angular/common';
import { Component, input } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  standalone: true,
  selector: 'app-content-images-map',
  imports: [CommonModule, FormsModule],
  templateUrl: './images-map.component.html',
})
export class ImagesMapComponent {
  readonly albumId = input.required<string>();
}
