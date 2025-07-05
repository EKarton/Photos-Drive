import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';

import { WINDOW } from '../../../../../app.tokens';
import { authState } from '../../../../../auth/store';
import { AvatarButtonComponent } from '../avatar-button.component';

describe('AvatarButtonComponent', () => {
  let component: AvatarButtonComponent;
  let fixture: ComponentFixture<AvatarButtonComponent>;
  let windowMock: {
    localStorage: { removeItem: jasmine.Spy };
    location: { href: string; pathname: string };
  };

  beforeEach(async () => {
    windowMock = {
      localStorage: {
        removeItem: jasmine.createSpy('removeItem'),
      },
      location: {
        href: '',
        pathname: '/content/home',
      },
    };

    await TestBed.configureTestingModule({
      imports: [AvatarButtonComponent],
      providers: [
        provideMockStore({
          selectors: [
            {
              selector: authState.selectUserProfileUrl,
              value: 'http://profile.com/1',
            },
          ],
        }),
        { provide: WINDOW, useValue: windowMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AvatarButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render component correctly', () => {
    expect(component).toBeTruthy();
  });

  it('should show dropdown menu when user clicks on the profile picture', () => {
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector('[data-testid="signout-button"]'),
    ).toBeTruthy();
  });

  it('should close dropdown menu when user clicks on the profile picture again', () => {
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector('[data-testid="signout-button"]'),
    ).toBeTruthy();
    button.click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelector('[data-testid="signout-button"]'),
    ).toBeNull();
  });

  it('should clear local storage, redirect user to home page, and close dropdown menu when user clicks on the profile picture again', () => {
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    fixture.detectChanges();

    const element = fixture.nativeElement.querySelector(
      '[data-testid="signout-button"]',
    );
    element.click();
    fixture.detectChanges();

    expect(windowMock.localStorage.removeItem).toHaveBeenCalledWith(
      'auth_redirect_path',
    );
    expect(windowMock.location.href).toEqual('#');
    expect(
      fixture.nativeElement.querySelector('[data-testid="signout-button"]'),
    ).toBeNull();
  });
});
