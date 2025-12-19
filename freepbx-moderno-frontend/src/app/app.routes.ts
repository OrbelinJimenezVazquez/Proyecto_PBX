// src/app/app.routes.ts
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { ExtensionsComponent } from './extensions/extensions';
import { CallsComponent } from './calls/calls';
import { TrunksComponent } from './trunks/trunks';

export const routes: Routes = [
  { path: '', redirectTo: '/extensions', pathMatch: 'full' },
  { path: 'extensions', component: ExtensionsComponent },
  { path: 'calls', component: CallsComponent },
  { path: 'trunks', component: TrunksComponent } 
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }