import {
  ComponentFixture,
  fakeAsync,
  TestBed,
  tick,
} from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideMockStore } from '@ngrx/store/testing';

import { authState } from '../../../auth/store';
import { themeState } from '../../../themes/store';
import { routes } from '../../content-page.routes';
import { HeaderComponent } from '../header.component';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideRouter(routes),
        provideMockStore({
          selectors: [
            { selector: themeState.selectIsDarkMode, value: false },
            {
              selector: authState.selectUserProfileUrl,
              value: 'http://profile.com/1',
            },
          ],
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    router = TestBed.inject(Router);
    router.navigateByUrl('/albums/1234');
  });

  it('should render component', () => {
    expect(component).toBeTruthy();
  });

  it('should open hamburger menu when the hamburger menu button is clicked', () => {
    fixture.nativeElement
      .querySelector('[data-testid="hamburger-menu-button"]')
      .click();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('aside')).toBeTruthy();
  });

  it('should close the hamburger menu when the close button is clicked, given menu is open', () => {
    fixture.nativeElement
      .querySelector('[data-testid="hamburger-menu-button"]')
      .click();
    fixture.detectChanges();

    fixture.nativeElement
      .querySelector('[data-testid="close-sidepanel-button"]')
      .click();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('aside')).toBeNull();
  });

  it('should highlight the Albums tab when the user is on the /albums/:albumId route', () => {
    router.navigateByUrl('/albums/1234');
    fixture.detectChanges();

    expect(
      fixture.nativeElement
        .querySelector('[data-testid="albums-tab"]')
        .classList.contains('tab-active'),
    ).toBeTrue();
    expect(
      fixture.nativeElement
        .querySelector('[data-testid="photos-tab"]')
        .classList.contains('tab-active'),
    ).toBeFalse();
  });

  it('should highlight the Photos tab when the user is on the /photos route', fakeAsync(() => {
    router.navigateByUrl('/photos');
    fixture.detectChanges();
    tick();
    fixture.detectChanges();

    expect(
      fixture.nativeElement
        .querySelector('[data-testid="albums-tab"]')
        .classList.contains('tab-active'),
    ).toBeFalse();
    expect(
      fixture.nativeElement
        .querySelector('[data-testid="photos-tab"]')
        .classList.contains('tab-active'),
    ).toBeTrue();
  }));
});
