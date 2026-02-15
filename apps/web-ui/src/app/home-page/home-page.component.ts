import { CommonModule } from '@angular/common';
import {
  Component,
  HostListener,
  inject,
  OnDestroy,
  signal,
} from '@angular/core';
import { Subscription } from 'rxjs';

import { WINDOW } from '../app.tokens';
import { WebApiService } from '../auth/services/webapi.service';
import { hasSucceed } from '../shared/results/results';
import { ThemeToggleButtonComponent } from '../themes/components/theme-toggle-button/theme-toggle-button.component';

interface GetGoogleLoginUrlResponse {
  url: string;
}

@Component({
  selector: 'app-home-page',
  imports: [CommonModule, ThemeToggleButtonComponent],
  templateUrl: './home-page.component.html',
})
export class HomePageComponent implements OnDestroy {
  private readonly webApiService = inject(WebApiService);
  private readonly window: Window = inject(WINDOW);
  private readonly subscriptions = new Subscription();

  readonly isScrolled = signal(false);

  @HostListener('window:scroll', [])
  onScroll() {
    this.isScrolled.set(this.window.pageYOffset > 50);
  }

  handleLoginClick() {
    this.subscriptions.add(
      this.webApiService.getGoogleLoginUrl().subscribe((res) => {
        if (hasSucceed(res)) {
          this.window.location.href = res.data!.url;
        }
      }),
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }
}
