import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { MediaViewerComponent } from './albums-view/media-viewer/media-viewer.component';
import { HeaderComponent } from './header/header.component';

@Component({
  standalone: true,
  selector: 'app-content-page',
  imports: [CommonModule, HeaderComponent, MediaViewerComponent, RouterOutlet],
  templateUrl: './content-page.component.html',
})
export class ContentPageComponent {}
