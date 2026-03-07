# 4. Firebase Cloud Messaging 준비 절차

---

## 4.1 Firebase Project 생성

1. [Firebase Console](https://console.firebase.google.com)에 로그인합니다.
2. 새 프로젝트를 생성합니다.
3. 프로젝트 이름 예시: `ai-habit-platform-dev`

> Firebase Cloud Messaging은 Firebase 프로젝트 안에서 사용됩니다. 공식 문서는 Firebase 프로젝트를 만든 뒤, 클라이언트 앱과 서버 환경을 각각 준비하도록 안내합니다.

---

## 4.2 앱 등록

FCM은 클라이언트 앱이 먼저 등록되어야 토큰을 발급받을 수 있습니다.

**가능한 플랫폼**

- Android
- iOS
- Web

포트폴리오 초기 단계에서는 가장 간단하게 다음 중 하나를 선택하면 됩니다.

**추천**

- Android 앱 1개 등록
- 또는 Web 앱 1개 등록

> 클라이언트 앱은 FCM SDK를 통해 registration token을 발급받고, 서버는 그 토큰으로 메시지를 전송합니다.

---

## 4.3 서버 인증 방식 선택

FCM 서버 연동 방식은 보통 두 가지입니다.

### 옵션 A. Firebase Admin SDK 사용

**장점**

- 서버에서 구현이 단순함
- 인증 처리가 비교적 쉬움

### 옵션 B. FCM HTTP v1 API 사용

**장점**

- HTTP 기반으로 명확한 구조
- 포트폴리오에서 동작 원리 설명이 쉬움

> Firebase 공식 문서는 서버 측 구현에서 Admin SDK를 권장하며, HTTP v1 API를 사용할 경우 서비스 계정 기반 OAuth 2.0 access token으로 요청해야 한다고 설명합니다.

---

## 4.4 서비스 계정 준비

FCM HTTP v1 또는 Admin SDK 서버 전송을 위해 보통 서비스 계정을 사용합니다.

**필요 작업**

1. Firebase 프로젝트와 연결된 Google Cloud 프로젝트 확인
2. IAM / Service Accounts로 이동
3. 서비스 계정 생성
4. 필요한 권한 부여
5. JSON 키 발급 또는 Google Cloud 런타임 인증 사용

> FCM HTTP v1 API 공식 문서는 서비스 계정을 만들고, 해당 계정으로 OAuth 2.0 access token을 발급받아 `Authorization: Bearer <token>` 헤더로 요청하라고 안내합니다.

---

## 4.5 FCM API 활성화 확인

Firebase 공식 문서에는 FCM HTTP v1 API를 사용하려면 **Firebase Cloud Messaging API** 가 활성화되어 있어야 한다고 나옵니다.

프로젝트의 Cloud Messaging 설정과 Google Cloud API 활성화 상태를 함께 확인하는 것이 안전합니다.

---

## 4.6 테스트용 Registration Token 확보

푸시 전송을 확인하려면 실제 클라이언트 앱에서 **device registration token** 을 받아야 합니다.

**필수 흐름**

1. 앱에 Firebase SDK 추가
2. 앱 실행
3. FCM registration token 발급
4. 그 토큰을 서버 또는 테스트 DB에 저장
5. 서버에서 해당 토큰으로 push 발송

> Firebase는 오래되거나 비활성 토큰 관리를 따로 권장하며, 만료되거나 stale token은 정리해야 한다고 안내합니다.

---

## 4.7 애플리케이션에 저장할 환경 변수

NestJS에서 사용할 `.env` 예시:

```env
FCM_PROJECT_ID=your_firebase_project_id
FCM_CLIENT_EMAIL=your_service_account_email
FCM_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

파일 경로 기반으로 관리하고 싶다면:

```env
GOOGLE_APPLICATION_CREDENTIALS=/workspace/secrets/firebase-service-account.json
```

---

## 4.8 구현 전에 확인할 체크리스트

- [ ] Firebase 프로젝트 생성
- [ ] 앱 (Android / iOS / Web) 등록
- [ ] Firebase SDK 연동
- [ ] registration token 발급 확인
- [ ] 서비스 계정 생성
- [ ] FCM API 활성화 확인
- [ ] NestJS `.env` 등록
- [ ] 테스트용 토큰 저장

## 4.9 주요 정보
- 프로젝트 이름 : `ai-habit-platform-dev`
- 앱-Android 패키지 이름 : com.jscompany.aihabit
- 앱-닉네임 : aihabit
- google-services.json(Firebase Registration token 생성 위한 JSON) : google-services.json
- 앱-Registration token
```
2026-03-07 19:23:50.160  4869-4869  FCM                     com.jscompany.aihabit                D  Registration token: cRcW83AmTBKYwaRncGoWc1:APA91bG6KoY8xRnirdfRfyTrPFSETiju-86jt1nXaDj5M36m2bvNIDtVm1HaKdYIoxDdXaFAnp3Dcrddy9XqDuDDKTCO8P0EV8Jt12PxO6o_HdnBhgoThZ4
```
- 앱(서비스 계정 이름) : fcm-sender
- 앱-(서비스 계정 ID) : fcm-sender
- 앱-(서비스 계정 설명) : Service account for sending FCM messages
- 앱-(서비스 계정 역할) : Firebase Cloud Messaging API Admin
- 앱-(service-account.json | NestJS 서버에서 인증에 쓰는 핵심 키) : ai-habit-platform-dev-d022b23cbf17.json => fcm-sender.json