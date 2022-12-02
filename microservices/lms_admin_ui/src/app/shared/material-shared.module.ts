import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';

// import { MatMomentDateModule } from "@angular/material-moment-adapter";

@NgModule({
    declarations: [
    ],
    imports: [
        CommonModule
    ],
    exports: [
        MatMenuModule,
        MatButtonModule,
        MatIconModule,
        MatTabsModule,
        MatInputModule,
        MatFormFieldModule,
        MatTooltipModule,
        MatDialogModule,
        MatDatepickerModule,
        MatSelectModule,
        MatNativeDateModule,
        MatProgressSpinnerModule,
        MatSnackBarModule
    ]
})
export class MaterialSharedModule { }