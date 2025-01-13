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
});
