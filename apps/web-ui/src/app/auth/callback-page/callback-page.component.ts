import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { filter, map, Subscription } from 'rxjs';

import { filterOnlySuccess } from '../../shared/results/rxjs/filterOnlySuccess';
import { authActions, authState } from '../store';

@Component({
  selector: 'app-callback-page',
  imports: [],
  templateUrl: './callback-page.component.html',
  styleUrl: './callback-page.component.scss',
})
export class CallbackPageComponent implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly store = inject(Store);
  private readonly subscription = new Subscription();

  readonly code$ = this.route.queryParamMap.pipe(
    map((params) => params.get('code')!),
  );

  ngOnInit(): void {
    this.subscription.add(
      this.code$.subscribe((code) => {
        this.store.dispatch(authActions.loadAuth({ code }));
      }),
    );

    this.subscription.add(
      this.store
        .select(authState.selectAuthToken)
        .pipe(filter((accessToken) => accessToken.length > 0))
        .subscribe(() => {
          this.router.navigate(['/content/root']);
        }),
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
