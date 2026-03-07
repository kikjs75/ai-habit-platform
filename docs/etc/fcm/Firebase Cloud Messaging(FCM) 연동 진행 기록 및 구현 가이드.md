# Firebase Cloud Messaging(FCM) 연동 진행 기록 및 구현 가이드

## 목적

NestJS 서버에서 FCM HTTP v1 API를 사용해 푸시 알림을 전송하기 위한 준비 절차를 정리한다.

전체 목표 흐름은 다음과 같다.

```
Android 앱
→ Firebase SDK
→ registration token 발급
→ NestJS 서버 저장
→ Google 서비스 계정으로 access token 발급
→ FCM HTTP v1 API 호출
→ Push Notification 전송
```

---

## 진행 상태

- [x] 1) Firebase 프로젝트 생성
- [x] 2) Android 앱 또는 Web 앱 등록
- [x] 3) 클라이언트 앱에 Firebase SDK 붙이기
- [x] 4) 앱 실행해서 registration token 출력 확인
- [x] 5) Google Cloud 쪽에서 서비스 계정 준비
- [x] 6) Firebase Cloud Messaging API 활성화 확인
- [ ] 7) NestJS .env 설정
- [ ] 8) 서버에서 FCM HTTP v1 또는 Admin SDK 로 전송 테스트
- [ ] 9) 실패 시 에러 코드와 invalid token 처리 로직 추가

---

## 1) Firebase 프로젝트 생성

Firebase Console에서 새 프로젝트를 생성했다.

- 예시 프로젝트 ID: `ai-habit-platform-dev`

이 프로젝트는 내부적으로 Google Cloud 프로젝트와 연결된다.
즉 이후 설정 중 다음 항목은 Google Cloud Console에서 진행하게 된다.

- IAM
- 서비스 계정
- API 활성화
- OAuth 인증

---

## 2) Android 앱 또는 Web 앱 등록

FCM은 클라이언트 앱이 먼저 등록되어야 registration token을 발급받을 수 있다.
초기 포트폴리오 구현에서는 Android 앱 등록이 가장 단순하다.

### Android를 선택한 이유

iPhone 사용자여도 Android 앱으로 먼저 테스트하는 것이 유리하다.

| 플랫폼 | 조건 |
|--------|------|
| iOS | APNs 설정이 추가로 필요함 |
| Web | HTTPS + Service Worker 조건이 있음 |
| Android | Firebase 기반 테스트가 가장 단순함 |

즉, 포트폴리오 초기 단계에서는 다음 구조가 가장 현실적이다.

```
Firebase 프로젝트
→ Android 앱 등록
→ Android Emulator 또는 Android 폰
→ registration token 발급
→ 서버에서 push 전송 테스트
```

---

## 3) 클라이언트 앱에 Firebase SDK 붙이기

Android 앱에 Firebase SDK를 추가해 FCM 기능을 연결했다.

### 핵심 개념

여기서 말하는 Firebase SDK는 Android Studio 프로젝트에 넣는 공식 라이브러리를 의미한다.

- `google-services.json`
- `firebase-messaging` 의존성
- `FirebaseMessaging.getInstance().token`

### Android Studio 관련 정리

Android 앱 기준으로 FCM token을 얻으려면 보통 Android Studio 환경이 필요하다.
단, 물리 안드로이드 폰이 반드시 필요한 것은 아니다.

**가능한 실행 환경:**
- 실제 Android 폰
- Android Emulator
- Web 앱

**포트폴리오 기준 추천:**

```
Android Studio
→ Android Emulator (Google Play image)
→ Firebase SDK
→ FCM token 발급
```

---

## 4) 앱 실행해서 registration token 출력 확인

앱 실행 후 Firebase SDK를 통해 registration token을 발급받고 로그에서 확인했다.

### 핵심 개념

registration token은 서버가 만드는 것이 아니라 클라이언트 앱이 발급받는 값이다.

**흐름:**
```
Android App
→ Firebase SDK
→ registration token 생성
→ 서버에 전달
```

### 의미

이 token은 서버가 푸시를 보낼 때 대상 기기를 식별하는 값이다.
즉 서버는 이후 이 token을 이용해 FCM HTTP v1 API에 요청을 보내게 된다.

---

## 5) Google Cloud 쪽에서 서비스 계정 준비

NestJS 서버가 FCM HTTP v1 API를 호출하려면 Google 서비스 계정이 필요하다.

### 주의할 점

Google Cloud Console의 서비스 계정 목록에 자동 생성된 계정이 있을 수 있다.

- 예: `firebase-adminsdk-xxxxx@ai-habit-platform-dev.iam.gserviceaccount.com`
- 이 계정은 보통 Firebase 내부 동작용이다. (설명: `Firebase Admin SDK Service Agent`)

> 이 자동 생성 계정은 직접 사용하는 것보다 서버 전송용 서비스 계정을 **별도로 만드는 것이 권장**된다.

### 권장 방식

새 서비스 계정을 생성한다.

- 서비스 계정 이름: `fcm-sender`
- 설명: `Service account for sending FCM messages`
- 예상 이메일: `fcm-sender@ai-habit-platform-dev.iam.gserviceaccount.com`

### 이후 해야 하는 작업

서비스 계정 생성 후 JSON 키를 발급받는다.

```
Keys → Add Key → Create new key → JSON
```

다운로드된 JSON 파일이 NestJS 인증에 사용된다.

---

## 6) Firebase Cloud Messaging API 활성화 확인

FCM HTTP v1 API를 사용하려면 Firebase Cloud Messaging API가 활성화되어 있어야 한다.

### 확인 결과

Google Cloud Console에서 다음과 같이 확인했다.

- 버튼이 **관리**로 표시됨
- 초록 체크와 함께 **API 사용 설정됨** 표시

즉 현재 상태:

```
Firebase Cloud Messaging API → 활성화 완료
```

---

## 7) NestJS .env 설정

이제 NestJS 서버가 서비스 계정 정보를 읽을 수 있도록 환경 변수를 설정해야 한다.

### 목적

NestJS 서버가 다음을 수행할 수 있게 한다.

```
서비스 계정 정보 읽기
→ OAuth 2.0 access token 발급
→ FCM HTTP v1 API 호출
```

### 권장 방식: JSON 키 파일 경로 사용

가장 단순하고 안전한 방식은 서비스 계정 JSON 파일 경로를 `.env`에 넣는 것이다.

**`.env`**
```env
PORT=3000
FCM_PROJECT_ID=ai-habit-platform-dev
GOOGLE_APPLICATION_CREDENTIALS=./secrets/fcm-sender.json
```

| 변수 | 의미 |
|------|------|
| `FCM_PROJECT_ID` | Firebase 프로젝트 ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | 서비스 계정 JSON 파일 경로 |

### 권장 디렉토리 구조

```
project-root/
  src/
  secrets/
    fcm-sender.json
  .env
  .env.example
  package.json
```

### `.env.example`

실제 비밀값 대신 예시만 적은 파일도 같이 둔다.

```env
PORT=3000
FCM_PROJECT_ID=your_firebase_project_id
GOOGLE_APPLICATION_CREDENTIALS=./secrets/your-service-account.json
```

### `.gitignore`

서비스 계정 JSON과 `.env`는 Git에 올리면 안 된다.

```
.env
secrets/*.json
```

### NestJS 설정

`@nestjs/config`를 사용한다.

**설치**
```bash
npm install @nestjs/config
```

**`app.module.ts`**
```typescript
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
  ],
})
export class AppModule {}
```

**환경 변수 읽기 예시**
```typescript
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class FcmService {
  constructor(private readonly configService: ConfigService) {}

  getProjectId(): string {
    return this.configService.get<string>('FCM_PROJECT_ID', '');
  }

  getCredentialsPath(): string {
    return this.configService.get<string>('GOOGLE_APPLICATION_CREDENTIALS', '');
  }
}
```

