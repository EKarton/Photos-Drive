import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';
import { of } from 'rxjs';

import { environment } from '../../../environments/environment';
import { WINDOW } from '../../app.tokens';
import { WebApiService } from '../../auth/services/webapi.service';
import { toSuccess } from '../../shared/results/results';
import { themeState } from '../../themes/store';
import { HomePageComponent } from '../home-page.component';

describe('HomePageComponent', () => {
  let component: HomePageComponent;
  let fixture: ComponentFixture<HomePageComponent>;
  let mockWindow: Window;
  let mockWebApiService: jasmine.SpyObj<WebApiService>;

  beforeEach(async () => {
    mockWindow = { location: { href: '' }, pageYOffset: 0 } as Window;
    mockWebApiService = jasmine.createSpyObj('WebApiService', [
      'getGoogleLoginUrl',
    ]);

    mockWebApiService.getGoogleLoginUrl.and.returnValue(
      of(toSuccess({ url: `${environment.loginUrl}?select_account=true` })),
    );

    await TestBed.configureTestingModule({
      imports: [HomePageComponent],
      providers: [
        {
          provide: WINDOW,
          useValue: mockWindow,
        },
        {
          provide: WebApiService,
          useValue: mockWebApiService,
        },
        provideMockStore({
          initialState: {
            [themeState.FEATURE_KEY]: themeState.initialState,
          },
        }),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create component', () => {
    expect(component).toBeTruthy();
  });

  it('should have no shadow and bg-base-300 initially', () => {
    const header: HTMLElement = fixture.nativeElement.querySelector('header');

    expect(header.classList.contains('shadow-none')).toBeTrue();
    expect(header.classList.contains('bg-base-300')).toBeTrue();
    expect(header.classList.contains('shadow-md')).toBeFalse();
    expect(header.classList.contains('bg-base-200')).toBeFalse();
  });

  it('should add shadow and bg-base-200 when scrolled', () => {
    const header: HTMLElement = fixture.nativeElement.querySelector('header');

    // Simulate scroll down
    Object.defineProperty(mockWindow, 'pageYOffset', {
      configurable: true,
      get: () => 100,
    });
    window.dispatchEvent(new Event('scroll'));
    fixture.detectChanges();

    expect(header.classList.contains('shadow-md')).toBeTrue();
    expect(header.classList.contains('bg-base-200')).toBeTrue();
    expect(header.classList.contains('shadow-none')).toBeFalse();
    expect(header.classList.contains('bg-base-300')).toBeFalse();
  });

  it('should remove shadow and revert to bg-base-300 when scroll is at top', () => {
    const header: HTMLElement = fixture.nativeElement.querySelector('header');

    // Scroll down first
    Object.defineProperty(mockWindow, 'pageYOffset', {
      configurable: true,
      get: () => 100,
    });
    window.dispatchEvent(new Event('scroll'));
    fixture.detectChanges();

    // Scroll back to top
    Object.defineProperty(mockWindow, 'pageYOffset', {
      configurable: true,
      get: () => 0,
    });
    window.dispatchEvent(new Event('scroll'));
    fixture.detectChanges();

    expect(header.classList.contains('shadow-none')).toBeTrue();
    expect(header.classList.contains('bg-base-300')).toBeTrue();
    expect(header.classList.contains('shadow-md')).toBeFalse();
    expect(header.classList.contains('bg-base-200')).toBeFalse();
  });

  it('should redirect to login URL on handleLoginClick', () => {
    const button = fixture.nativeElement.querySelector(
      '[data-test-id="login-button"]',
    );
    button.click();

    const expectedHref = `${environment.loginUrl}?select_account=true`;
    expect(mockWindow.location.href).toBe(expectedHref);
  });
});
