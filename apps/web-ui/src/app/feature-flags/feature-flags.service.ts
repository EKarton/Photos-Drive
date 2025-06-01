import { Injectable } from '@angular/core';
import { NavigationEnd, ParamMap, Router } from '@angular/router';
import { BehaviorSubject } from 'rxjs';
import { filter, map } from 'rxjs/operators';

/** Defines all of the feature flags. */
export enum FeatureFlags {
  NewImagesListView = 'new_images_list_view_flag',
}

@Injectable({ providedIn: 'root' })
export class FeatureFlagsService {
  private flags = new Map<FeatureFlags, boolean>();
  private flags$ = new BehaviorSubject<Map<FeatureFlags, boolean>>(this.flags);

  constructor(private router: Router) {
    this.router.events
      .pipe(
        filter((event) => event instanceof NavigationEnd),
        map(() => this.router.routerState.root.snapshot.queryParamMap),
      )
      .subscribe((params) => this.updateFlags(params));

    // Initial flag update on service creation
    this.updateFlags(this.router.routerState.root.snapshot.queryParamMap);
  }

  private updateFlags(params: ParamMap): void {
    this.flags.clear();

    Object.values(FeatureFlags).forEach((flagKey) => {
      const value = params.get(flagKey);
      this.flags.set(flagKey, value?.toLowerCase() === 'true');
    });

    this.flags$.next(this.flags);
  }

  isEnabled(flag: FeatureFlags): boolean {
    return this.flags.get(flag) === true;
  }

  getFlagsObservable() {
    return this.flags$.asObservable();
  }
}
