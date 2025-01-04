import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { NgClickOutsideDirective } from 'ng-click-outside2';
import { getCookie } from 'typescript-cookie';

const DEFAULT_PROFILE_URL =
  'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80';

@Component({
  standalone: true,
  selector: 'app-header-avatar-button',
  imports: [CommonModule, NgClickOutsideDirective],
  templateUrl: './avatar-button.component.html',
})
export class AvatarButtonComponent {
  readonly isDropdownVisible = signal(false);
  readonly profileUrl = signal(
    getCookie('user_profile_url') || DEFAULT_PROFILE_URL,
  );

  toggleDropdown() {
    this.isDropdownVisible.set(!this.isDropdownVisible());
  }

  closeDropdown() {
    this.isDropdownVisible.set(false);
  }
}
