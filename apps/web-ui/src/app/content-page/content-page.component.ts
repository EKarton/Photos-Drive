import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

import { AlbumsViewComponent } from './albums-view/albums-view.component';
import { HeaderComponent } from './albums-view/header/header.component';
import { MediaViewerComponent } from './albums-view/media-viewer/media-viewer.component';

@Component({
  standalone: true,
  selector: 'app-content-page',
  imports: [
    CommonModule,
    HeaderComponent,
    AlbumsViewComponent,
    MediaViewerComponent,
  ],
  templateUrl: './content-page.component.html',
})
export class ContentPageComponent {}
