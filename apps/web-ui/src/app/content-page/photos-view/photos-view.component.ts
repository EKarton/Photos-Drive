import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { HasFailedPipe } from '../../shared/results/pipes/has-failed.pipe';
import { IsPendingPipe } from '../../shared/results/pipes/is-pending.pipe';

@Component({
  standalone: true,
  selector: 'app-photos-view',
  imports: [CommonModule, IsPendingPipe, HasFailedPipe],
  templateUrl: './photos-view.component.html',
})
export class PhotosViewComponent {}