### 주의 사항

**1. 프로젝트 이름과 프로젝트 ID를 혼동하지 말 것**

| 항목 | 예시 |
|------|------|
| 프로젝트 이름 | `AI Habit Platform Dev` |
| 프로젝트 ID | `ai-habit-platform-dev` |

> `.env`에는 반드시 **프로젝트 ID**를 넣어야 한다.

**2. 컨테이너 환경이면 경로 기준이 달라질 수 있음**

devcontainer / Docker 환경이라면 JSON 파일이 컨테이너 내부에서도 실제로 존재해야 한다.

```bash
ls -l ./secrets
cat ./secrets/fcm-sender.json
```

---

## 8) 서버에서 FCM HTTP v1 또는 Admin SDK 로 전송 테스트

다음 단계는 실제 전송 테스트다.

### 권장 방식

포트폴리오 설명 관점에서는 **FCM HTTP v1 API 직접 호출 방식**이 좋다.

- HTTP 구조가 명확함
- OAuth 인증 흐름을 설명하기 쉬움
- 서버 동작 원리를 문서화하기 좋음

### 전체 흐름

```
service account JSON
→ OAuth 2.0 access token 발급
→ Authorization: Bearer <token>
→ POST https://fcm.googleapis.com/v1/projects/{projectId}/messages:send
```

### 전송 시 필요한 값

- `FCM_PROJECT_ID`
- 서비스 계정 JSON
- registration token
- title / body

### 향후 구현 항목

- [ ] access token 발급 로직
- [ ] HTTP v1 payload 생성
- [ ] NestJS 서비스 메서드 작성
- [ ] 테스트용 API 엔드포인트 작성

---

## 9) 실패 시 에러 코드와 invalid token 처리 로직 추가

실제 구현에서는 성공 케이스만이 아니라 실패 케이스도 같이 처리해야 한다.

### 처리해야 할 대표 항목

- 잘못된 registration token
- 만료된 token
- 비활성 기기 token
- 인증 실패
- 권한 오류
- payload 형식 오류

### 구현 권장 사항

**1. FCM 응답 전체 로깅**

| 항목 | 내용 |
|------|------|
| 요청 대상 token | 전송 대상 기기 식별자 |
| 응답 status | HTTP 상태 코드 |
| 응답 body | FCM 응답 내용 |
| 에러 코드 | FCM 에러 타입 |
| timestamp | 요청 시각 |

**2. invalid token 정리 정책**

특정 에러가 발생하면 해당 token을 DB에서 비활성화하거나 삭제 대상으로 마킹한다.

```sql
device_tokens
  - id
  - user_id
  - token
  - platform
  - is_active
  - last_error_code
  - updated_at
```

**3. 재시도 여부 분리**

| 유형 | 처리 방식 |
|------|-----------|
| 영구 실패 | token 제거 대상 |
| 일시 실패 | 재시도 가능 |

---

## 현재까지의 결론

### 완료된 항목

- [x] Firebase 프로젝트 생성 완료
- [x] Android 앱 등록 완료
- [x] Firebase SDK 연동 완료
- [x] registration token 확인 완료
- [x] 서비스 계정 준비 완료
- [x] Firebase Cloud Messaging API 활성화 완료

### 지금 바로 해야 할 항목

**1. NestJS `.env` 설정**

```env
PORT=3000
FCM_PROJECT_ID=ai-habit-platform-dev
GOOGLE_APPLICATION_CREDENTIALS=./secrets/fcm-sender.json
```

**2. `.env.example` 생성**

```env
PORT=3000
FCM_PROJECT_ID=your_firebase_project_id
GOOGLE_APPLICATION_CREDENTIALS=./secrets/your-service-account.json
```

**3. `.gitignore` 확인**

```
.env
secrets/*.json
```

**4. ConfigModule 적용**

```typescript
ConfigModule.forRoot({ isGlobal: true })
```