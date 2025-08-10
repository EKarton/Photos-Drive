import {
  ComponentFixture,
  fakeAsync,
  TestBed,
  tick,
} from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideRouter, Router } from '@angular/router';
import { provideStore } from '@ngrx/store';
import { provideMockStore } from '@ngrx/store/testing';

import { authState } from '../../../auth/store';
import { themeState } from '../../../themes/store';
import { routes } from '../../content-page.routes';
import { WebApiService } from '../../services/web-api/web-api.service';
import { albumsState } from '../../store/albums';
import { dialogsState } from '../../store/dialogs';
import { HeaderComponent } from '../header.component';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;
  let router: Router;

  beforeEach(async () => {
    const mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'listMediaItems',
      'listAlbums',
    ]);

    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
        provideRouter(routes),
        provideStore({}),
        provideMockStore({
          initialState: {
            [albumsState.FEATURE_KEY]: albumsState.buildInitialState(),
            [dialogsState.FEATURE_KEY]: dialogsState.initialState,
            [themeState.FEATURE_KEY]: themeState.initialState,
            [authState.FEATURE_KEY]: authState.buildInitialState(),
          },
        }),
        {
          provide: WebApiService,
          useValue: mockWebApiService,
        },
        provideNoopAnimations(),
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
