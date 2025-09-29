import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';

import { environment } from '../../environments/environment';
import { WINDOW } from '../app.tokens';
import { ThemeToggleButtonComponent } from '../themes/components/theme-toggle-button/theme-toggle-button.component';

@Component({
  selector: 'app-home-page',
  imports: [CommonModule, ThemeToggleButtonComponent],
  templateUrl: './home-page.component.html',
})
export class HomePageComponent {
  private readonly window: Window = inject(WINDOW);

  handleLoginClick() {
    this.window.location.href = `${environment.loginUrl}?select_account=true`;
  }
}
