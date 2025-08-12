import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Reasoning } from '../../../store/chats/chats.state';
import { ReasoningCollapseComponent } from '../reasoning-collapse.component';

describe('ReasoningCollapseComponent', () => {
  let fixture: ComponentFixture<ReasoningCollapseComponent>;
  let mockReasonings: Reasoning[];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReasoningCollapseComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ReasoningCollapseComponent);

    mockReasonings = [
      { id: '1', content: 'Reason 1' },
      { id: '2', content: 'Reason 2' },
    ];
  });

  it('should show toggle button and be closed by default', () => {
    fixture.componentRef.setInput('reasonings', mockReasonings);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    expect(button).toBeTruthy();
    expect(button.nativeElement.textContent).toContain('Show Reasoning');

    expect(
      fixture.nativeElement.querySelectorAll(
        '[data-testid="reasoning-content"]',
      ).length,
    ).toBe(0);
  });

  it('should open and display reasonings after clicking toggle', () => {
    fixture.componentRef.setInput('reasonings', mockReasonings);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    button.nativeElement.click();
    fixture.detectChanges();

    const paragraphs = fixture.nativeElement.querySelectorAll(
      '[data-testid="reasoning-content"]',
    );
    expect(paragraphs.length).toBe(2);
    expect(paragraphs[0].nativeElement.textContent).toContain('Reason 1');
    expect(paragraphs[1].nativeElement.textContent).toContain('Reason 2');
  });

  it('should close again after clicking toggle twice', () => {
    fixture.componentRef.setInput('reasonings', mockReasonings);
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector('button');
    button.nativeElement.click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelectorAll(
        '[data-testid="reasoning-content"]',
      ).length,
    ).toBe(2);

    button.nativeElement.click();
    fixture.detectChanges();

    expect(
      fixture.nativeElement.querySelectorAll(
        '[data-testid="reasoning-content"]',
      ).length,
    ).toBe(0);
  });
});
