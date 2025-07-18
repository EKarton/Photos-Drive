import { Routes } from '@angular/router';

import { AlbumsViewComponent } from './albums-view/albums-view.component';
import { ContentPageComponent } from './content-page.component';
import { ImagesViewComponent } from './images-view/images-view.component';

export const routes: Routes = [
  {
    path: '',
    component: ContentPageComponent,
    children: [
      { path: 'albums/:albumId', component: AlbumsViewComponent },
      { path: 'photos', component: ImagesViewComponent },
      { path: '', pathMatch: 'full', redirectTo: 'photos' },
    ],
  },
];
