import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { NgClickOutsideDirective } from 'ng-click-outside2';

import { authState } from '../../../../auth/store';

@Component({
  standalone: true,
  selector: 'app-header-avatar-button',
  imports: [CommonModule, NgClickOutsideDirective],
  templateUrl: './avatar-button.component.html',
})
export class AvatarButtonComponent {
  private readonly store = inject(Store);

  readonly isDropdownVisible = signal(false);
  readonly profileUrl = this.store.selectSignal(authState.selectUserProfileUrl);

  toggleDropdown() {
    this.isDropdownVisible.set(!this.isDropdownVisible());
  }

  closeDropdown() {
    this.isDropdownVisible.set(false);
  }
}
