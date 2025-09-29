import { ComponentFixture, TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { WINDOW } from '../../app.tokens';
import { HomePageComponent } from '../home-page.component';

describe('HomePageComponent', () => {
  let component: HomePageComponent;
  let fixture: ComponentFixture<HomePageComponent>;
  let mockWindow: Window;

  beforeEach(async () => {
    mockWindow = { location: { href: '' } } as Window;

    await TestBed.configureTestingModule({
      imports: [HomePageComponent],
      providers: [
        {
          provide: WINDOW,
          useValue: mockWindow,
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomePageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create component', () => {
    expect(component).toBeTruthy();
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
