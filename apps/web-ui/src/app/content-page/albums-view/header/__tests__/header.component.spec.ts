import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideMockStore } from '@ngrx/store/testing';

import { authState } from '../../../../auth/store';
import { themeState } from '../../../../themes/store';
import { HeaderComponent } from '../header.component';

describe('HeaderComponent', () => {
  let component: HeaderComponent;
  let fixture: ComponentFixture<HeaderComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [
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

  it('should be truthy when user clicks on Albums tab', () => {
    fixture.nativeElement.querySelector('[data-testid="albums-tab"]').click();
    fixture.detectChanges();

    expect(component).toBeTruthy();
  });

  it('should be truthy when user clicks on Photos tab', () => {
    fixture.nativeElement.querySelector('[data-testid="photos-tab"]').click();
    fixture.detectChanges();

    expect(component).toBeTruthy();
  });
});
