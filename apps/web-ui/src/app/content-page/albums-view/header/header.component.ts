import { Component } from '@angular/core';

import { ThemeToggleButtonComponent } from '../../../themes/components/theme-toggle-button/theme-toggle-button.component';
import { AvatarButtonComponent } from './avatar-button/avatar-button.component';

@Component({
  standalone: true,
  selector: 'app-content-header',
  imports: [ThemeToggleButtonComponent, AvatarButtonComponent],
  templateUrl: './header.component.html',
})
export class HeaderComponent {}
