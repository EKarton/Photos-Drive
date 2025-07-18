import { Routes } from '@angular/router';

import { AlbumsViewComponent } from './albums-view/albums-view.component';
import { ContentPageComponent } from './content-page.component';
import { PhotosViewComponent } from './photos-view/photos-view.component';

export const routes: Routes = [
  {
    path: '',
    component: ContentPageComponent,
    children: [
      { path: 'albums/:albumId', component: AlbumsViewComponent },
      { path: 'photos', component: PhotosViewComponent },
      { path: '', pathMatch: 'full', redirectTo: 'photos' },
    ],
  },
];
