import { Component, OnInit, ViewChild, Inject } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { LtiService } from '../service/lti.service';
import { MatLegacyDialog as MatDialog, MAT_LEGACY_DIALOG_DATA as MAT_DIALOG_DATA, MatLegacyDialogRef as MatDialogRef } from '@angular/material/legacy-dialog'
import { ContentSelectorComponent } from '../content-selector/content-selector.component';
import { HomeService } from 'src/app/home/service/home.service';
interface LooseObject {
  [key: string]: any
}
@Component({
  selector: 'app-create-assignment',
  templateUrl: './create-assignment.component.html',
  styleUrls: ['./create-assignment.component.scss']
})
export class CreateAssignmentComponent {
  ltiAssignmentForm: FormGroup;
  toolsList = []
  showProgressSpinner: boolean = false
  selectedTool: any
  constructor(
    public dialogRef: MatDialogRef<CreateAssignmentComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData: any,
    public dialog: MatDialog,
    private fb: FormBuilder, private homeService: HomeService, private ltiService: LtiService) { }

  ngOnInit() {
    this.getAllTools()
    if (this.dialogData.mode == "Create") {
      this.ltiAssignmentForm = this.fb.group({
        "tool_id": [null, Validators.required],
        "lti_assignment_title": [null, Validators.required],
        "lti_content_item_id": [null],
        "start_date": [null],
        "end_date": [null],
        "due_date": [null],
        "max_points": [null]
      });
    } else {
      this.ltiAssignmentForm = this.fb.group({
        "tool_id": [this.dialogData.extra_data.assignment.tool_id, Validators.required],
        "lti_assignment_title": [this.dialogData.extra_data.assignment.lti_assignment_title, Validators.required],
        "lti_content_item_id": [this.dialogData.extra_data.assignment.lti_content_item_id],
        "start_date": [this.dialogData.extra_data.assignment.start_date],
        "end_date": [this.dialogData.extra_data.assignment.end_date],
        "due_date": [this.dialogData.extra_data.assignment.due_date],
        "max_points": [this.dialogData.extra_data.assignment.max_points]
      });
    }
  }

  onDropdownChange() {
    console.log(this.ltiAssignmentForm.value)

  }

  processFormInputs(values) {
    // convert redirect uris from str to list and make data ready to send to API
    const arr = values.redirect_uris.split(";")
    const redirect_uris = arr.map(element => {
      return element.trim();
    });
    const finalValues = { ...values, "redirect_uris": redirect_uris }
    return finalValues
  }

  onSubmit(ltiAssignmentForm) {
    this.showProgressSpinner = true
    console.log(ltiAssignmentForm.value)
    const data = ltiAssignmentForm.value
    let context_type = this.dialogData.page
    console.log(data)
    console.log("Extra dataaaaa", this.dialogData.extra_data)
    if (this.dialogData.mode == "Create") {
      this.homeService.postLtiAssignments({ ...data, context_type: context_type, context_id: this.dialogData.extra_data.contextId }).subscribe(response => {
        console.log("response", response)
        this.showProgressSpinner = false
        this.dialogRef.close({ data: 'success' })
      })
    } else {
      console.log("this.dialogData.extra_data", this.dialogData.extra_data)
      this.homeService.updateLtiAssignments(this.dialogData.extra_data.assignment.id, data).subscribe(response => {
        console.log("response", response)
        this.showProgressSpinner = false
        this.dialogRef.close({ data: 'success' })
      })
    }
  }

  fetchData(id) {
    const data = this.ltiService.getToolData(id).subscribe((response: any) => {
      return response.data
    })
  }

  openContentSelector(ltiAssignmentForm) {
    console.log(ltiAssignmentForm.value)
    let ltiModalData: LooseObject = {}
    ltiModalData['mode'] = 'Open'
    ltiModalData['init_data'] = ''
    ltiModalData['extra_data'] = {
      contextId: this.dialogData.extra_data.courseTemplateId,
      contextType: "course_template",
      toolId: ltiAssignmentForm.value.tool_id,
      userId: "vcmt4ZemmyFm59rDzl1U"
    }

    const dialogRef = this.dialog.open(ContentSelectorComponent, {
      width: '80vw',
      maxWidth: '750px',
      maxHeight: "90vh",
      data: ltiModalData
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result.data.status == "success") {
        this.ltiAssignmentForm.get("lti_content_item_id").setValue(result.data.response[0].lti_content_item_id)
      }
      console.log("result", result)
    });
  }

  getAllTools() {
    this.ltiService.getToolsList().subscribe((res: any) => {
      this.toolsList = res.data
    })
  }

  onNoClick(): void {
    this.dialogRef.close({ data: 'closed' });
  }

}