import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';

import { ThemeToggleButtonComponent } from '../../../themes/components/theme-toggle-button/theme-toggle-button.component';
import { AvatarButtonComponent } from './avatar-button/avatar-button.component';

enum Tabs {
  ALBUMS = 'albums',
  PHOTOS = 'photos',
}

@Component({
  standalone: true,
  selector: 'app-content-header',
  imports: [CommonModule, ThemeToggleButtonComponent, AvatarButtonComponent],
  templateUrl: './header.component.html',
})
export class HeaderComponent {
  readonly isSidebarOpen = signal(false);
  readonly selectedTab = signal(Tabs.ALBUMS);

  readonly Tabs = Tabs;

  selectTab(tab: Tabs) {
    this.selectedTab.set(tab);
    this.isSidebarOpen.set(false);
  }

  openSideBar() {
    this.isSidebarOpen.set(true);
  }

  closeSideBar() {
    this.isSidebarOpen.set(false);
  }
}
