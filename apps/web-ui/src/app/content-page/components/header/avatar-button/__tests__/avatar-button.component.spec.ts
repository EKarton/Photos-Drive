import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AvatarButtonComponent } from '../avatar-button.component';

describe('AvatarButtonComponent', () => {
  let component: AvatarButtonComponent;
  let fixture: ComponentFixture<AvatarButtonComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AvatarButtonComponent],
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

    expect(fixture.nativeElement.querySelector('.signout-button')).toBeTruthy();
  });

  it('should close dropdown menu when user clicks on the profile picture again', () => {
    const button = fixture.nativeElement.querySelector('button');
    button.click();
    fixture.detectChanges();

    const element = fixture.nativeElement.querySelector('a');
    expect(element.textContent).toContain('Sign out');
    button.click();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.signout-button')).toBeNull();
  });
});
