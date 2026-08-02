import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Params, Router } from '@angular/router';
import { MockStore, provideMockStore } from '@ngrx/store/testing';
import { Map as ImmutableMap } from 'immutable';
import { BehaviorSubject } from 'rxjs';

import { WINDOW } from '../../../app.tokens';
import { authActions, authState } from '../../store';
import { CallbackPageComponent } from '../callback-page.component';

describe('CallbackPageComponent', () => {
  let router: jasmine.SpyObj<Router>;
  let mockLocalStorageGetItem: jasmine.Spy;
  let mockSessionStorageGetItem: jasmine.Spy;
  let queryParamMapSubject: BehaviorSubject<Params>;

  beforeEach(() => {
    mockLocalStorageGetItem = jasmine.createSpy('getItem');
    mockSessionStorageGetItem = jasmine.createSpy('getItem');

    router = jasmine.createSpyObj('Router', ['navigate']);
    queryParamMapSubject = new BehaviorSubject({
      code: 'test-auth-code',
      state: 'test-state',
    } as Params);

    TestBed.configureTestingModule({
      imports: [CallbackPageComponent],
      providers: [
        { provide: Router, useValue: router },
        {
          provide: ActivatedRoute,
          useValue: {
            queryParamMap: queryParamMapSubject.asObservable(),
          },
        },
        provideMockStore({
          selectors: [{ selector: authState.selectAuthToken, value: '' }],
        }),
        {
          provide: WINDOW,
          useValue: {
            localStorage: {
              getItem: mockLocalStorageGetItem,
            },
            sessionStorage: {
              getItem: mockSessionStorageGetItem,
              removeItem: jasmine.createSpy('removeItem'),
            },
          },
        },
      ],
    }).compileComponents();
  });

  it('should dispatch auth.loadAuth action given valid code and state', () => {
    const store = TestBed.inject(MockStore);
    spyOn(store, 'dispatch');
    mockSessionStorageGetItem.and.returnValue('test-state');
    queryParamMapSubject.next(
      ImmutableMap({ code: 'test-auth-code', state: 'test-state' }),
    );

    const fixture = TestBed.createComponent(CallbackPageComponent);
    fixture.detectChanges();

    expect(store.dispatch).toHaveBeenCalledWith(
      authActions.loadAuth({ code: 'test-auth-code' }),
    );
  });

  it('should navigate to redirect path when auth token is available', () => {
    const store = TestBed.inject(MockStore);
    store.overrideSelector(authState.selectAuthToken, 'mockAccessToken');

    const fixture = TestBed.createComponent(CallbackPageComponent);
    fixture.detectChanges();

    expect(router.navigate).toHaveBeenCalledWith(['/albums/root']);
  });

  it('should navigate to custom redirect path if set in localStorage', () => {
    const store = TestBed.inject(MockStore);
    store.overrideSelector(authState.selectAuthToken, 'mockAccessToken');
    mockLocalStorageGetItem.and.returnValue('/custom/path');

    const fixture = TestBed.createComponent(CallbackPageComponent);
    fixture.detectChanges();

    expect(router.navigate).toHaveBeenCalledWith(['/custom/path']);
  });

  it('should not navigate if auth token is empty', () => {
    const store = TestBed.inject(MockStore);
    store.overrideSelector(authState.selectAuthToken, '');

    const fixture = TestBed.createComponent(CallbackPageComponent);
    fixture.detectChanges();

    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('should navigate to / if oauth state mismatch', () => {
    mockSessionStorageGetItem.and.returnValue('different-state');
    queryParamMapSubject.next(
      ImmutableMap({ code: 'test-auth-code', state: 'test-state' }),
    );

    const fixture = TestBed.createComponent(CallbackPageComponent);
    fixture.detectChanges();

    expect(router.navigate).toHaveBeenCalledWith(['/']);
  });
});
