import { Component, inject } from '@angular/core';

import { environment } from '../../environments/environment';
import { WINDOW } from '../app.tokens';

@Component({
  selector: 'app-home-page',
  imports: [],
  templateUrl: './home-page.component.html',
  styleUrl: './home-page.component.scss',
})
export class HomePageComponent {
  private readonly window: Window = inject(WINDOW);

  handleLoginClick() {
    this.window.location.href = environment.loginUrl;
  }
}
