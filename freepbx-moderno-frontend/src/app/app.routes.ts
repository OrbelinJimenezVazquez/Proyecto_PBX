// src/app/app.routes.ts
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './dashboard/dashboard';
import { ExtensionsComponent } from './extensions/extensions';
import { CallsComponent } from './calls/calls';
import { TrunksComponent } from './trunks/trunks';
import { IvrComponent } from './ivr/ivr';
import { IncomingRoutesComponent } from './incoming-routes/incoming-routes';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  {path: 'incoming-routes', component: IncomingRoutesComponent},
  { path: 'extensions', component: ExtensionsComponent },
  { path: 'calls', component: CallsComponent },
  { path: 'trunks', component: TrunksComponent },
  {path: 'ivr', component: IvrComponent},
];
  
@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }