
import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import * as auth from 'firebase/auth';
import { AngularFireAuth } from '@angular/fire/compat/auth';
import {
  AngularFirestore,
  AngularFirestoreDocument,
} from '@angular/fire/compat/firestore';
import { Router } from '@angular/router'

import { Observable, of } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { MatLegacySnackBar as MatSnackBar } from '@angular/material/legacy-snack-bar';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  userData: any
  user$: Observable<any>
  constructor(
    private afAuth: AngularFireAuth,
    private afs: AngularFirestore,
    private router: Router,
    private http: HttpClient,
    private _snackBar: MatSnackBar,
  ) {
    this.user$ = this.afAuth.authState.pipe(
      switchMap(user => {
        // Logged in
        if (user) {
          localStorage.setItem('userEmail', user.email)
          user.getIdToken(true).then(idToken => {
            localStorage.setItem('idToken', idToken)
              setTimeout(() => {
                this.router.navigate(['/home'])
              }, 50);
          });
          return this.afs.doc<any>(`users/${user.uid}`).valueChanges();
        } else {
          // Logged out
          return of(null);
        }
      })
    )
  }


  async googleSignin() {
    const provider = new auth.GoogleAuthProvider();
    const credential = await this.afAuth.signInWithPopup(provider);
    localStorage.setItem('user', credential.user.displayName)
    localStorage.setItem('userEmail', credential.user.email)
    this.setUserId(credential.user.email)
    credential.user?.getIdToken(true).then(idToken => {
      localStorage.setItem('idToken', idToken)
      this.setUserId(credential.user.email)
      this.validate().subscribe((res: any) => {
        if (res.success == true) {

          setTimeout(() => {
            this.router.navigate(['/home'])
          }, 50);
        }
        else {
          this.openFailureSnackBar('Authentication Failed', 'Close')
        }
      }, (error: any) => {
        this.openFailureSnackBar('Authentication Failed', 'Close')
      })
    });
  }

  async emaiAndPasswordSignIn(email: string, password: string) {
    const credential = await this.afAuth.signInWithEmailAndPassword(email, password)
    localStorage.setItem('user', credential.user.displayName)
    localStorage.setItem('userEmail', credential.user.email)

    credential.user?.getIdToken().then(idToken => {
      setTimeout(() => { this.setUserId(credential.user.email) }, 10)
      localStorage.setItem('idToken', idToken)
      this.validate().subscribe((res: any) => {
        if (res.success == true) {
          setTimeout(() => {
            this.router.navigate(['/home'])
          }, 50);
        }
        else {
          this.openFailureSnackBar(res.message, 'Close')
        }
      }, (error: any) => {
        this.openFailureSnackBar("504 error", 'Close')
      })

    })
  }

  private updateUserData(user: any) {
    // Sets user data to firestore on login
    const userRef: AngularFirestoreDocument<any> = this.afs.doc(`users/${user.uid}`);

    const data = {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName,
      photoURL: user.photoURL
    }
    return userRef.set(data, { merge: true })
  }

  async signOut() {
    await this.afAuth.signOut();
    if (localStorage.getItem('idToken')) {
      localStorage.removeItem('idToken')
    }
    this.router.navigate(['/login']);
  }

  validate() {
    return this.http.get(`${environment.auth_apiUrl}validate`)
  }

  setUserId(email) {
    this.searchUser(email).subscribe((res: any) => {
      localStorage.setItem("userId", res.data[0].user_id)
    })
  }

  searchUser(email) {
    return this.http.get(`${environment.classroomShimUrl}user/search/email?email=${email}`)
  }


  findEmailSetId() {
    this.afAuth.authState.subscribe(user => {
      // Logged in
      if (user) {
        localStorage.setItem('userEmail', user.email)
        setTimeout(() => { this.setUserId(user.email) }, 10)
        return true
      } else {
        // Logged out
        return of(null);
      }
    })
  }

  openFailureSnackBar(message: string, action: string) {
    this._snackBar.open(message, action, {
      duration: 100000,
      panelClass: ['red-snackbar'],
    });
  }

}
