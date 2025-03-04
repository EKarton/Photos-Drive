import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AlbumsListTableComponent } from './albums-list-table.component';

describe('AlbumsListTableComponent', () => {
  let component: AlbumsListTableComponent;
  let fixture: ComponentFixture<AlbumsListTableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumsListTableComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(AlbumsListTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
