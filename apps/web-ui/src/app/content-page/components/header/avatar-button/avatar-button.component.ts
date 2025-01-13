import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Store } from '@ngrx/store';
import { NgClickOutsideDirective } from 'ng-click-outside2';

import { authState } from '../../../../auth/store';

const DEFAULT_PROFILE_URL =
  'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80';

@Component({
  standalone: true,
  selector: 'app-header-avatar-button',
  imports: [CommonModule, NgClickOutsideDirective],
  templateUrl: './avatar-button.component.html',
})
export class AvatarButtonComponent {
  private readonly store = inject(Store);

  readonly isDropdownVisible = signal(false);
  readonly profileUrl =
    this.store.selectSignal(authState.selectUserProfileUrl) ||
    DEFAULT_PROFILE_URL;

  toggleDropdown() {
    this.isDropdownVisible.set(!this.isDropdownVisible());
  }

  closeDropdown() {
    this.isDropdownVisible.set(false);
  }
}
