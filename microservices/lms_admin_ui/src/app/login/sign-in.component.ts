import { Component, OnInit } from '@angular/core';
import { AuthService } from '../shared/service/auth.service';
import { MatIconRegistry } from "@angular/material/icon";
import { DomSanitizer } from "@angular/platform-browser";


@Component({
  selector: 'app-sign-in',
  templateUrl: './sign-in.component.html',
  styleUrls: ['./sign-in.component.scss']
})
export class SignInComponent implements OnInit {

  constructor(public authService: AuthService, private matIconRegistry: MatIconRegistry, private domSanitizer: DomSanitizer) {
    this.matIconRegistry.addSvgIcon(
      'google-icon',
      this.domSanitizer.bypassSecurityTrustResourceUrl('assets/img/Google.svg')
    );
    this.matIconRegistry.addSvgIcon(
      'google-text-icon',
      this.domSanitizer.bypassSecurityTrustResourceUrl('assets/img/google-text.svg')
    );
  }

  ngOnInit(): void {
  }

}
