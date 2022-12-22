import { Component, OnInit } from '@angular/core';
import { MatLegacyDialog as MatDialog, MAT_LEGACY_DIALOG_DATA as MAT_DIALOG_DATA, MatLegacyDialogRef as MatDialogRef } from '@angular/material/legacy-dialog';
import { FormControl, UntypedFormGroup, UntypedFormBuilder, Validators, Form } from '@angular/forms';
import { MatLegacySnackBar as MatSnackBar } from '@angular/material/legacy-snack-bar';
import { HomeService } from '../service/home.service';

interface LooseObject {
  [key: string]: any
}
@Component({
  selector: 'app-create-course-template-modal',
  templateUrl: './create-course-template-modal.component.html',
  styleUrls: ['./create-course-template-modal.component.scss']
})
export class CreateCourseTemplateModalComponent implements OnInit {
  courseTemplateForm: UntypedFormGroup
  showProgressSpinner: boolean = false
  constructor(public dialogRef: MatDialogRef<CreateCourseTemplateModalComponent>, private fb: UntypedFormBuilder,
    private _snackBar: MatSnackBar, private _HomeService: HomeService) { }

  ngOnInit(): void {
    this.courseTemplateForm = this.fb.group({
      name: this.fb.control('', [Validators.required]),
      description: this.fb.control('', [Validators.required]),
      instructional_designer: this.fb.control('', [Validators.required]),
      admin: this.fb.control('', [Validators.required]),
    });

  }
  openSuccessSnackBar(message: string, action: string) {
    this._snackBar.open(message, action, {
      duration: 3000,
      panelClass: ['green-snackbar'],
    });
  }
  openFailureSnackBar(message: string, action: string) {
    this._snackBar.open(message, action, {
      duration: 3000,
      panelClass: ['red-snackbar'],
    });
  }
  onNoClick(): void {
    this.dialogRef.close({ data: 'close' });
  }

  createCourseTemplate() {
    this.showProgressSpinner = true
    this._HomeService.createCourseTemplate(this.courseTemplateForm.value).subscribe((res: any) => {
      if (res.success == true) {
        this.openSuccessSnackBar('Create course template', 'SUCCESS')
        this.dialogRef.close({ data: 'success' });
      }
      else {
        this.openFailureSnackBar('Create course template', 'FAILED')
      }
      this.showProgressSpinner = false
    }, (error: any) => {
      this.openFailureSnackBar('Create course template', 'FAILED')
      this.showProgressSpinner = false
    })

  }


}
