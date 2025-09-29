import { CommonModule } from '@angular/common';
import { Component, HostListener, inject } from '@angular/core';

import { environment } from '../../environments/environment';
import { WINDOW } from '../app.tokens';
import { ThemeToggleButtonComponent } from '../themes/components/theme-toggle-button/theme-toggle-button.component';

@Component({
  selector: 'app-home-page',
  imports: [CommonModule, ThemeToggleButtonComponent],
  templateUrl: './home-page.component.html',
  styleUrl: './home-page.component.scss',
})
export class HomePageComponent {
  private readonly window: Window = inject(WINDOW);

  scrolled = false;

  @HostListener('window:scroll', [])
  onWindowScroll() {
    this.scrolled = window.scrollY > 50; // toggle when scrolled more than 50px
  }

  handleLoginClick() {
    this.window.location.href = `${environment.loginUrl}?select_account=true`;
  }
}
