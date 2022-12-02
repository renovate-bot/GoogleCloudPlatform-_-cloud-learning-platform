import { CreateCourseTemplateModalComponent } from './create-course-template-modal/create-course-template-modal.component';
import { Component, OnInit } from '@angular/core';
import { MatDialog, MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog'
import { CreateCohortModalComponent } from './create-cohort-modal/create-cohort-modal.component';
import { HomeService } from './service/home.service';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})
export class HomeComponent implements OnInit {
  searchText: string = '';
  cohortList: any[]
  courseTemplateList: any[]
  courseTemplateLoader: boolean = true
  cohortLoader: boolean = true
  constructor(public dialog: MatDialog, public _HomeService: HomeService) { }

  ngOnInit(): void {
    this.getCohortList()
    this.getCourseTemplateList()
  }
  getCourseTemplateList() {
    this.courseTemplateLoader = true
    this._HomeService.getCourseTemplateList().subscribe((res: any) => {
      if (res.success == true) {
        this.courseTemplateList = res.course_template_list
        this.courseTemplateLoader = false
      }
    })
  }
  getCohortList() {
    this.cohortLoader = true
    this._HomeService.getCohortList().subscribe((res: any) => {
      if (res.success == true) {
        this.cohortList = res.cohort_list
        this.cohortLoader = false
      }
    })
  }


  openDialog(): void {
    const dialogRef = this.dialog.open(CreateCohortModalComponent, {
      width: '500px',
      data: this.courseTemplateList
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result.data == 'success') {
        this.getCohortList()
      }
    });
  }

  openCourseTemplateDialog(): void {
    const dialogRef = this.dialog.open(CreateCourseTemplateModalComponent, {
      width: '500px'
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log(result)
      if (result.data == 'success') {
        this.getCourseTemplateList()
      }
    });
  }


}